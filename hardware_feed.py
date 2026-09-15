import serial
import time
import requests
import json

# ==========================================
# CONFIGURATION
# ==========================================
# Change this to your Arduino's serial port (e.g., 'COM3' on Windows, '/dev/cu.usbmodem...' on Mac)
ARDUINO_PORT = '/dev/cu.usbmodem14101' 
BAUD_RATE = 9600

# VIT Chennai Coordinates
LATITUDE = 12.8406
LONGITUDE = 80.1534

# Open-Meteo API URL (Current Weather in Fahrenheit for consistency with your model)
WEATHER_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=temperature_2m,relative_humidity_2m&temperature_unit=fahrenheit"

def get_outdoor_weather():
    try:
        response = requests.get(WEATHER_API_URL)
        if response.status_code == 200:
            data = response.json()
            temp = data['current']['temperature_2m']
            hum = data['current']['relative_humidity_2m']
            return temp, hum
        else:
            print("Failed to fetch weather from Open-Meteo")
            return None, None
    except Exception as e:
        print(f"Error connecting to Open-Meteo: {e}")
        return None, None

def main():
    print("=============================================")
    print("Cygnix Hardware Feed: DHT22 + Open-Meteo API")
    print("=============================================")
    print(f"Location: VIT Chennai ({LATITUDE}, {LONGITUDE})")
    
    # Connect to Arduino
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for serial connection to initialize
        print(f"Successfully connected to Arduino on {ARDUINO_PORT}")
    except Exception as e:
        print(f"\n[!] WARNING: Could not connect to Arduino on {ARDUINO_PORT}.")
        print("[!] Please check your port in the script.")
        print("[!] Running in API-only mode for outdoor weather...\n")
        ser = None

    print("Fetching initial outdoor weather...")
    out_temp, out_hum = get_outdoor_weather()
    last_weather_fetch = time.time()

    print("\n--- LIVE TELEMETRY FEED ---")
    print("Use these values to punch into the Cygnix Dashboard 'Live Sensor' mode:\n")

    while True:
        try:
            # Refresh weather every 5 minutes (300 seconds) to avoid API limits
            if time.time() - last_weather_fetch > 300:
                out_temp, out_hum = get_outdoor_weather()
                last_weather_fetch = time.time()

            indoor_temp_f = None
            indoor_hum = None

            # Read from Arduino
            if ser and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                # Assuming Arduino prints in format: "Temp: 24.5C Hum: 55%"
                # Adjust parsing based on your exact Arduino code output!
                if "Temp" in line or "," in line:
                    try:
                        # Example expected string: "75.2,55.0" (TempF, Humidity)
                        # Update this parsing logic to match your Arduino's exact Serial.println()
                        parts = line.split(',')
                        if len(parts) >= 2:
                            indoor_temp_f = float(parts[0])
                            indoor_hum = float(parts[1])
                    except ValueError:
                        pass # Ignore malformed serial lines
            
            # If we don't have Arduino plugged in right now, just mock the indoor temp for testing the script
            if not ser:
                indoor_temp_f = 78.5
                indoor_hum = 60.0

            if indoor_temp_f is not None and out_temp is not None:
                print(f"OUTDOOR (VIT Chennai): {out_temp}°F | INDOOR (DHT22): {indoor_temp_f}°F, {indoor_hum}% Hum")
            
            time.sleep(2)

        except KeyboardInterrupt:
            print("\nExiting...")
            if ser:
                ser.close()
            break

if __name__ == "__main__":
    main()
