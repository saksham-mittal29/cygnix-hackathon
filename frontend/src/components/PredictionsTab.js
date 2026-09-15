export function renderPredictionsTab(state) {
  const container = document.createElement("div");
  container.className = "tab-content predictions-tab";

  // Animation State
  let isSimulating = false;
  let simInterval = null;
  let simStepCount = 0;
  const MAX_SIM_STEPS = 13;

  // Chart Data State
  let chartInstance = null;
  let chartLabels = [];
  let actualTempData = [];
  let upperBoundData = [];
  let lowerBoundData = [];

  // Cost Data State
  let cumulativeNeuralCost = 0.0;
  let cumulativeLegacyCost = 0.0;
  let batteryStorage = 0.0;

  const initialTemp = 76.5;
  const initialPrefLow = 70.0;
  const initialPrefHigh = 74.0;
  const initialOutdoor = 82.0;
  const initialSolar = 2.5;

  const initialSource = state.predictionSource || "simulation";

  container.innerHTML = `
    <div class="page-header" style="margin-bottom: 20px;">
      <h1 class="page-title" style="font-size: 24px; font-weight: 700; color: #0f172a; margin: 0 0 4px 0;">Live Thermostat Simulation</h1>
      <div class="page-subtitle" style="font-size: 13px; color: #64748b;">Real-time AI Control Policy Dispatch & Trajectory</div>
    </div>
    
    <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 30px;">
      
      <!-- Left Controls Panel -->
      <div style="flex: 1; min-width: 320px; background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <div style="display: flex; gap: 16px; margin-bottom: 18px;">
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;">
            <input type="radio" name="pred-source" value="simulation" ${initialSource === 'simulation' ? 'checked' : ''} style="accent-color: #2563eb; width: 16px; height: 16px;">
            Interactive Demo Mode
          </label>
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;">
            <input type="radio" name="pred-source" value="live" ${initialSource === 'live' ? 'checked' : ''} style="accent-color: #2563eb; width: 16px; height: 16px;">
            Live Sensor (DHT22)
          </label>
        </div>

        <!-- Simulation Inputs -->
        <div id="sim-inputs" style="display: ${initialSource === 'simulation' ? 'block' : 'none'};">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Initial Temp (°F)</label>
              <input type="number" id="sim-curr-temp" value="${initialTemp}" step="0.5" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Outdoor Temp (°F)</label>
              <input type="number" id="sim-outdoor-temp" value="${initialOutdoor}" step="1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
          </div>

          <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 14px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px;">Comfort Target Band</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
              <div>
                <label style="display: block; font-size: 11px; color: #475569; margin-bottom: 4px;">Low Bound (°F)</label>
                <input type="number" id="pref-temp-low" value="${initialPrefLow}" step="0.5" style="width: 100%; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; box-sizing: border-box;">
              </div>
              <div>
                <label style="display: block; font-size: 11px; color: #475569; margin-bottom: 4px;">High Bound (°F)</label>
                <input type="number" id="pref-temp-high" value="${initialPrefHigh}" step="0.5" style="width: 100%; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; box-sizing: border-box;">
              </div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Solar Gen (kW)</label>
              <input type="number" id="sim-solar-kw" value="${initialSolar}" step="0.5" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Time of Day</label>
              <select id="sim-tod" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box;">
                <option value="Morning">Morning (Mid-Peak)</option>
                <option value="Afternoon" selected>Afternoon (Super Peak)</option>
                <option value="Night">Night (Mid-Peak)</option>
                <option value="Midnight">Midnight (Off-Peak)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Live Inputs -->
        <div id="live-inputs" style="display: ${initialSource === 'live' ? 'block' : 'none'};">
          <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 11px; font-weight: 700; color: #334155;">ESP32 DHT22 Telemetry</span>
              <span id="live-sensor-badge" style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: #fee2e2; color: #b91c1c;">OFFLINE</span>
            </div>
            <div id="live-sensor-port" style="font-size: 10px; color: #64748b; margin-top: 3px; font-family: monospace;">No active ESP32 data on USB (115200 baud)</div>
          </div>
          <div style="margin-bottom: 10px;">
            <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Live Room Temp (°F)</label>
            <input type="number" id="live-curr-temp" value="75.2" step="0.1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box; font-weight: 600; color: #0f172a;">
          </div>
          <div style="margin-bottom: 10px;">
            <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Live Room Humidity (%)</label>
            <input type="number" id="live-curr-hum" value="55" step="1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box; font-weight: 600; color: #0f172a;">
          </div>
          <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #166534; letter-spacing: 0.05em;" id="live-loc-title">Outdoor Weather (Open-Meteo)</span>
              <button id="btn-detect-loc" type="button" style="background: #dcfce7; border: 1px solid #86efac; font-size: 10px; font-weight: 700; color: #15803d; cursor: pointer; padding: 3px 8px; border-radius: 4px;">📍 GPS Detect</button>
            </div>
            <div style="display: flex; gap: 6px; margin-bottom: 8px;">
              <input type="text" id="live-city-input" placeholder="Enter city (e.g. Delhi, London, New York)" style="flex: 1; padding: 6px 8px; border-radius: 5px; border: 1px solid #86efac; font-size: 12px; background: white; color: #0f172a; outline: none;">
              <button id="btn-search-city" type="button" style="background: #15803d; color: white; border: none; border-radius: 5px; padding: 0 10px; font-size: 11px; font-weight: 700; cursor: pointer;">Set</button>
            </div>
            <div style="font-size: 12px; font-weight: 700; color: #15803d;" id="live-outdoor-display">Open-Meteo: Fetching...</div>
          </div>
          <div style="margin-bottom: 12px;">
            <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Live Dispatch Rate</label>
            <select id="live-interval-select" style="width: 100%; padding: 7px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 12px; font-weight: 600; color: #334155; box-sizing: border-box;">
              <option value="300" selected>Every 5 Minutes (Real-Time Control)</option>
              <option value="60">Every 1 Minute</option>
              <option value="5">Every 5 Seconds (Fast Demo)</option>
            </select>
          </div>
          <div id="live-timer-banner" style="display: none; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 6px 10px; font-size: 11px; color: #1e40af; font-weight: 600; margin-bottom: 12px; text-align: center;">
            Next Live Reading in: <span id="live-countdown-text">5:00</span>
          </div>
        </div>

        <button class="btn" id="btn-run-simulation" style="width: 100%; background: #0f172a; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          Schedule
        </button>

        <div id="confidence-widget" style="text-align: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
          <h4 style="margin:0 0 4px 0; color: #475569; font-weight: 600; font-size: 12px; text-transform: uppercase;">AI Model Confidence</h4>
          <div style="font-size: 36px; font-weight: 800; color: #16a34a; line-height: 1;" id="conf-score">--%</div>
        </div>
      </div>
      
      <!-- Right Visualization & Wisp Decision Panel -->
      <div style="flex: 2; min-width: 500px; display: flex; flex-direction: column; gap: 20px;">
        
        <!-- Action & Cost Card -->
        <div id="wisp-decision-panel" style="background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
            <div>
              <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 2px;">Thermostat Status</div>
              <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: #0f172a;" id="action-title">AWAITING SCHEDULE</h2>
            </div>
            <div id="action-badge" style="padding: 6px 14px; border-radius: 9999px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: #94a3b8; color: white; transition: all 0.3s ease;">
              IDLE
            </div>
          </div>

          <!-- Explanation -->
          <div id="action-explanation" style="font-size: 13px; color: #334155; line-height: 1.5; background: #f8fafc; padding: 12px 14px; border-radius: 8px; border-left: 4px solid #94a3b8; margin-bottom: 16px; min-height: 40px; transition: all 0.3s ease;">
            Click "Schedule" to begin the real-time thermostat simulation.
          </div>

          <!-- Cost Grid -->
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px;">
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Standard Cost</div>
              <div style="font-size: 18px; font-weight: 700; color: #ef4444; margin-top: 4px;" id="cost-legacy">$0.00</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Cygnix Cost</div>
              <div style="font-size: 18px; font-weight: 700; color: #10b981; margin-top: 4px;" id="cost-neural">$0.00</div>
            </div>
            <div style="background: #ecfdf5; padding: 10px 8px; border-radius: 8px; border: 1px solid #a7f3d0; text-align: center;">
              <div style="font-size: 11px; color: #059669; font-weight: 700; text-transform: uppercase;">Total Savings</div>
              <div style="font-size: 18px; font-weight: 800; color: #059669; margin-top: 4px;" id="cost-savings">$0.00</div>
            </div>
          </div>

          <!-- Key Metrics Grid -->
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Current Temp</div>
              <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px;" id="m-curr-temp">--°F</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Battery</div>
              <div style="font-size: 20px; font-weight: 700; color: #059669; margin-top: 4px;" id="m-battery-power">0.0 kWh</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Comfort Target</div>
              <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px;" id="m-pref-band">--</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Time Elapsed</div>
              <div style="font-size: 20px; font-weight: 700; color: #2563eb; margin-top: 4px;" id="m-time">0 min</div>
            </div>
          </div>

        </div>

        <!-- Telemetry Feed -->
        <div style="background: white; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          <h3 style="margin: 0 0 8px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em;">Live Telemetry Stream</h3>
          <div id="telemetry-feed" style="background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; padding: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #334155; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; height: 100px;">
            <div style="color: #94a3b8;">> Awaiting initialization...</div>
          </div>
        </div>

        <!-- Chart Area -->
        <div style="background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); flex: 1;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h3 style="margin: 0; font-size: 15px; color: #0f172a; font-weight: 700;">Live Temperature Trajectory</h3>
            <span style="font-size: 11px; color: #64748b;" id="chart-status">Ready</span>
          </div>
          <div style="position: relative; height: 260px; width: 100%;">
            <canvas id="predictionChart"></canvas>
          </div>
        </div>
        
      </div>
    </div>
  `;

  // UI Toggles
  const radios = container.querySelectorAll('input[name="pred-source"]');
  const simInputs = container.querySelector('#sim-inputs');
  const liveInputs = container.querySelector('#live-inputs');

  let liveSensorPollTimer = null;
  let cachedLiveOutdoorTemp = 82.0;
  let cachedLiveOutdoorHum = 65.0;
  let cachedLocationName = "Local";
  let userLat = null;
  let userLon = null;
  let userCity = "";

  const requestBrowserLocation = () => {
    if (navigator.geolocation) {
      const outdoorEl = container.querySelector("#live-outdoor-display");
      if (outdoorEl) outdoorEl.innerText = "Requesting GPS Location...";
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          userLat = pos.coords.latitude;
          userLon = pos.coords.longitude;
          userCity = "";
          fetchLiveSensorData();
        },
        (err) => {
          console.log("Geolocation permission not granted or unavailable, using IP location.", err);
          fetchLiveSensorData();
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    } else {
      fetchLiveSensorData();
    }
  };

  const fetchLiveSensorData = async () => {
    try {
      let url = "http://localhost:8000/api/live/sensor";
      const params = [];
      if (userLat !== null && userLon !== null) {
        params.push(`lat=${userLat}&lon=${userLon}`);
      } else if (userCity) {
        params.push(`loc=${encodeURIComponent(userCity)}`);
      }
      if (params.length) {
        url += `?${params.join("&")}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const badge = container.querySelector("#live-sensor-badge");
        const portEl = container.querySelector("#live-sensor-port");
        const outdoorEl = container.querySelector("#live-outdoor-display");
        const tempInput = container.querySelector("#live-curr-temp");
        const humInput = container.querySelector("#live-curr-hum");
        const cityInput = container.querySelector("#live-city-input");

        if (data.connected) {
          if (badge) {
            badge.innerText = "ONLINE";
            badge.style.background = "#dcfce7";
            badge.style.color = "#15803d";
          }
          if (portEl) portEl.innerText = `${data.port} @ 115200 baud`;
        } else {
          if (badge) {
            badge.innerText = "OFFLINE";
            badge.style.background = "#fee2e2";
            badge.style.color = "#b91c1c";
          }
          if (portEl) portEl.innerText = "No active ESP32 data on USB (115200 baud)";
        }

        if (data.indoor_temp_f && tempInput && !isSimulating) {
          tempInput.value = data.indoor_temp_f.toFixed(1);
        }
        if (data.indoor_humidity && humInput && !isSimulating) {
          humInput.value = data.indoor_humidity.toFixed(1);
        }
        if (data.outdoor_temp_f !== undefined) {
          cachedLiveOutdoorTemp = data.outdoor_temp_f;
          cachedLiveOutdoorHum = data.outdoor_humidity || 65.0;
          cachedLocationName = data.location || "Local";
          if (outdoorEl) {
            outdoorEl.innerText = `${data.outdoor_temp_f.toFixed(1)}°F | ${cachedLiveOutdoorHum.toFixed(0)}% RH (${cachedLocationName})`;
          }
          if (cityInput && !cityInput.matches(':focus') && !userCity && data.location) {
            cityInput.placeholder = `Current: ${data.location}`;
          }
        }
      }
    } catch (e) {
      // Backend polling error
    }
  };

  fetchLiveSensorData();
  liveSensorPollTimer = setInterval(fetchLiveSensorData, 2000);

  const locBtn = container.querySelector("#btn-detect-loc");
  if (locBtn) {
    locBtn.addEventListener("click", () => {
      requestBrowserLocation();
    });
  }

  const cityInput = container.querySelector("#live-city-input");
  const searchBtn = container.querySelector("#btn-search-city");
  const handleCitySearch = () => {
    if (!cityInput) return;
    const val = cityInput.value.trim();
    if (val) {
      userCity = val;
      userLat = null;
      userLon = null;
      const outdoorEl = container.querySelector("#live-outdoor-display");
      if (outdoorEl) outdoorEl.innerText = `Fetching Open-Meteo weather for ${val}...`;
      fetchLiveSensorData();
    }
  };

  if (searchBtn) {
    searchBtn.addEventListener("click", handleCitySearch);
  }
  if (cityInput) {
    cityInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleCitySearch();
      }
    });
  }

  radios.forEach(r => {
    r.addEventListener('change', (e) => {
      if (e.target.value === 'simulation') {
        simInputs.style.display = 'block';
        liveInputs.style.display = 'none';
      } else {
        simInputs.style.display = 'none';
        liveInputs.style.display = 'block';
        requestBrowserLocation();
      }
    });
  });

  const getActionBadgeStyle = (actName) => {
    switch (actName) {
      case 'NO_ACTION': return { bg: '#94a3b8', text: 'IDLE (NO ACTION)' };
      case 'COOL_LOW': return { bg: '#38bdf8', text: 'COOLING (MODULATED)' };
      case 'COOL_MEDIUM': return { bg: '#0ea5e9', text: 'COOLING (BALANCED)' };
      case 'COOL_HIGH': return { bg: '#0284c7', text: 'COOLING (MAXIMUM)' };
      case 'PRECOOL': return { bg: '#10b981', text: 'PRE-COOLING' };
      case 'REDUCE_HVAC': return { bg: '#f59e0b', text: 'SETBACK' };
      default: return { bg: '#0f172a', text: actName };
    }
  };

  const logTelemetry = (msg, isSuccess = false) => {
    const feed = container.querySelector('#telemetry-feed');
    const line = document.createElement('div');
    line.style.color = isSuccess ? '#10b981' : '#334155';
    line.style.fontWeight = isSuccess ? '600' : '400';
    line.innerText = `> ${msg}`;
    feed.appendChild(line);
    feed.scrollTop = feed.scrollHeight;
  };

  const initChart = () => {
    const canvas = container.querySelector('#predictionChart');
    if (!canvas || !window.Chart) return;
    const ctx = canvas.getContext('2d');
    
    if (chartInstance) chartInstance.destroy();

    chartInstance = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: chartLabels,
        datasets: [
          {
            label: 'Lower Confidence',
            data: lowerBoundData,
            borderColor: 'transparent',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: '+1', // Fill to next dataset
            pointRadius: 0
          },
          {
            label: 'Predicted Temp (°F)',
            data: actualTempData,
            borderColor: '#0f172a',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
            pointBackgroundColor: '#0f172a',
            pointRadius: 4,
            pointBorderColor: 'white',
            pointBorderWidth: 2
          },
          {
            label: 'Upper Confidence',
            data: upperBoundData,
            borderColor: 'transparent',
            fill: false,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 400,
          easing: 'linear'
        },
        scales: {
          y: {
            grid: { color: '#f1f5f9' },
            suggestedMin: 68,
            suggestedMax: 78
          },
          x: {
            grid: { display: false }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
          }
        }
      }
    });
  };

  let simulatedCurrentTemp = 76.5;

  const performSimulationStep = async (stepCount) => {
    const pLow = parseFloat(container.querySelector('#pref-temp-low').value) || 70.0;
    const pHigh = parseFloat(container.querySelector('#pref-temp-high').value) || 74.0;
    const outTemp = parseFloat(container.querySelector('#sim-outdoor-temp').value) || 82.0;
    const solKw = parseFloat(container.querySelector('#sim-solar-kw').value) || 0.0;
    const tod = container.querySelector('#sim-tod').value;
    const mode = container.querySelector('input[name="pred-source"]:checked')?.value || 'simulation';
    
    // ToD Logic
    let tariff = 10.0;
    let isDay = true;
    if (tod === 'Midnight') { tariff = 3.0; isDay = false; }
    else if (tod === 'Morning') { tariff = 10.0; isDay = true; }
    else if (tod === 'Afternoon') { tariff = 25.0; isDay = true; }
    else if (tod === 'Night') { tariff = 10.0; isDay = false; }
    
    let activeSolar = isDay ? solKw : 0.0;

    let currHum = 50.0;
    let actualOutdoor = outTemp;
    if (mode === 'live') {
      simulatedCurrentTemp = parseFloat(container.querySelector('#live-curr-temp').value) || 75.2;
      currHum = parseFloat(container.querySelector('#live-curr-hum').value) || 55.0;
      actualOutdoor = cachedLiveOutdoorTemp || 81.1;
      if (stepCount === 0) {
        logTelemetry(`Live mode initialized. Sensor: ${simulatedCurrentTemp}°F | Outdoor (${cachedLocationName}): ${actualOutdoor}°F`);
      }
    } else if (stepCount === 0) {
      simulatedCurrentTemp = parseFloat(container.querySelector('#sim-curr-temp').value) || 76.5;
      logTelemetry(`Booting Agent... Analyzing ${outTemp}°F outdoor temp.`);
    }

    logTelemetry(`[Step ${stepCount}] Sending thermal vector to API...`);

    try {
      const response = await fetch("http://localhost:8000/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zone_id: "main_zone",
          current_temp: simulatedCurrentTemp,
          current_humidity: currHum,
          outdoor_temp: actualOutdoor,
          preferred_temp_low: pLow,
          preferred_temp_high: pHigh,
          solar_kw: activeSolar,
          tariff_rate: tariff,
          mode: "COOLING"
        })
      });
      
      if (!response.ok) throw new Error("API responded with " + response.status);
      const data = await response.json();
      
      // Compute Battery & Cost Savings
      const hvacPower = data.hvac_power_kw !== undefined ? data.hvac_power_kw : (data.action && data.action.includes("COOL") ? 1.75 : 0.0);
      let gridPull = 0.0;

      if (activeSolar > hvacPower) {
        const excess = activeSolar - hvacPower;
        batteryStorage = Math.min(13.5, batteryStorage + excess);
        logTelemetry(`Charging battery with ${excess.toFixed(2)}kW excess solar`);
      } else {
        let deficit = hvacPower - activeSolar;
        if (batteryStorage >= deficit) {
          batteryStorage -= deficit;
          if (deficit > 0) logTelemetry(`Discharging battery to cover ${deficit.toFixed(2)}kW load`);
        } else {
          gridPull = deficit - batteryStorage;
          batteryStorage = 0;
          if (deficit > 0) {
            logTelemetry(`Battery depleted. Pulling ${gridPull.toFixed(2)}kW from grid at ${tariff}¢/kWh.`);
          }
        }
      }

      container.querySelector("#m-battery-power").innerText = `${batteryStorage.toFixed(1)} kWh`;

      const cygnixCost = gridPull > 0 ? (gridPull * 0.25) * (tariff / 100) : 0;
      let legacyCost = 0.0;
      if (simulatedCurrentTemp > pHigh || data.action.includes('COOL')) {
        let legacyDeficit = Math.max(0, 3.5 - activeSolar);
        legacyCost = (legacyDeficit * 0.25) * (tariff / 100);
      }
      
      cumulativeNeuralCost += cygnixCost;
      cumulativeLegacyCost += legacyCost;
      const savings = cumulativeLegacyCost - cumulativeNeuralCost;

      container.querySelector("#cost-legacy").innerText = `$${cumulativeLegacyCost.toFixed(3)}`;
      container.querySelector("#cost-neural").innerText = `$${cumulativeNeuralCost.toFixed(3)}`;
      container.querySelector("#cost-savings").innerText = `$${Math.max(0, savings).toFixed(3)}`;

      // Update Chart Data Arrays
      const elapsedMins = stepCount * 15;
      const timeStr = elapsedMins === 0 ? "Now" : `+${elapsedMins}m`;
      chartLabels.push(timeStr);
      
      const temp = data.current_temp;
      actualTempData.push(temp);
      
      // Simulate narrowing uncertainty funnel
      const uncertainty = Math.max(0.1, 1.5 - (stepCount * 0.1));
      upperBoundData.push(temp + uncertainty);
      lowerBoundData.push(temp - uncertainty);

      if (chartInstance) {
        chartInstance.update();
      } else {
        initChart();
      }

      // Update UI Action Card
      const confScore = container.querySelector("#conf-score");
      confScore.innerText = data.confidence_score + "%";
      if (data.confidence_score >= 80) confScore.style.color = "#16a34a";
      else if (data.confidence_score >= 50) confScore.style.color = "#eab308";
      else confScore.style.color = "#dc2626";

      const badgeInfo = getActionBadgeStyle(data.action);
      const badge = container.querySelector("#action-badge");
      badge.style.background = badgeInfo.bg;
      badge.innerText = badgeInfo.text;
      
      container.querySelector("#action-title").innerText = badgeInfo.text;
      container.querySelector("#action-explanation").innerText = data.explanation;
      container.querySelector("#action-explanation").style.borderLeftColor = badgeInfo.bg;
      
      container.querySelector("#m-curr-temp").innerText = `${data.current_temp.toFixed(1)}°F`;
      container.querySelector("#m-pref-band").innerText = `[${pLow}, ${pHigh}]°F`;
      container.querySelector("#m-time").innerText = `${elapsedMins} min`;

      // Telemetry updates
      logTelemetry(`Action Selected: ${data.action} (${hvacPower.toFixed(2)} kW)`, true);
      if (cygnixCost < legacyCost) {
        logTelemetry(`Action avoided ${((legacyCost - cygnixCost)*100).toFixed(1)}¢ excess cost.`);
      }

      // Progress to next temp
      simulatedCurrentTemp = data.trajectory[0].predicted_temp;

    } catch (err) {
      console.warn("Simulation API call failed:", err);
      logTelemetry(`ERROR: ${err.message}`, false);
      stopSimulation();
    }
  };

  let countdownTimer = null;
  let secondsRemaining = 0;

  const updateCountdownDisplay = () => {
    const banner = container.querySelector("#live-timer-banner");
    const countText = container.querySelector("#live-countdown-text");
    if (!banner || !countText) return;
    const mins = Math.floor(secondsRemaining / 60);
    const secs = secondsRemaining % 60;
    countText.innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const stopSimulation = () => {
    isSimulating = false;
    clearInterval(simInterval);
    clearInterval(countdownTimer);
    const banner = container.querySelector("#live-timer-banner");
    if (banner) banner.style.display = "none";
    const btn = container.querySelector("#btn-run-simulation");
    if (btn) {
      btn.innerHTML = "Schedule";
      btn.style.background = "#0f172a";
    }
    container.querySelector("#chart-status").innerText = "Paused";
  };

  const startSimulation = () => {
    isSimulating = true;
    simStepCount = 0;
    
    // Reset Data
    chartLabels = [];
    actualTempData = [];
    upperBoundData = [];
    lowerBoundData = [];
    cumulativeNeuralCost = 0.0;
    cumulativeLegacyCost = 0.0;
    batteryStorage = 0.0;
    
    container.querySelector('#telemetry-feed').innerHTML = '';
    const batEl = container.querySelector('#m-battery-power');
    if (batEl) batEl.innerText = '0.0 kWh';
    
    if (chartInstance) chartInstance.destroy();
    initChart();

    const mode = container.querySelector('input[name="pred-source"]:checked')?.value || 'simulation';
    const intervalSecs = mode === 'live' 
      ? (parseInt(container.querySelector('#live-interval-select')?.value) || 300) 
      : 2.5;

    const banner = container.querySelector("#live-timer-banner");
    if (mode === 'live' && banner) {
      banner.style.display = "block";
      secondsRemaining = intervalSecs;
      updateCountdownDisplay();
      clearInterval(countdownTimer);
      countdownTimer = setInterval(() => {
        secondsRemaining--;
        if (secondsRemaining <= 0) {
          secondsRemaining = intervalSecs;
        }
        updateCountdownDisplay();
      }, 1000);
    } else if (banner) {
      banner.style.display = "none";
    }

    const btn = container.querySelector("#btn-run-simulation");
    btn.innerHTML = mode === 'live' ? "Stop Live Monitoring" : "Stop Schedule";
    btn.style.background = "#dc2626";
    container.querySelector("#chart-status").innerText = "Running";

    // Step 0
    performSimulationStep(simStepCount);

    const tickMs = intervalSecs * 1000;
    const maxSteps = mode === 'live' ? 1000 : MAX_SIM_STEPS;

    simInterval = setInterval(() => {
      simStepCount++;
      if (simStepCount >= maxSteps) {
        stopSimulation();
        container.querySelector("#chart-status").innerText = "Completed";
        const savings = cumulativeLegacyCost - cumulativeNeuralCost;
        logTelemetry(`Schedule complete. Total savings: $${savings.toFixed(3)}`, true);
        return;
      }
      secondsRemaining = intervalSecs;
      updateCountdownDisplay();
      performSimulationStep(simStepCount);
    }, tickMs);
  };

  container.querySelector("#btn-run-simulation").addEventListener("click", () => {
    if (isSimulating) {
      stopSimulation();
    } else {
      startSimulation();
    }
  });

  return container;
}
