export function renderLogsTab(state, setState) {
  const container = document.createElement("div");
  container.className = "tab-content logs-tab";

  let activeSubtab = "history"; // Default to Cycle History matching the screenshot
  let activeWindow = "24h";
  let isPaused = false;
  let activeLevels = { info: true, warning: true, error: true };

  // Cycle history data
  let cycles = [
    {
      id: "1ed97f7a..",
      fullId: "1ed97f7a-867d-4346-a60e-383690708147",
      thermostat: "climate.upstairs_2",
      mode: "COOLING",
      outcome: "COMPLETED",
      started: "5/30/2026, 2:42:27 PM",
      ended: "5/30/2026, 3:12:15 PM",
      duration: "30m",
      roomsCount: 2,
      expanded: true,
      thermostatTemp: "70.0°F → 71.0°F",
      setpoint: "70.0°F → 68.0°F",
      endedReason: "completed",
      rooms: [
        {
          name: "Bedroom",
          trigger: "presence",
          triggerSub: "presence, holdover ends 5/30/2026, 4:35:03 PM",
          target: "70.0°F",
          startEnd: "70.0°F → 70.0°F",
          reached: "2:42:31 PM",
          ventClosed: "2:42:31 PM"
        },
        {
          name: "Office",
          trigger: "presence",
          triggerSub: "presence, holdover ends 5/30/2026, 3:39:01 PM",
          target: "70.0°F",
          startEnd: "73.0°F → 70.9°F",
          reached: "3:12:15 PM",
          ventClosed: "3:12:15 PM"
        }
      ],
      ventActivity: [
        { time: "2:42:27 PM", vent: "cover.bedroom_f503_bed_vent", action: "OPENED_AT_START" },
        { time: "2:42:27 PM", vent: "cover.office_a9c9_vent", action: "OPENED_AT_START" },
        { time: "2:42:31 PM", vent: "cover.bedroom_f503_bed_vent", action: "CLOSED_REACHED_TARGET", extra: "avg=70.0 target=70.0" },
        { time: "3:12:15 PM", vent: "cover.office_a9c9_vent", action: "CLOSED_REACHED_TARGET", extra: "avg=70.9 target=70.0" }
      ],
      setpointHistory: [
        { time: "2:42:31 PM", setpoint: "68.0°F", mode: "mode=cooling" }
      ]
    },
    {
      id: "503882b7..",
      fullId: "503882b7-124a-4311-b541-118820491024",
      thermostat: "climate.upstairs_2",
      mode: "COOLING",
      outcome: "COMPLETED",
      started: "5/30/2026, 2:27:14 PM",
      ended: "5/30/2026, 2:37:15 PM",
      duration: "10m",
      roomsCount: 3,
      expanded: false,
      thermostatTemp: "70.0°F → 70.5°F",
      setpoint: "70.0°F → 68.0°F",
      endedReason: "completed",
      rooms: [],
      ventActivity: [],
      setpointHistory: []
    },
    {
      id: "666d1568..",
      fullId: "666d1568-7cfa-4e88-a284-829104819284",
      thermostat: "climate.upstairs_2",
      mode: "COOLING",
      outcome: "COMPLETED",
      started: "5/30/2026, 2:04:38 PM",
      ended: "5/30/2026, 2:15:15 PM",
      duration: "11m",
      roomsCount: 1,
      expanded: false,
      thermostatTemp: "71.0°F → 70.8°F",
      setpoint: "71.0°F → 68.0°F",
      endedReason: "completed",
      rooms: [],
      ventActivity: [],
      setpointHistory: []
    }
  ];

  function renderContent() {
    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Logs</h1>
          <div class="page-subtitle">Cycle history, live event feed, and retention settings</div>
        </div>
        
        <div class="logs-header-actions">
          <button class="logs-subtab-btn ${activeSubtab === "live" ? "active" : ""}" id="subtab-live">
            Live Feed
          </button>
          <button class="logs-subtab-btn ${activeSubtab === "history" ? "active" : ""}" id="subtab-history">
            Cycle History
          </button>
          <button class="logs-subtab-btn ${activeSubtab === "retention" ? "active" : ""}" id="subtab-retention">
            Retention
          </button>
        </div>
      </div>

      ${
        activeSubtab === "history"
          ? `
        <!-- Cycle History Filters -->
        <div class="logs-controls-bar">
          <div class="logs-controls-row">
            <div class="logs-window-group">
              <span>Window:</span>
              ${["1h", "6h", "24h", "7d", "Custom"]
                .map(
                  (w) => `
                <button class="window-pill ${activeWindow === w ? "active" : ""}" data-window="${w}">
                  ${w}
                </button>
              `
                )
                .join("")}
              <button class="btn btn-outline btn-sm" id="btn-refresh-cycles" style="margin-left: 6px;">
                ↻ Refresh
              </button>
            </div>
          </div>
        </div>

        <!-- Cycle History Table -->
        <div class="logs-table-container">
          <div class="cycle-header-row cycle-table-head">
            <span>ID</span>
            <span>Thermostat</span>
            <span>Mode</span>
            <span>Outcome</span>
            <span>Started</span>
            <span>Ended</span>
            <span>Duration</span>
            <span>Rooms</span>
            <span></span>
          </div>

          ${cycles
            .map(
              (cycle, cIdx) => `
            <div class="cycle-card">
              <div class="cycle-header-row cycle-toggle-header" data-cycle-index="${cIdx}">
                <span class="cycle-id-text">${cycle.id}</span>
                <span class="cycle-entity-text">${cycle.thermostat}</span>
                <span><span class="badge badge-blue">${cycle.mode}</span></span>
                <span><span class="badge badge-blue">${cycle.outcome}</span></span>
                <span>${cycle.started}</span>
                <span>${cycle.ended}</span>
                <span>${cycle.duration}</span>
                <span>${cycle.roomsCount}</span>
                <span style="font-size: 10px; color: var(--text-secondary);">${cycle.expanded ? "▲" : "▼"}</span>
              </div>

              ${
                cycle.expanded
                  ? `
                <div class="cycle-details-panel">
                  <!-- Summary mini cards -->
                  <div class="cycle-summary-cards">
                    <div class="cycle-mini-card">
                      <div class="cycle-mini-card-label">Thermostat temp</div>
                      <div class="cycle-mini-card-val">${cycle.thermostatTemp}</div>
                    </div>
                    <div class="cycle-mini-card">
                      <div class="cycle-mini-card-label">Setpoint</div>
                      <div class="cycle-mini-card-val">${cycle.setpoint}</div>
                    </div>
                    <div class="cycle-mini-card">
                      <div class="cycle-mini-card-label">Ended reason</div>
                      <div class="cycle-mini-card-val">${cycle.endedReason}</div>
                    </div>
                  </div>

                  <!-- Rooms table -->
                  <div class="cycle-inner-box">
                    <div class="cycle-inner-box-title">Rooms</div>
                    <table class="cycle-rooms-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Trigger</th>
                          <th>Target</th>
                          <th>Start → End</th>
                          <th>Reached</th>
                          <th>Vent closed</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        ${cycle.rooms
                          .map(
                            (r) => `
                          <tr>
                            <td><strong>${r.name}</strong></td>
                            <td>
                              <div><strong>${r.trigger}</strong></div>
                              <div class="cycle-trigger-sub">${r.triggerSub}</div>
                            </td>
                            <td><strong>${r.target}</strong></td>
                            <td>${r.startEnd}</td>
                            <td>${r.reached}</td>
                            <td>${r.ventClosed}</td>
                            <td style="text-align: right;">
                              <button class="btn btn-outline btn-sm">View chart</button>
                            </td>
                          </tr>
                        `
                          )
                          .join("")}
                      </tbody>
                    </table>
                  </div>

                  <!-- Vent activity box -->
                  <div class="cycle-inner-box">
                    <div class="cycle-inner-box-title">Vent activity (${cycle.ventActivity.length})</div>
                    <div class="cycle-vent-log-list">
                      ${cycle.ventActivity
                        .map(
                          (va) => `
                        <div class="vent-log-line">
                          <span class="vent-log-time">${va.time}</span>
                          <span class="vent-log-entity">${va.vent}</span>
                          <span class="vent-log-badge">${va.action}</span>
                          ${va.extra ? `<span style="color: var(--text-muted); font-size: 11px;">${va.extra}</span>` : ""}
                        </div>
                      `
                        )
                        .join("")}
                    </div>
                  </div>

                  <!-- Setpoint history box -->
                  <div class="cycle-inner-box">
                    <div class="cycle-inner-box-title">Setpoint history (${cycle.setpointHistory.length})</div>
                    <div class="cycle-vent-log-list">
                      ${cycle.setpointHistory
                        .map(
                          (sh) => `
                        <div class="vent-log-line">
                          <span class="vent-log-time">${sh.time}</span>
                          <span style="font-weight: 700;">${sh.setpoint}</span>
                          <span style="color: var(--text-muted);">${sh.mode}</span>
                        </div>
                      `
                        )
                        .join("")}
                    </div>
                  </div>
                </div>
              `
                  : ""
              }
            </div>
          `
            )
            .join("")}
        </div>
      `
          : activeSubtab === "live"
          ? `
        <!-- Live Feed Controls -->
        <div class="logs-controls-bar">
          <div class="logs-controls-row">
            <div class="logs-window-group">
              <span>Window:</span>
              ${["1h", "6h", "24h", "7d", "Custom"]
                .map(
                  (w) => `
                <button class="window-pill ${activeWindow === w ? "active" : ""}" data-window="${w}">
                  ${w}
                </button>
              `
                )
                .join("")}
            </div>

            <div>
              <select class="logs-category-select" id="logs-category-select">
                <option>All categories</option>
                <option>reconcile</option>
                <option>engine</option>
                <option>presence</option>
                <option>api</option>
              </select>
            </div>

            <div class="logs-levels-group">
              <span>Levels:</span>
              <button class="level-toggle-pill level-info ${activeLevels.info ? "" : "inactive"}" id="toggle-info">info</button>
              <button class="level-toggle-pill level-warning ${activeLevels.warning ? "" : "inactive"}" id="toggle-warning">warning</button>
              <button class="level-toggle-pill level-error ${activeLevels.error ? "" : "inactive"}" id="toggle-error">error</button>
            </div>

            <div class="logs-status-group">
              <span>50 events</span>
              <button class="btn-pause-logs" id="btn-pause-logs">${isPaused ? "▶ Resume" : "⏸ Pause"}</button>
              <button class="btn-clear-logs-red" id="btn-clear-logs">Clear logs</button>
            </div>
          </div>
        </div>

        <button class="btn-load-older" id="btn-load-older">
          Load older entries
        </button>

        <div class="logs-table-container">
          ${(state.detailedLogs || [])
            .filter((log) => {
              const lvl = log.level.toLowerCase();
              return activeLevels[lvl] !== false;
            })
            .map(
              (log, idx) => `
            <div class="log-entry-row" id="log-row-${idx}">
              <span class="log-timestamp">${log.time}</span>
              <span class="log-level-badge ${
                log.level === "INFO"
                  ? "level-badge-info"
                  : log.level === "WARNING"
                  ? "level-badge-warning"
                  : "level-badge-error"
              }">${log.level}</span>
              <span class="log-tag">${log.tag}</span>
              <span class="log-message-text">${log.message}</span>
              <span class="log-arrow">▼</span>
            </div>
          `
            )
            .join("")}
        </div>
      `
          : `
        <!-- Retention Settings -->
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px; box-shadow: var(--shadow-card); max-width: 600px;">
          <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 12px;">Data Retention Policies</h3>
          <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 20px;">
            Configure how long cycle records, telemetry samples, and debug logs are kept in storage.
          </p>
          <div class="form-group">
            <label class="form-label">Cycle history retention</label>
            <select class="form-select">
              <option>30 days</option>
              <option selected>90 days (Default)</option>
              <option>180 days</option>
              <option>1 year</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">High-frequency telemetry samples</label>
            <select class="form-select">
              <option selected>7 days</option>
              <option>14 days</option>
              <option>30 days</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Storage Usage</label>
            <div style="font-size: 13px; color: var(--text-primary); font-weight: 600;">14.2 MB / 500 MB</div>
          </div>
          <button class="btn btn-primary" style="margin-top: 10px;">Save retention settings</button>
        </div>
      `
      }
    `;

    // Handlers
    container.querySelectorAll(".logs-subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeSubtab = btn.id.replace("subtab-", "");
        renderContent();
      });
    });

    container.querySelectorAll(".window-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        activeWindow = pill.getAttribute("data-window");
        renderContent();
      });
    });

    container.querySelectorAll(".cycle-toggle-header").forEach((header) => {
      header.addEventListener("click", () => {
        const cIdx = parseInt(header.getAttribute("data-cycle-index"));
        cycles[cIdx].expanded = !cycles[cIdx].expanded;
        renderContent();
      });
    });

    const toggleInfo = container.querySelector("#toggle-info");
    if (toggleInfo) {
      toggleInfo.addEventListener("click", () => {
        activeLevels.info = !activeLevels.info;
        renderContent();
      });
    }

    const toggleWarn = container.querySelector("#toggle-warning");
    if (toggleWarn) {
      toggleWarn.addEventListener("click", () => {
        activeLevels.warning = !activeLevels.warning;
        renderContent();
      });
    }

    const toggleErr = container.querySelector("#toggle-error");
    if (toggleErr) {
      toggleErr.addEventListener("click", () => {
        activeLevels.error = !activeLevels.error;
        renderContent();
      });
    }

    const btnPause = container.querySelector("#btn-pause-logs");
    if (btnPause) {
      btnPause.addEventListener("click", () => {
        isPaused = !isPaused;
        renderContent();
      });
    }

    const btnClear = container.querySelector("#btn-clear-logs");
    if (btnClear) {
      btnClear.addEventListener("click", () => {
        setState({ detailedLogs: [] });
      });
    }
  }

  renderContent();
  return container;
}
