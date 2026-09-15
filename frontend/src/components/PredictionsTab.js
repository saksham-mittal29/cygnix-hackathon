export function renderPredictionsTab(state) {
  const container = document.createElement("div");
  container.className = "tab-content predictions-tab";

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">AI Prediction Engine</h1>
        <div class="page-subtitle">Neural State-Space Trajectory Forecasting</div>
      </div>
    </div>
    
    <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 30px;">
      
      <!-- Controls Panel -->
      <div style="flex: 1; min-width: 320px; background: white; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
        
        <h3 style="margin-top:0; font-size: 16px; color: #475569; font-weight: 600; margin-bottom: 20px;">Data Source</h3>
        
        <div style="display: flex; gap: 16px; margin-bottom: 24px;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; font-weight: 500;">
            <input type="radio" name="pred-source" value="simulation" checked style="accent-color: #2563eb; width: 16px; height: 16px;">
            Simulation Mode
          </label>
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; font-weight: 500;">
            <input type="radio" name="pred-source" value="live" style="accent-color: #2563eb; width: 16px; height: 16px;">
            Live Data (DHT22)
          </label>
        </div>

        <div id="sim-inputs" style="display: block;">
          <h4 style="font-size: 14px; color: #64748b; margin-bottom: 12px;">Simulation Parameters</h4>
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Target Temperature (°F)</label>
            <input type="number" id="sim-target-temp" value="70" step="0.5" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          </div>
          <div style="margin-bottom: 24px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Target Humidity (%)</label>
            <input type="number" id="sim-target-hum" value="45" step="1" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          </div>
        </div>

        <div id="live-inputs" style="display: none;">
          <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 16px;">
            <span style="font-size: 12px; color: #64748b;">Arduino DHT22 Input Stream</span>
          </div>
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Current Temp (°F)</label>
            <input type="number" id="live-curr-temp" value="75.2" step="0.1" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          </div>
          <div style="margin-bottom: 16px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Current Humidity (%)</label>
            <input type="number" id="live-curr-hum" value="55" step="1" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          </div>
          <div style="margin-bottom: 24px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Target Temperature (°F)</label>
            <input type="number" id="live-target-temp" value="70" step="0.5" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          </div>
        </div>

        <button class="btn" id="btn-run-inference" style="width: 100%; background: #0f172a; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: background 0.2s;">
          Run Inference Engine
        </button>

        <div id="confidence-widget" style="display:none; text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid #e2e8f0;">
          <h4 style="margin:0 0 8px 0; color: #475569; font-weight: 600; font-size: 14px;">Inference Confidence</h4>
          <div style="font-size: 42px; font-weight: 700; color: #2563eb; line-height: 1;" id="conf-score">--%</div>
        </div>
      </div>
      
      <!-- Visualization Panel -->
      <div style="flex: 2; min-width: 500px; display: flex; flex-direction: column; gap: 24px;">
        
        <!-- Chart Area -->
        <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <h3 style="margin-top:0; font-size: 16px; color: #475569; font-weight: 600; margin-bottom: 20px;">Thermal Trajectory vs Target</h3>
          <div style="position: relative; height: 300px; width: 100%;">
            <canvas id="predictionChart"></canvas>
          </div>
        </div>
        
        <!-- Schedule Diagram -->
        <div id="schedule-diagram" style="display: none; background: white; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <h3 style="margin-top:0; font-size: 16px; color: #475569; font-weight: 600; margin-bottom: 20px;">Optimal HVAC Schedule Decided</h3>
          <div style="display: flex; height: 40px; border-radius: 6px; overflow: hidden; font-size: 12px; font-weight: 600; color: white; text-align: center; line-height: 40px;">
            <div style="flex: 1; background: #3b82f6;" title="Cooling Stage 1">T+0m (Cooling)</div>
            <div style="flex: 2; background: #60a5fa;" title="Fan Only">T+15m (Fan Circulation)</div>
            <div style="flex: 3; background: #94a3b8;" title="Idle">T+30m (Idle / Target Reached)</div>
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

  let chartInstance = null;

  const renderChart = (trajectory, currentTemp, targetTemp) => {
    const canvas = container.querySelector('#predictionChart');
    if (!canvas) return;

    const times = ["Now", "+5m", "+15m", "+30m"];
    const actualData = [currentTemp, trajectory[0].predicted_temp, trajectory[1].predicted_temp, trajectory[2].predicted_temp];
    const targetData = [targetTemp, targetTemp, targetTemp, targetTemp];

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
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#2563eb',
            pointRadius: 5
          },
          {
            label: 'Target Setpoint (°F)',
            data: targetData,
            borderColor: '#ef4444',
            borderWidth: 2,
            borderDash: [5, 5],
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
            suggestedMin: Math.min(...actualData, targetTemp) - 2,
            suggestedMax: Math.max(...actualData, targetTemp) + 2,
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

  container.querySelector("#btn-run-inference").addEventListener("click", async () => {
    const btn = container.querySelector("#btn-run-inference");
    btn.innerHTML = "Processing...";
    btn.disabled = true;

    const mode = container.querySelector('input[name="pred-source"]:checked').value;
    
    let currentTemp, targetTemp;
    if (mode === 'simulation') {
      currentTemp = parseFloat(state.zones.find(z => z.id === 'simulation').ambient) || 71.0;
      targetTemp = parseFloat(container.querySelector('#sim-target-temp').value);
    } else {
      currentTemp = parseFloat(container.querySelector('#live-curr-temp').value);
      targetTemp = parseFloat(container.querySelector('#live-target-temp').value);
    }

    try {
      const response = await fetch("http://localhost:8000/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zone_id: "test",
          current_temp: currentTemp,
          target_temp: targetTemp,
          mode: "COOLING"
        })
      });
      
      if (!response.ok) throw new Error("API error");
      const data = await response.json();
      
      renderChart(data.trajectory, currentTemp, targetTemp);
      
      container.querySelector("#confidence-widget").style.display = "block";
      container.querySelector("#schedule-diagram").style.display = "block";
      
      const confScore = container.querySelector("#conf-score");
      confScore.innerText = data.confidence_score + "%";
      
      if(data.confidence_score >= 80) confScore.style.color = "#16a34a";
      else if(data.confidence_score >= 50) confScore.style.color = "#eab308";
      else confScore.style.color = "#dc2626";
      
    } catch (err) {
      console.error(err);
      alert("Failed to reach backend API.");
    } finally {
      btn.innerHTML = "Run Inference Engine";
      btn.disabled = false;
    }
  });

  return container;
}
