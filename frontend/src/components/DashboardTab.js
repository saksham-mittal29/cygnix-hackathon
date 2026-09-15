export function renderDashboardTab(state, setState) {
  const container = document.createElement("div");
  container.className = "tab-content dashboard-tab";

  const totalZones = state.zones.length;
  const totalRooms = state.rooms.length;

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <div class="page-subtitle">${totalZones} zones · ${totalRooms} rooms · Updated ${state.lastUpdated}</div>
      </div>
      <button class="btn btn-outline" id="btn-refresh-dash">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
        </svg>
        Refresh
      </button>
    </div>

    <div class="dashboard-actions">
      <button class="vacation-mode-btn ${state.vacationMode ? "active" : ""}" id="btn-vacation-mode">
        <span>→</span>
        <span>${state.vacationMode ? "Disable vacation mode" : "Enable vacation mode"}</span>
      </button>
    </div>

    <div class="zones-grid">
      ${state.zones
        .map(
          (zone) => `
        <div class="zone-card" id="zone-card-${zone.id}">
          <div class="zone-card-header">
            <div>
              <h2 class="zone-title">${zone.name}</h2>
              <div class="zone-entity-id">${zone.entityId}</div>
            </div>
            <span class="zone-mode-badge ${zone.mode === "COOLING" ? "mode-cooling" : "mode-cool"}">
              ${zone.mode}
            </span>
          </div>

          <div class="zone-stats-list">
            <div class="zone-stat-row">
              <span class="zone-stat-label">Ambient</span>
              <span class="zone-stat-value">${zone.ambient}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Setpoint</span>
              <span class="zone-stat-value">${zone.setpoint}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Cycle</span>
              <span class="cycle-badge">${zone.cycle}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Active rooms</span>
              <span class="zone-stat-value">${zone.activeRooms}</span>
            </div>
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  // Handlers
  container.querySelector("#btn-refresh-dash").addEventListener("click", () => {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setState({
      lastUpdated: timeString
    });
  });

  container.querySelector("#btn-vacation-mode").addEventListener("click", () => {
    setState({
      vacationMode: !state.vacationMode
    });
  });

  return container;
}
