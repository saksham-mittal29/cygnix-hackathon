export function renderPredictionsTab(state) {
  const container = document.createElement("div");
  container.className = "tab-content predictions-tab";

  // Initial default state data
  const initialTemp = 76.5;
  const initialPrefLow = 70.0;
  const initialPrefHigh = 74.0;
  const initialOutdoor = 82.0;
  const initialSolar = 3.0;
  const initialTariff = 10.0;

  container.innerHTML = `
    <div class="page-header" style="margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 class="page-title" style="font-size: 24px; font-weight: 700; color: #0f172a; margin: 0 0 4px 0;">AI Prediction & Wisp RL Controller</h1>
          <div class="page-subtitle" style="font-size: 13px; color: #64748b;">Neural State-Space Thermal Forecasting & Deep Q-Network Policy Dispatch</div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="display: inline-flex; align-items: center; gap: 6px; background: #ecfdf5; color: #059669; padding: 6px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; border: 1px solid #a7f3d0;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulse 2s infinite;"></span> Backend Live: Port 8000
          </span>
        </div>
      </div>
    </div>

    <!-- Visual 6-Stage Control Pipeline -->
    <div style="background: white; padding: 14px 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
      <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; flex-wrap: wrap; gap: 8px;">
        <span style="display: flex; align-items: center; gap: 6px; color: #2563eb;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #2563eb;"></span> 1. Sense</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="display: flex; align-items: center; gap: 6px; color: #0284c7;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #0284c7;"></span> 2. Predict (+5, +15, +30m)</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="display: flex; align-items: center; gap: 6px; color: #059669;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #059669;"></span> 3. ACI Confidence</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="display: flex; align-items: center; gap: 6px; color: #d97706;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #d97706;"></span> 4. Personalize</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="display: flex; align-items: center; gap: 6px; color: #7c3aed;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #7c3aed;"></span> 5. Wisp DQN</span>
        <span style="color: #cbd5e1;">➔</span>
        <span style="display: flex; align-items: center; gap: 6px; color: #dc2626;"><span style="width: 8px; height: 8px; border-radius: 50%; background: #dc2626;"></span> 6. Act & Optimize</span>
      </div>
    </div>
    
    <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 30px;">
      
      <!-- Left Controls Panel -->
      <div style="flex: 1; min-width: 320px; background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <!-- Demo Presets -->
        <div style="margin-bottom: 18px;">
          <label style="display: block; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; margin-bottom: 6px;">
            ⚡ Quick Test Scenarios
          </label>
          <select id="demo-scenario-select" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; font-weight: 600; background: #f8fafc; color: #0f172a; cursor: pointer;">
            <option value="moderately_warm" selected>2. Moderately Warm (76.5°F > 74°F Upper Bound)</option>
            <option value="comfortable">1. Comfortable (72.0°F in [70, 74]°F Comfort Band)</option>
            <option value="severe_heat">3. Severe Heat (81.0°F Indoor, 98°F Outdoor)</option>
            <option value="overcooled">4. Overcooled (67.5°F < 70°F Lower Bound)</option>
            <option value="high_solar">5. High Solar (75.5°F, 8.0 kW Solar Surplus)</option>
            <option value="peak_tariff">6. Peak Tariff Spike (76.0°F, $50.0/kWh Tariff)</option>
          </select>
        </div>

        <div style="display: flex; gap: 16px; margin-bottom: 18px;">
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;">
            <input type="radio" name="pred-source" value="simulation" checked style="accent-color: #2563eb; width: 16px; height: 16px;">
            Simulation Mode
          </label>
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;">
            <input type="radio" name="pred-source" value="live" style="accent-color: #2563eb; width: 16px; height: 16px;">
            Live Sensor (DHT22)
          </label>
        </div>

        <!-- Simulation Inputs -->
        <div id="sim-inputs" style="display: block;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Current Temp (°F)</label>
              <input type="number" id="sim-curr-temp" value="${initialTemp}" step="0.5" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Outdoor Temp (°F)</label>
              <input type="number" id="sim-outdoor-temp" value="${initialOutdoor}" step="1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
          </div>

          <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 12px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px;">Occupant Comfort Preference</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
              <div>
                <label style="display: block; font-size: 11px; color: #475569; margin-bottom: 4px;">Pref Low (°F)</label>
                <input type="number" id="pref-temp-low" value="${initialPrefLow}" step="0.5" style="width: 100%; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; box-sizing: border-box;">
              </div>
              <div>
                <label style="display: block; font-size: 11px; color: #475569; margin-bottom: 4px;">Pref High (°F)</label>
                <input type="number" id="pref-temp-high" value="${initialPrefHigh}" step="0.5" style="width: 100%; padding: 6px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 12px; box-sizing: border-box;">
              </div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Solar Power (kW)</label>
              <input type="number" id="sim-solar-kw" value="${initialSolar}" step="0.5" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Tariff Rate ($/kWh)</label>
              <input type="number" id="sim-tariff-rate" value="${initialTariff}" step="1.0" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 13px; box-sizing: border-box;">
            </div>
          </div>
        </div>

        <!-- Live Inputs -->
        <div id="live-inputs" style="display: none;">
          <div style="background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 12px;">
            <span style="font-size: 11px; color: #64748b;">Arduino DHT22 Sensor Live Telemetry</span>
          </div>
          <div style="margin-bottom: 10px;">
            <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Current Temp (°F)</label>
            <input type="number" id="live-curr-temp" value="75.2" step="0.1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box;">
          </div>
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Current Humidity (%)</label>
            <input type="number" id="live-curr-hum" value="55" step="1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box;">
          </div>
        </div>

        <button class="btn" id="btn-run-inference" style="width: 100%; background: #0f172a; color: white; border: none; padding: 14px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; transition: background 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          Run Wisp RL Policy Inference
        </button>

        <div id="confidence-widget" style="text-align: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
          <h4 style="margin:0 0 4px 0; color: #475569; font-weight: 600; font-size: 12px; text-transform: uppercase;">Inference Confidence (ACI)</h4>
          <div style="font-size: 36px; font-weight: 800; color: #16a34a; line-height: 1;" id="conf-score">94%</div>
        </div>
      </div>
      
      <!-- Right Visualization & Wisp Decision Panel -->
      <div style="flex: 2; min-width: 500px; display: flex; flex-direction: column; gap: 20px;">
        
        <!-- Wisp Controller Real Decision Card -->
        <div id="wisp-decision-panel" style="background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
            <div>
              <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 2px;">Active Control Policy</div>
              <h2 style="margin: 0; font-size: 18px; font-weight: 700; color: #0f172a;" id="wisp-ctrl-title">Wisp Deep Q-Network (DQN)</h2>
            </div>
            <div id="action-badge" style="padding: 6px 14px; border-radius: 9999px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: #2563eb; color: white;">
              COOL_MEDIUM (BALANCED)
            </div>
          </div>

          <!-- Explanation -->
          <div id="action-explanation" style="font-size: 13px; color: #334155; line-height: 1.5; background: #f8fafc; padding: 12px 14px; border-radius: 8px; border-left: 4px solid #2563eb; margin-bottom: 16px;">
            Moderate cooling is selected to control predicted warming and stabilize indoor conditions within occupant comfort bounds.
          </div>

          <!-- Key Metrics Grid -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-bottom: 18px;">
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Current Temp</div>
              <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;" id="m-curr-temp">76.5°F</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Preferred Band</div>
              <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;" id="m-pref-band">[70, 74]°F</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Predicted +30m</div>
              <div style="font-size: 15px; font-weight: 700; color: #2563eb; margin-top: 2px;" id="m-pred-30">75.33°F</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">HVAC Power</div>
              <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;" id="m-hvac-kw">2.31 kW</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Est. Cost</div>
              <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;" id="m-cost">$0.00</div>
            </div>
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Step Reward</div>
              <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-top: 2px;" id="m-reward">-1.88</div>
            </div>
          </div>

          <!-- Q-Values Breakdown Bar -->
          <div>
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 8px;">DQN Q-Values (All 6 Discrete Actions)</div>
            <div id="q-values-container" style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; font-size: 11px; text-align: center;">
              <div style="background: #f1f5f9; color: #334155; padding: 6px 4px; border-radius: 6px; font-weight: 500; border: 1px solid #cbd5e1;"><div style="font-size: 9px;">NO ACTION</div><div style="font-size: 11px; margin-top: 2px;">-17.94</div></div>
              <div style="background: #f1f5f9; color: #334155; padding: 6px 4px; border-radius: 6px; font-weight: 500; border: 1px solid #cbd5e1;"><div style="font-size: 9px;">COOL LOW</div><div style="font-size: 11px; margin-top: 2px;">-14.70</div></div>
              <div style="background: #0f172a; color: white; padding: 6px 4px; border-radius: 6px; font-weight: 700; border: 2px solid #2563eb;"><div style="font-size: 9px;">COOL MED</div><div style="font-size: 11px; margin-top: 2px;">-12.91 ★</div></div>
              <div style="background: #f1f5f9; color: #334155; padding: 6px 4px; border-radius: 6px; font-weight: 500; border: 1px solid #cbd5e1;"><div style="font-size: 9px;">COOL HIGH</div><div style="font-size: 11px; margin-top: 2px;">-13.39</div></div>
              <div style="background: #f1f5f9; color: #334155; padding: 6px 4px; border-radius: 6px; font-weight: 500; border: 1px solid #cbd5e1;"><div style="font-size: 9px;">PRECOOL</div><div style="font-size: 11px; margin-top: 2px;">-12.95</div></div>
              <div style="background: #f1f5f9; color: #334155; padding: 6px 4px; border-radius: 6px; font-weight: 500; border: 1px solid #cbd5e1;"><div style="font-size: 9px;">REDUCE</div><div style="font-size: 11px; margin-top: 2px;">-17.22</div></div>
            </div>
          </div>

        </div>

        <!-- Chart Area -->
        <div style="background: white; padding: 22px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <h3 style="margin: 0; font-size: 15px; color: #0f172a; font-weight: 700;">Thermal Trajectory Forecast vs Comfort Band</h3>
            <span style="font-size: 11px; color: #64748b;">Person 2 Multi-Horizon Dynamic Modeling</span>
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
  const scenarioSelect = container.querySelector('#demo-scenario-select');

  radios.forEach(r => {
    r.addEventListener('change', (e) => {
      if (e.target.value === 'simulation') {
        simInputs.style.display = 'block';
        liveInputs.style.display = 'none';
      } else {
        simInputs.style.display = 'none';
        liveInputs.style.display = 'block';
      }
    });
  });

  // Demo Scenario Selector Handler
  scenarioSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val === 'comfortable') {
      container.querySelector('#sim-curr-temp').value = '72.0';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '72.0';
      container.querySelector('#sim-solar-kw').value = '2.0';
      container.querySelector('#sim-tariff-rate').value = '10.0';
    } else if (val === 'moderately_warm') {
      container.querySelector('#sim-curr-temp').value = '76.5';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '82.0';
      container.querySelector('#sim-solar-kw').value = '3.0';
      container.querySelector('#sim-tariff-rate').value = '10.0';
    } else if (val === 'severe_heat') {
      container.querySelector('#sim-curr-temp').value = '81.0';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '98.0';
      container.querySelector('#sim-solar-kw').value = '6.0';
      container.querySelector('#sim-tariff-rate').value = '20.0';
    } else if (val === 'overcooled') {
      container.querySelector('#sim-curr-temp').value = '67.5';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '68.0';
      container.querySelector('#sim-solar-kw').value = '0.0';
      container.querySelector('#sim-tariff-rate').value = '10.0';
    } else if (val === 'high_solar') {
      container.querySelector('#sim-curr-temp').value = '75.5';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '85.0';
      container.querySelector('#sim-solar-kw').value = '8.0';
      container.querySelector('#sim-tariff-rate').value = '15.0';
    } else if (val === 'peak_tariff') {
      container.querySelector('#sim-curr-temp').value = '76.0';
      container.querySelector('#pref-temp-low').value = '70.0';
      container.querySelector('#pref-temp-high').value = '74.0';
      container.querySelector('#sim-outdoor-temp').value = '86.0';
      container.querySelector('#sim-solar-kw').value = '0.0';
      container.querySelector('#sim-tariff-rate').value = '50.0';
    }
    // Execute inference immediately on scenario switch
    executeInference();
  });

  let chartInstance = null;

  const renderChart = (trajectory, currentTemp, prefLow, prefHigh) => {
    const canvas = container.querySelector('#predictionChart');
    if (!canvas || !window.Chart) return;

    const times = ["Now", "+5m", "+15m", "+30m"];
    const actualData = [currentTemp, trajectory[0].predicted_temp, trajectory[1].predicted_temp, trajectory[2].predicted_temp];
    const highData = [prefHigh, prefHigh, prefHigh, prefHigh];
    const lowData = [prefLow, prefLow, prefLow, prefLow];

    if (chartInstance) {
      chartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    chartInstance = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: times,
        datasets: [
          {
            label: 'Predicted Temperature (°F)',
            data: actualData,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.12)',
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#2563eb',
            pointRadius: 5
          },
          {
            label: 'Preferred Upper Bound (°F)',
            data: highData,
            borderColor: '#ef4444',
            borderWidth: 2,
            borderDash: [4, 4],
            fill: false,
            pointRadius: 0
          },
          {
            label: 'Preferred Lower Bound (°F)',
            data: lowData,
            borderColor: '#0284c7',
            borderWidth: 2,
            borderDash: [4, 4],
            fill: false,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            suggestedMin: Math.min(...actualData, prefLow) - 1.5,
            suggestedMax: Math.max(...actualData, prefHigh) + 1.5,
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false }
          }
        },
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  };

  const getActionBadgeStyle = (actName) => {
    switch (actName) {
      case 'NO_ACTION': return { bg: '#64748b', text: 'NO ACTION (IDLE)' };
      case 'COOL_LOW': return { bg: '#0284c7', text: 'COOL LOW (MODULATED)' };
      case 'COOL_MEDIUM': return { bg: '#2563eb', text: 'COOL MEDIUM (BALANCED)' };
      case 'COOL_HIGH': return { bg: '#7c3aed', text: 'COOL HIGH (MAX COOL)' };
      case 'PRECOOL': return { bg: '#059669', text: 'PRECOOL (SOLAR/FORECAST)' };
      case 'REDUCE_HVAC': return { bg: '#d97706', text: 'REDUCE HVAC (SETBACK)' };
      default: return { bg: '#2563eb', text: actName };
    }
  };

  const executeInference = async () => {
    const btn = container.querySelector("#btn-run-inference");
    if (btn) {
      btn.innerHTML = "Processing Wisp RL Inference...";
      btn.disabled = true;
    }

    const mode = container.querySelector('input[name="pred-source"]:checked')?.value || 'simulation';
    
    let currentTemp, currHum, outTemp, pLow, pHigh, solarKw, tariffRate;

    if (mode === 'simulation') {
      currentTemp = parseFloat(container.querySelector('#sim-curr-temp').value) || 76.5;
      currHum = 50.0;
      outTemp = parseFloat(container.querySelector('#sim-outdoor-temp').value) || 82.0;
      pLow = parseFloat(container.querySelector('#pref-temp-low').value) || 70.0;
      pHigh = parseFloat(container.querySelector('#pref-temp-high').value) || 74.0;
      solarKw = parseFloat(container.querySelector('#sim-solar-kw').value) || 3.0;
      tariffRate = parseFloat(container.querySelector('#sim-tariff-rate').value) || 10.0;
    } else {
      currentTemp = parseFloat(container.querySelector('#live-curr-temp').value) || 75.2;
      currHum = parseFloat(container.querySelector('#live-curr-hum').value) || 55.0;
      outTemp = 85.0;
      pLow = 70.0;
      pHigh = 74.0;
      solarKw = 2.0;
      tariffRate = 10.0;
    }

    try {
      const response = await fetch("http://localhost:8000/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zone_id: "main_zone",
          current_temp: currentTemp,
          current_humidity: currHum,
          outdoor_temp: outTemp,
          preferred_temp_low: pLow,
          preferred_temp_high: pHigh,
          solar_kw: solarKw,
          tariff_rate: tariffRate,
          mode: "COOLING"
        })
      });
      
      if (!response.ok) throw new Error("Backend API responded with " + response.status);
      const data = await response.json();
      
      // 1. Render Chart
      renderChart(data.trajectory, currentTemp, pLow, pHigh);
      
      // 2. Render Confidence Score
      const confScore = container.querySelector("#conf-score");
      if (confScore) {
        confScore.innerText = data.confidence_score + "%";
        if (data.confidence_score >= 80) confScore.style.color = "#16a34a";
        else if (data.confidence_score >= 50) confScore.style.color = "#eab308";
        else confScore.style.color = "#dc2626";
      }

      // 3. Render Wisp Decision Card
      const badgeInfo = getActionBadgeStyle(data.action);
      const badge = container.querySelector("#action-badge");
      if (badge) {
        badge.style.background = badgeInfo.bg;
        badge.innerText = badgeInfo.text;
      }

      const expl = container.querySelector("#action-explanation");
      if (expl) {
        expl.style.borderLeftColor = badgeInfo.bg;
        expl.innerText = data.explanation;
      }

      // Metrics
      container.querySelector("#m-curr-temp").innerText = `${data.current_temp}°F`;
      container.querySelector("#m-pref-band").innerText = `[${data.preferred_temp_low}, ${data.preferred_temp_high}]°F`;
      container.querySelector("#m-pred-30").innerText = `${data.trajectory[2].predicted_temp}°F`;
      container.querySelector("#m-hvac-kw").innerText = `${data.hvac_power_kw} kW`;
      container.querySelector("#m-cost").innerText = `$${data.estimated_cost}`;
      container.querySelector("#m-reward").innerText = `${data.reward}`;

      // Q-Values Breakdown
      const qCont = container.querySelector("#q-values-container");
      if (qCont && data.q_values) {
        qCont.innerHTML = "";
        for (const [aName, qVal] of Object.entries(data.q_values)) {
          const isSelected = aName === data.action;
          const box = document.createElement("div");
          box.style.background = isSelected ? "#0f172a" : "#f1f5f9";
          box.style.color = isSelected ? "white" : "#334155";
          box.style.padding = "6px 4px";
          box.style.borderRadius = "6px";
          box.style.fontWeight = isSelected ? "700" : "500";
          box.style.border = isSelected ? "2px solid #2563eb" : "1px solid #cbd5e1";
          box.innerHTML = `
            <div style="font-size: 9px; text-transform: uppercase;">${aName.replace('_', ' ')}</div>
            <div style="font-size: 11px; margin-top: 2px;">${qVal}${isSelected ? ' ★' : ''}</div>
          `;
          qCont.appendChild(box);
        }
      }

    } catch (err) {
      console.warn("Backend API call:", err);
    } finally {
      if (btn) {
        btn.innerHTML = "Run Wisp RL Policy Inference";
        btn.disabled = false;
      }
    }
  };

  container.querySelector("#btn-run-inference").addEventListener("click", executeInference);

  // Initial draw and fetch on mount
  setTimeout(() => {
    executeInference();
  }, 100);

  return container;
}
