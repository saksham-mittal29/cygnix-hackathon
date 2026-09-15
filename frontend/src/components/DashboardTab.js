export function renderDashboardTab(state, setState) {
  const container = document.createElement("div");
  container.className = "tab-content dashboard-tab";

  const totalZones = state.zones.length;

  const renderContent = (logsData = []) => {
    // Render System Mode Panel
    const currentMode = state.systemMode || "automatic";
    let systemModeHTML = '';
    if (currentMode === "automatic") {
      systemModeHTML = `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h3 style="margin: 0 0 8px 0; color: #0f172a; font-size: 16px; font-weight: 600;">System Status: Automatic Mode</h3>
            <p style="margin: 0; color: #475569; font-size: 14px;">System is running under predictive automation.</p>
          </div>
          <button class="btn" id="btn-stop-auto" style="background: white; border: 1px solid #cbd5e1; color: #0f172a; padding: 10px 16px; border-radius: 6px; font-weight: 500; cursor: pointer;">
            Manual Override
          </button>
        </div>
      `;
    } else if (currentMode === "manual_pending") {
      systemModeHTML = `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px;">
            <div>
              <h3 style="margin: 0 0 8px 0; color: #0f172a; font-size: 16px; font-weight: 600;">Manual Override Configuration</h3>
              <p style="margin: 0; color: #475569; font-size: 14px;">Define manual setpoints. The system will halt predictive automation.</p>
            </div>
            <button class="btn" id="btn-start-manual" style="background: #0f172a; color: white; border: none; padding: 10px 24px; border-radius: 6px; font-weight: 600; cursor: pointer;">
              Apply Settings
            </button>
          </div>
          
          <div style="display: flex; gap: 24px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 220px;">
              <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Target Temperature (°F)</label>
              <input type="number" id="manual-temp" value="${state.manualSettings.temp}" step="0.5" style="width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 14px; box-sizing: border-box;">
            </div>
            <div style="flex: 1; min-width: 220px;">
              <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">HVAC Mode</label>
              <select id="manual-mode" style="width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 14px; box-sizing: border-box; background: white;">
                <option value="COOLING" ${state.manualSettings.mode === "COOLING" ? "selected" : ""}>Cooling</option>
                <option value="HEATING" ${state.manualSettings.mode === "HEATING" ? "selected" : ""}>Heating</option>
                <option value="FAN_ONLY" ${state.manualSettings.mode === "FAN_ONLY" ? "selected" : ""}>Fan Only</option>
              </select>
            </div>
            <div style="flex: 1; min-width: 220px;">
              <label style="display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px;">Airflow / Fan Speed</label>
              <select id="manual-airflow" style="width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #cbd5e1; font-family: inherit; font-size: 14px; box-sizing: border-box; background: white;">
                <option value="Auto" ${state.manualSettings.airflow === "Auto" ? "selected" : ""}>Auto Configuration</option>
                <option value="Low" ${state.manualSettings.airflow === "Low" ? "selected" : ""}>Low Volume</option>
                <option value="High" ${state.manualSettings.airflow === "High" ? "selected" : ""}>High Volume</option>
              </select>
            </div>
          </div>
        </div>
      `;
    } else if (currentMode === "manual") {
      systemModeHTML = `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h3 style="margin: 0 0 8px 0; color: #0f172a; font-size: 16px; font-weight: 600;">System Status: Manual Override</h3>
            <p style="margin: 0; color: #475569; font-size: 14px;">Active parameters: ${state.manualSettings.temp}°F | Mode: ${state.manualSettings.mode}</p>
          </div>
          <button class="btn" id="btn-return-auto" style="background: white; border: 1px solid #cbd5e1; color: #0f172a; padding: 10px 16px; border-radius: 6px; font-weight: 500; cursor: pointer;">
            Resume Automation
          </button>
        </div>
      `;
    }

    // Recent Test Data
    const latestTest = logsData.length > 0 ? logsData[0] : null;
    const testDataHTML = latestTest ? `
      <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 16px; border-radius: 8px; margin-bottom: 32px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h4 style="margin: 0 0 4px 0; color: #065f46; font-size: 14px;">Recent Interactive Test Results</h4>
          <div style="font-size: 12px; color: #047857;">Run at: ${latestTest.timestamp} | ToD: ${latestTest.time_of_day} | Start Temp: ${latestTest.initial_temp}°F</div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 11px; color: #059669; font-weight: 700; text-transform: uppercase;">Total Run Savings</div>
          <div style="font-size: 20px; font-weight: 800; color: #059669;">$${latestTest.total_savings.toFixed(3)}</div>
        </div>
      </div>
    ` : '';

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Dashboard Overview</h1>
          <div class="page-subtitle">${totalZones} operational zones · Updated ${state.lastUpdated}</div>
        </div>
        <button class="btn" id="btn-refresh-dash" style="background: white; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 6px; font-weight: 500; cursor: pointer; color: #475569;">
          Refresh Data
        </button>
      </div>

      ${systemModeHTML}

      <!-- Navigation Routing Cards -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px;">
        
        <div class="nav-card" id="nav-sim" style="background: white; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #0f172a; display: flex; align-items: center; gap: 8px;">
            Interactive Simulation
          </h3>
          <p style="margin: 0; font-size: 13px; color: #64748b;">Run local climate simulation with customizable weather, solar, and Time-of-Day inputs.</p>
        </div>

        <div class="nav-card" id="nav-live" style="background: white; border: 1px solid #e2e8f0; padding: 24px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #0f172a; display: flex; align-items: center; gap: 8px;">
            Live Sensor Stream
          </h3>
          <p style="margin: 0; font-size: 13px; color: #64748b;">Use live telemetry data streaming from the local DHT22 Arduino sensor.</p>
        </div>

      </div>

      ${testDataHTML}

      <h2 style="font-size: 16px; color: #0f172a; margin-bottom: 16px; font-weight: 600;">Hardware Zone Status</h2>
      <div class="zones-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
        ${state.zones
          .map(
            (zone) => {
              const displayTemp = currentMode === "manual" && state.manualSettings ? state.manualSettings.temp + ".0°F" : zone.setpoint;
              const displayMode = currentMode === "manual" && state.manualSettings ? state.manualSettings.mode : zone.mode;
              
              return `
          <div class="zone-card" id="zone-card-${zone.id}" style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
            <div class="zone-card-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 16px;">
              <div>
                <h2 class="zone-title" style="margin: 0 0 4px 0; font-size: 15px; color: #0f172a; font-weight: 600;">${zone.name}</h2>
                <div class="zone-entity-id" style="font-size: 12px; color: #64748b; font-family: monospace;">${zone.entityId}</div>
              </div>
              <span style="font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 4px; background: ${displayMode === 'COOLING' ? '#eff6ff' : '#f8fafc'}; color: ${displayMode === 'COOLING' ? '#2563eb' : '#475569'}; border: 1px solid ${displayMode === 'COOLING' ? '#bfdbfe' : '#e2e8f0'};">
                ${displayMode}
              </span>
            </div>

            <div class="zone-stats-list" style="display: flex; flex-direction: column; gap: 12px;">
              <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
                <span class="zone-stat-label" style="color: #64748b;">Ambient Temp</span>
                <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${zone.ambient}</span>
              </div>
              <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
                <span class="zone-stat-label" style="color: #64748b;">Target Setpoint</span>
                <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${displayTemp}</span>
              </div>
              <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
                <span class="zone-stat-label" style="color: #64748b;">Current Cycle</span>
                <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${zone.cycle}</span>
              </div>
            </div>
          </div>
        `;
        })
        .join("")}
      </div>
    `;

    // Handlers
    container.querySelector("#btn-refresh-dash")?.addEventListener("click", () => {
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setState({ lastUpdated: timeString });
    });

    // Routing Cards
    container.querySelector("#nav-sim")?.addEventListener("click", () => {
      setState({ activeTab: "predictions", predictionSource: "simulation" });
    });
    
    container.querySelector("#nav-live")?.addEventListener("click", () => {
      setState({ activeTab: "predictions", predictionSource: "live" });
    });

    // Hover effects for cards
    container.querySelectorAll('.nav-card').forEach(card => {
      card.addEventListener('mouseover', () => {
        card.style.borderColor = '#2563eb';
        card.style.transform = 'translateY(-2px)';
      });
      card.addEventListener('mouseout', () => {
        card.style.borderColor = '#e2e8f0';
        card.style.transform = 'translateY(0)';
      });
    });

    // Mode Handlers
    container.querySelector("#btn-stop-auto")?.addEventListener("click", () => {
      setState({ systemMode: "manual_pending" });
    });
    
    container.querySelector("#btn-start-manual")?.addEventListener("click", () => {
      const temp = parseFloat(container.querySelector("#manual-temp").value);
      const mode = container.querySelector("#manual-mode").value;
      const airflow = container.querySelector("#manual-airflow").value;
      
        const newLog = {
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        level: "INFO",
        tag: "[system]",
        message: `User manual override detected. Parameters: ${temp}°F, ${mode}, ${airflow}`
      };
      
      setState({
        systemMode: "manual",
        manualSettings: { temp, mode, airflow },
        detailedLogs: [newLog, ...state.detailedLogs]
      });
    });
    
    container.querySelector("#btn-return-auto")?.addEventListener("click", () => {
      const newLog = {
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        level: "INFO",
        tag: "[system]",
        message: `Returned to automatic control.`
      };
      
      setState({ 
          systemMode: "automatic",
          activeTab: "predictions",
          predictionSource: "simulation", // route to simulation automatically
          detailedLogs: [newLog, ...state.detailedLogs]
      });
    });
  };

  // Fetch sim logs first, then render
  fetch("http://localhost:8000/api/sim_logs")
    .then(res => res.json())
    .then(data => renderContent(data))
    .catch(err => {
      console.warn("Could not fetch sim logs for dashboard:", err);
      renderContent([]);
    });

  return container;
}
