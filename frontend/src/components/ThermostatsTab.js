export function renderThermostatsTab(state) {
  const container = document.createElement("div");
  container.className = "tab-content thermostats-tab";

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Thermostats</h1>
        <div class="page-subtitle">Connected HVAC hardware controllers and zone assignments</div>
      </div>
      <button class="btn btn-outline" id="btn-discover-thermostats">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        Discover devices
      </button>
    </div>

    <div class="zones-grid" style="max-width: 100%;">
      ${state.thermostats
        .map(
          (t) => `
        <div class="zone-card">
          <div class="zone-card-header">
            <div>
              <h2 class="zone-title">${t.name}</h2>
              <div class="zone-entity-id">${t.entity} · ${t.model}</div>
            </div>
            <span class="badge badge-green">${t.status}</span>
          </div>

          <div class="zone-stats-list">
            <div class="zone-stat-row">
              <span class="zone-stat-label">Assigned Zone</span>
              <span class="zone-stat-value">${t.zone}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Current Reading</span>
              <span class="zone-stat-value">${t.currentTemp}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Target Setpoint</span>
              <span class="zone-stat-value">${t.targetTemp}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Relative Humidity</span>
              <span class="zone-stat-value">${t.humidity}</span>
            </div>
            <div class="zone-stat-row">
              <span class="zone-stat-label">Firmware</span>
              <span class="cycle-badge">${t.firmware}</span>
            </div>
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  return container;
}
