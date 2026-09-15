export function renderMetricsTab(state, selectedThermostat = "upstairs", onFilterChange) {
  const container = document.createElement("div");
  container.className = "tab-content metrics-tab";

  const renderContent = (simLogs = []) => {
    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Analytics & Operations</h1>
          <div class="page-subtitle">Historical energy consumption, cost analysis, and system logs.</div>
        </div>
      </div>

      <!-- Filter Card -->
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 24px; display: flex; gap: 24px; flex-wrap: wrap; align-items: flex-end;">
        <div style="flex: 1; min-width: 200px;">
          <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Thermostat Source</label>
          <select id="metrics-thermostat" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
            <option value="all">All Thermostats (Home)</option>
            <option value="live_room">Live Room Thermostat</option>
            <option value="simulation">Simulation</option>
          </select>
        </div>
        <div style="flex: 1; min-width: 200px;">
          <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Time Range</label>
          <select id="metrics-range" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
            <option value="30">Last 30 Days</option>
            <option value="14">Last 14 Days</option>
            <option value="7">Last 7 Days</option>
          </select>
        </div>
        <button class="btn" id="btn-load-metrics" style="background: #0f172a; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: 600; cursor: pointer; height: 40px;">
          Refresh Analytics
        </button>
      </div>

      <!-- Chart Area: SPLIT GRAPHS -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px;">
        <!-- Cost Graph -->
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <h3 style="margin: 0 0 20px 0; font-size: 16px; color: #0f172a; font-weight: 600;">Monetary Cost (USD)</h3>
          <div style="position: relative; height: 250px; width: 100%;">
            <canvas id="costChart"></canvas>
          </div>
        </div>
        <!-- Energy Graph -->
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <h3 style="margin: 0 0 20px 0; font-size: 16px; color: #0f172a; font-weight: 600;">Energy Consumption (kWh)</h3>
          <div style="position: relative; height: 250px; width: 100%;">
            <canvas id="energyChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Simulation History -->
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-bottom: 32px;">
        <h3 style="margin: 0 0 20px 0; font-size: 16px; color: #0f172a; font-weight: 600;">Interactive Simulation History (Mini DB)</h3>
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
            <thead>
              <tr style="border-bottom: 2px solid #e2e8f0; color: #64748b;">
                <th style="padding: 12px 16px;">Timestamp</th>
                <th style="padding: 12px 16px;">Time of Day (ToD)</th>
                <th style="padding: 12px 16px;">Start Temp</th>
                <th style="padding: 12px 16px;">Solar (kW)</th>
                <th style="padding: 12px 16px;">Legacy Cost</th>
                <th style="padding: 12px 16px;">Cygnix Cost</th>
                <th style="padding: 12px 16px; color: #059669; font-weight: 700;">Total Saved</th>
              </tr>
            </thead>
            <tbody>
              ${simLogs.length === 0 ? '<tr><td colspan="7" style="padding: 24px; text-align: center; color: #64748b;">No simulations run yet.</td></tr>' : 
                simLogs.map(log => `
                <tr style="border-bottom: 1px solid #f1f5f9;">
                  <td style="padding: 12px 16px; color: #475569; font-family: monospace;">${log.timestamp}</td>
                  <td style="padding: 12px 16px;">
                    <span style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #f1f5f9; color: #475569;">
                      ${log.time_of_day}
                    </span>
                  </td>
                  <td style="padding: 12px 16px; color: #0f172a;">${log.initial_temp}°F</td>
                  <td style="padding: 12px 16px; color: #d97706;">${log.solar_kw} kW</td>
                  <td style="padding: 12px 16px; color: #ef4444;">$${log.legacy_cost.toFixed(3)}</td>
                  <td style="padding: 12px 16px; color: #2563eb;">$${log.neural_cost.toFixed(3)}</td>
                  <td style="padding: 12px 16px; color: #059669; font-weight: 700;">$${log.total_savings.toFixed(3)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- System Logs -->
      <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
        <h3 style="margin: 0 0 20px 0; font-size: 16px; color: #0f172a; font-weight: 600;">System Event Logs</h3>
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">
            <thead>
              <tr style="border-bottom: 2px solid #e2e8f0; color: #64748b;">
                <th style="padding: 12px 16px;">Timestamp</th>
                <th style="padding: 12px 16px;">Level</th>
                <th style="padding: 12px 16px;">Tag</th>
                <th style="padding: 12px 16px;">Message</th>
              </tr>
            </thead>
            <tbody>
              ${state.detailedLogs.map(log => `
                <tr style="border-bottom: 1px solid #f1f5f9;">
                  <td style="padding: 12px 16px; color: #475569; font-family: monospace;">${log.time}</td>
                  <td style="padding: 12px 16px;">
                    <span style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; 
                      background: ${log.level === 'INFO' ? '#eff6ff' : log.level === 'WARN' ? '#fffbeb' : '#fef2f2'};
                      color: ${log.level === 'INFO' ? '#2563eb' : log.level === 'WARN' ? '#d97706' : '#dc2626'};">
                      ${log.level}
                    </span>
                  </td>
                  <td style="padding: 12px 16px; color: #64748b; font-family: monospace;">${log.tag}</td>
                  <td style="padding: 12px 16px; color: #0f172a;">${log.message}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    let costChartInstance = null;
    let energyChartInstance = null;

    const loadAndRenderCharts = async () => {
      const days = parseInt(container.querySelector('#metrics-range').value);

      try {
        const res = await fetch("http://localhost:8000/api/metrics");
        if(!res.ok) throw new Error("API Error");
        
        let data = await res.json();
        if(data.error) throw new Error(data.error);

        // Filter by days
        const sliceIdx = Math.max(0, data.dates.length - days);
        const labels = data.dates.slice(sliceIdx);
        
        // 1. Cost Chart
        const costCanvas = container.querySelector('#costChart');
        if (costChartInstance) costChartInstance.destroy();
        costChartInstance = new window.Chart(costCanvas.getContext('2d'), {
          type: 'line',
          data: {
            labels,
            datasets: [{
              label: 'Cost (USD)',
              data: data.cost_usd.slice(sliceIdx),
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              borderWidth: 3,
              fill: true,
              tension: 0.4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: true, title: { display: true, text: 'USD ($)' } } }
          }
        });

        // 2. Energy Chart
        const energyCanvas = container.querySelector('#energyChart');
        if (energyChartInstance) energyChartInstance.destroy();
        energyChartInstance = new window.Chart(energyCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels,
            datasets: [{
              label: 'Energy (kWh)',
              data: data.energy_kwh.slice(sliceIdx),
              backgroundColor: 'rgba(37, 99, 235, 0.7)',
              borderColor: '#2563eb',
              borderWidth: 1,
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: true, title: { display: true, text: 'kWh' } } }
          }
        });

      } catch (e) {
        console.error(e);
      }
    };

    container.querySelector('#btn-load-metrics').addEventListener('click', loadAndRenderCharts);
    setTimeout(() => loadAndRenderCharts(), 100);
  };

  // Fetch sim logs first, then render
  fetch("http://localhost:8000/api/sim_logs")
    .then(res => res.json())
    .then(data => renderContent(data))
    .catch(err => {
      console.warn("Could not fetch sim logs for metrics tab:", err);
      renderContent([]);
    });

  return container;
}
