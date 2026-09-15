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

  const initialTemp = 76.5;
  const initialPrefLow = 70.0;
  const initialPrefHigh = 74.0;
  const initialOutdoor = 82.0;
  const initialSolar = 0.0;
  const initialTariff = 10.0;

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
            <input type="radio" name="pred-source" value="simulation" checked style="accent-color: #2563eb; width: 16px; height: 16px;">
            Interactive Demo Mode
          </label>
          <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 13px; font-weight: 600; color: #334155;">
            <input type="radio" name="pred-source" value="live" style="accent-color: #2563eb; width: 16px; height: 16px;">
            Live Sensor (DHT22)
          </label>
        </div>

        <!-- Simulation Inputs -->
        <div id="sim-inputs" style="display: block;">
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
              <label style="display: block; font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">Tariff (¢/kWh)</label>
              <input type="number" id="sim-tariff-rate" value="${initialTariff}" step="1" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 13px; box-sizing: border-box;">
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
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div style="background: #f8fafc; padding: 10px 8px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
              <div style="font-size: 11px; color: #64748b; font-weight: 600;">Current Temp</div>
              <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px;" id="m-curr-temp">--°F</div>
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
    const tariff = parseFloat(container.querySelector('#sim-tariff-rate').value) || 10.0;
    const mode = container.querySelector('input[name="pred-source"]:checked')?.value || 'simulation';
    
    let currHum = 50.0;
    if (mode === 'live' && stepCount === 0) {
      simulatedCurrentTemp = parseFloat(container.querySelector('#live-curr-temp').value) || 75.2;
      currHum = parseFloat(container.querySelector('#live-curr-hum').value) || 55.0;
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
          outdoor_temp: outTemp,
          preferred_temp_low: pLow,
          preferred_temp_high: pHigh,
          solar_kw: solKw,
          tariff_rate: tariff,
          mode: "COOLING"
        })
      });
      
      if (!response.ok) throw new Error("API responded with " + response.status);
      const data = await response.json();
      
      // Compute Cost Savings
      const cygnixCost = data.estimated_cost;
      let legacyCost = 0.0;
      if (simulatedCurrentTemp > pHigh || data.action.includes('COOL')) {
        legacyCost = cygnixCost > 0 ? cygnixCost * (1.2 + Math.random() * 0.3) : ((3.5 * 0.25) * (tariff / 100));
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
      logTelemetry(`Action Selected: ${data.action}`, true);
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

  const stopSimulation = () => {
    isSimulating = false;
    clearInterval(simInterval);
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
    container.querySelector('#telemetry-feed').innerHTML = '';
    
    if (chartInstance) chartInstance.destroy();
    initChart();

    const btn = container.querySelector("#btn-run-simulation");
    btn.innerHTML = "Stop Schedule";
    btn.style.background = "#dc2626";
    container.querySelector("#chart-status").innerText = "Running";

    // Step 0
    performSimulationStep(simStepCount);

    simInterval = setInterval(() => {
      simStepCount++;
      if (simStepCount >= MAX_SIM_STEPS) {
        stopSimulation();
        container.querySelector("#chart-status").innerText = "Completed";
        logTelemetry(`Simulation complete. Total savings: $${(cumulativeLegacyCost - cumulativeNeuralCost).toFixed(3)}`, true);
        return;
      }
      performSimulationStep(simStepCount);
    }, 2500);
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
