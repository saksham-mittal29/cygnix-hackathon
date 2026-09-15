"""
dht22_reader.py
---------------
Real-time USB Serial DHT22 reader and Open-Meteo weather client.
Reads live indoor room temperature & humidity from Arduino @ 115200 baud,
and fetches real-time outdoor temperature & humidity for Chennai, India.
"""

import glob
import json
import logging
import re
import threading
import time
from typing import Dict, Any, Optional, Tuple

import requests
import serial

logger = logging.getLogger("wisp.sensor")
DEFAULT_BAUD = 115200


class WeatherClient:
    """Fetches and caches live outdoor weather from Open-Meteo for any city or coordinates."""

    def __init__(self, lat: Optional[float] = None, lon: Optional[float] = None, cache_ttl_sec: float = 30.0):
        self.default_lat = lat
        self.default_lon = lon
        self.cache_ttl = cache_ttl_sec
        self._last_fetch_time: float = 0.0
        self._cached_key: str = ""
        self._cached_weather: Dict[str, Any] = {
            "outdoor_temp_f": 82.0,
            "outdoor_humidity": 65.0,
            "location": "Local Weather",
            "last_updated": "Cached",
        }
        self._lock = threading.Lock()
        self._detected_ip_loc: Optional[Tuple[float, float, str]] = None

    def detect_ip_location(self) -> Optional[Tuple[float, float, str]]:
        """Detect current approximate location from IP."""
        if self._detected_ip_loc:
            return self._detected_ip_loc
        try:
            resp = requests.get("http://ip-api.com/json", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    lat = float(data["lat"])
                    lon = float(data["lon"])
                    city = data.get("city", "")
                    country = data.get("country", "")
                    loc = f"{city}, {country}" if city and country else (city or country or "Local")
                    self._detected_ip_loc = (lat, lon, loc)
                    return self._detected_ip_loc
        except Exception as e:
            logger.debug(f"IP Geolocation failed: {e}")
        return None

    def geocode_city(self, city_name: str) -> Optional[Tuple[float, float, str]]:
        """Geocode city name to lat, lon, and full location name via Open-Meteo Geocoding API."""
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(city_name.strip())}&count=1"
            resp = requests.get(url, timeout=3.0)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    res = results[0]
                    lat = float(res.get("latitude"))
                    lon = float(res.get("longitude"))
                    name = res.get("name", city_name)
                    country = res.get("country", "")
                    admin = res.get("admin1", "")
                    parts = [p for p in [name, admin, country] if p]
                    full_name = ", ".join(parts[:2]) if len(parts) > 1 else name
                    return lat, lon, full_name
        except Exception as e:
            logger.debug(f"Geocoding failed for {city_name}: {e}")
        return None

    def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None, location_name: Optional[str] = None) -> Dict[str, Any]:
        target_lat = lat
        target_lon = lon
        loc_str = location_name

        # If user searched by city name
        if location_name and (lat is None or lon is None):
            geo = self.geocode_city(location_name)
            if geo:
                target_lat, target_lon, loc_str = geo
            else:
                loc_str = location_name

        # If neither lat/lon nor city is given, attempt auto-detect via IP
        if target_lat is None or target_lon is None:
            ip_loc = self.detect_ip_location()
            if ip_loc:
                target_lat, target_lon, loc_str = ip_loc
            elif self.default_lat is not None and self.default_lon is not None:
                target_lat = self.default_lat
                target_lon = self.default_lon
            else:
                target_lat = 28.6139
                target_lon = 77.2090
                if not loc_str:
                    loc_str = "Local Weather"

        if not loc_str:
            loc_str = f"GPS ({target_lat:.2f}°, {target_lon:.2f}°)"

        cache_key = f"{target_lat:.4f},{target_lon:.4f}"

        now = time.time()
        with self._lock:
            if self._cached_key == cache_key and (now - self._last_fetch_time < self.cache_ttl):
                return dict(self._cached_weather)

        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={target_lat}&longitude={target_lon}"
                f"&current=temperature_2m,relative_humidity_2m"
                f"&temperature_unit=fahrenheit"
            )
            resp = requests.get(url, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                temp_f = float(current.get("temperature_2m", 82.0))
                hum = float(current.get("relative_humidity_2m", 65.0))
                if not loc_str:
                    loc_str = f"GPS ({target_lat:.2f}°, {target_lon:.2f}°)"
                with self._lock:
                    self._cached_key = cache_key
                    self._cached_weather = {
                        "outdoor_temp_f": round(temp_f, 1),
                        "outdoor_humidity": round(hum, 1),
                        "latitude": target_lat,
                        "longitude": target_lon,
                        "location": loc_str,
                        "last_updated": current.get("time", "Now"),
                    }
                    self._last_fetch_time = now
        except Exception as e:
            logger.warning(f"Failed to fetch Open-Meteo weather: {e}")

        with self._lock:
            return dict(self._cached_weather)


class DHT22SerialReader:
    """Thread-safe USB Serial reader for DHT22 sensor @ 115200 baud."""

    def __init__(self, baudrate: int = DEFAULT_BAUD):
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.active_port: Optional[str] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Telemetry state
        self.indoor_temp_f: float = 75.2
        self.indoor_humidity: float = 55.0
        self.is_connected: bool = False
        self.last_read_time: float = 0.0
        self.is_monitoring_active: bool = False
        self.weather_client = WeatherClient()

    def set_monitoring(self, active: bool):
        """Enable or disable active USB serial reading."""
        self.is_monitoring_active = active
        if not active:
            with self._lock:
                self.is_connected = False
                self.active_port = None
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass

    def find_serial_ports(self) -> list:
        """Scan macOS / Linux USB serial ports."""
        patterns = [
            "/dev/cu.usbmodem*",
            "/dev/cu.usbserial*",
            "/dev/tty.usbmodem*",
            "/dev/tty.usbserial*",
            "/dev/ttyUSB*",
            "/dev/ttyACM*",
        ]
        ports = []
        for pattern in patterns:
            ports.extend(glob.glob(pattern))
        return sorted(list(set(ports)))

    def start(self):
        """Start background polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"DHT22SerialReader started background thread @ {self.baudrate} baud.")

    def stop(self):
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass

    def _process_line(self, line: str) -> bool:
        """Process incoming serial line (supporting single or combined temp/humidity lines)."""
        line = line.strip()
        if not line:
            return False

        updated = False
        # 1. Check for JSON format
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                t = float(data.get("temp", data.get("temperature", 0)))
                h = float(data.get("hum", data.get("humidity", 0)))
                if t > 0:
                    if t < 45.0: t = (t * 9.0 / 5.0) + 32.0
                    self.indoor_temp_f = round(t, 1)
                    updated = True
                if h > 0:
                    self.indoor_humidity = round(h, 1)
                    updated = True
            except Exception:
                pass

        # 2. Check for combined or single regex patterns
        mt = re.search(r"(?:temp|temperature|tmpeaue|tmperaur|tmperatr|tmp)[:=\s]*([0-9.]+)", line, re.IGNORECASE)
        if not mt and "c" in line.lower() and re.search(r"([0-9.]+)\s*c", line, re.IGNORECASE):
            mt = re.search(r"([0-9.]+)\s*c", line, re.IGNORECASE)

        if mt:
            try:
                t = float(mt.group(1))
                if t < 45.0:
                    t = (t * 9.0 / 5.0) + 32.0
                if 40.0 <= t <= 130.0:
                    self.indoor_temp_f = round(t, 1)
                    updated = True
            except Exception:
                pass

        mh = re.search(r"(?:hum|humidity|iiy|dt)[:=\s]*([0-9.]+)", line, re.IGNORECASE)
        if not mh and "%" in line and re.search(r"([0-9.]+)\s*%", line):
            mh = re.search(r"([0-9.]+)\s*%", line)

        if mh:
            try:
                h = float(mh.group(1))
                if 0.0 <= h <= 100.0:
                    self.indoor_humidity = round(h, 1)
                    updated = True
            except Exception:
                pass

        # 3. Comma-separated floats: "75.2, 55.0"
        if not updated and "," in line:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                try:
                    t = float(parts[0])
                    h = float(parts[1])
                    if t < 45.0: t = (t * 9.0 / 5.0) + 32.0
                    self.indoor_temp_f = round(t, 1)
                    self.indoor_humidity = round(h, 1)
                    updated = True
                except Exception:
                    pass

        if updated:
            self.last_read_time = time.time()
            self.is_connected = True
        return updated

    def _poll_loop(self):
        """Background serial reader that connects and streams live ESP32 lines."""
        while self._running:
            if not self.is_monitoring_active:
                time.sleep(1.0)
                continue

            ports = self.find_serial_ports()
            if not ports:
                with self._lock:
                    self.is_connected = False
                    self.active_port = None
                time.sleep(2.0)
                continue

            for port in ports:
                if not self._running or not self.is_monitoring_active:
                    break
                conn = None
                try:
                    conn = serial.Serial(port, self.baudrate, timeout=1.0)
                    with self._lock:
                        self.active_port = port

                    while self._running and self.is_monitoring_active and conn.is_open:
                        try:
                            raw = conn.readline().decode("utf-8", errors="ignore").strip()
                            if raw:
                                with self._lock:
                                    self._process_line(raw)
                        except (serial.SerialException, OSError):
                            break
                except Exception as e:
                    logger.debug(f"Serial port {port} unavailable: {e}")
                finally:
                    if conn and conn.is_open:
                        try:
                            conn.close()
                        except Exception:
                            pass

            with self._lock:
                if time.time() - self.last_read_time > 6.0:
                    self.is_connected = False
                    self.active_port = None
            time.sleep(1.5)

    def get_live_readings(self, lat: Optional[float] = None, lon: Optional[float] = None, location_name: Optional[str] = None) -> Dict[str, Any]:
        """Return composite live room and dynamic outdoor weather."""
        self.is_monitoring_active = True
        weather = self.weather_client.get_weather(lat=lat, lon=lon, location_name=location_name)
        now = time.time()
        with self._lock:
            indoor_t = self.indoor_temp_f
            indoor_h = self.indoor_humidity
            last_ts = self.last_read_time
            # Truly connected ONLY if valid data arrived in last 6 seconds
            conn = (last_ts > 0) and ((now - last_ts) < 6.0)
            self.is_connected = conn
            port_name = self.active_port if conn else None

        return {
            "connected": conn,
            "port": port_name,
            "baudrate": self.baudrate,
            "indoor_temp_f": indoor_t,
            "indoor_humidity": indoor_h,
            "outdoor_temp_f": weather.get("outdoor_temp_f", 82.0),
            "outdoor_humidity": weather.get("outdoor_humidity", 65.0),
            "location": weather.get("location", "Local Weather"),
            "source": f"USB Serial ({port_name})" if conn else "ESP32 (Close Arduino Serial Monitor to connect)",
            "last_read_seconds_ago": round(now - last_ts, 1) if last_ts > 0 else None,
        }


# Global Singleton Instance
dht22_sensor = DHT22SerialReader(baudrate=115200)
