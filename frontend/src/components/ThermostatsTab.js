export function renderThermostatsTab(state, setState) {
  const container = document.createElement("div");
  container.className = "tab-content thermostats-tab";

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Hardware Terminals</h1>
        <div class="page-subtitle">Connected physical HVAC controllers</div>
      </div>
    </div>

    <div class="zones-grid" style="max-width: 600px;">
      ${state.thermostats
        .map(
          (t) => `
        <div class="zone-card thermostat-card" data-id="${t.id}" style="cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
          <div class="zone-card-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 16px;">
            <div>
              <h2 class="zone-title" style="margin: 0 0 4px 0; font-size: 16px; color: #0f172a; font-weight: 600;">${t.name}</h2>
              <div class="zone-entity-id" style="font-size: 12px; color: #64748b; font-family: monospace;">${t.entity} · ${t.model}</div>
            </div>
            <span style="font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 4px; background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0;">
              ${t.status}
            </span>
          </div>

          <div class="zone-stats-list" style="display: flex; flex-direction: column; gap: 12px;">
            <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
              <span class="zone-stat-label" style="color: #64748b;">Assigned Zone</span>
              <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${t.zone}</span>
            </div>
            <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
              <span class="zone-stat-label" style="color: #64748b;">Current Reading</span>
              <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${t.currentTemp}</span>
            </div>
            <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
              <span class="zone-stat-label" style="color: #64748b;">Target Setpoint</span>
              <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${t.targetTemp}</span>
            </div>
            <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
              <span class="zone-stat-label" style="color: #64748b;">Relative Humidity</span>
              <span class="zone-stat-value" style="font-weight: 500; color: #0f172a;">${t.humidity}</span>
            </div>
            <div class="zone-stat-row" style="display: flex; justify-content: space-between; font-size: 14px;">
              <span class="zone-stat-label" style="color: #64748b;">Firmware</span>
              <span class="zone-stat-value" style="font-weight: 500; font-family: monospace; font-size: 12px; background: #f8fafc; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2e8f0;">${t.firmware}</span>
            </div>
          </div>
          <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9; text-align: center; color: #2563eb; font-size: 13px; font-weight: 600;">
            Click to launch Prediction Engine &rarr;
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  // Add hover effects and click listeners
  container.querySelectorAll('.thermostat-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-2px)';
      card.style.boxShadow = '0 10px 15px -3px rgb(0 0 0 / 0.1)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'translateY(0)';
      card.style.boxShadow = 'none';
    });
    card.addEventListener('click', () => {
      if (setState) {
        setState({ activeTab: 'predictions' });
      }
    });
  });

  return container;
}
