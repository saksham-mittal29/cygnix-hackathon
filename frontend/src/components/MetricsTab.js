export function renderMetricsTab(state, selectedThermostat = "upstairs", onFilterChange) {
  const container = document.createElement("div");
  container.className = "tab-content metrics-tab";

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
        <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Metric View</label>
        <select id="metrics-type" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit;">
          <option value="cost_energy">Cost & Energy Usage</option>
          <option value="runtime">HVAC Runtime</option>
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
        Load Data
      </button>
    </div>

    <!-- Chart Area -->
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
      <h3 id="chart-title" style="margin: 0 0 20px 0; font-size: 16px; color: #0f172a; font-weight: 600;">Energy & Cost Overview</h3>
      <div style="position: relative; height: 350px; width: 100%;">
        <canvas id="metricsChart"></canvas>
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

  let chartInstance = null;

  const loadAndRenderChart = async () => {
    const type = container.querySelector('#metrics-type').value;
    const days = parseInt(container.querySelector('#metrics-range').value);

    try {
      const res = await fetch("http://localhost:8000/api/metrics");
      if(!res.ok) throw new Error("API Error");
      
      let data = await res.json();
      if(data.error) throw new Error(data.error);

      // Filter by days
      const sliceIdx = Math.max(0, data.dates.length - days);
      const labels = data.dates.slice(sliceIdx);
      
      let datasets = [];

      if (type === 'cost_energy') {
        container.querySelector('#chart-title').innerText = "Energy (kWh) & Cost ($)";
        datasets = [
          {
            label: 'Cost (USD)',
            data: data.cost_usd.slice(sliceIdx),
            type: 'line',
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            borderWidth: 3,
            yAxisID: 'y-cost'
          },
          {
            label: 'Energy (kWh)',
            data: data.energy_kwh.slice(sliceIdx),
            type: 'bar',
            backgroundColor: 'rgba(37, 99, 235, 0.5)',
            borderColor: '#2563eb',
            borderWidth: 1,
            yAxisID: 'y-energy'
          }
        ];
      } else {
        container.querySelector('#chart-title').innerText = "HVAC Equipment Runtime (minutes)";
        // In dataset it's technically seconds or arbitrary runtime metric. Let's just plot it raw for now.
        datasets = [
          {
            label: 'Cooling Runtime',
            data: data.cooling_time.slice(sliceIdx),
            type: 'bar',
            backgroundColor: '#3b82f6',
            stacked: true
          },
          {
            label: 'Heating Runtime',
            data: data.heating_time.slice(sliceIdx),
            type: 'bar',
            backgroundColor: '#f97316',
            stacked: true
          }
        ];
      }

      const canvas = container.querySelector('#metricsChart');
      if (chartInstance) chartInstance.destroy();

      const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: {}
      };

      if (type === 'cost_energy') {
        options.scales = {
          'y-energy': { type: 'linear', position: 'left', title: { display: true, text: 'Energy (kWh)' } },
          'y-cost': { type: 'linear', position: 'right', title: { display: true, text: 'Cost ($)' }, grid: { drawOnChartArea: false } }
        };
      } else {
        options.scales = {
          x: { stacked: true },
          y: { stacked: true, title: { display: true, text: 'Runtime Units' } }
        };
      }

      chartInstance = new window.Chart(canvas.getContext('2d'), {
        data: { labels, datasets },
        options
      });

    } catch (e) {
      console.error(e);
      alert("Failed to load metrics from API.");
    }
  };

  container.querySelector('#btn-load-metrics').addEventListener('click', loadAndRenderChart);

  // Initial load
  setTimeout(() => loadAndRenderChart(), 100);

  return container;
}
