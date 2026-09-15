export function renderRoomsTab(state, setState, onAddRoom, onConfigureRoom, onRoomSettings) {
  const container = document.createElement("div");
  container.className = "tab-content rooms-tab";

  const totalRooms = state.rooms.length;

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Rooms</h1>
        <div class="page-subtitle">${totalRooms} rooms · click "Configure sensors & vents" to set up a room</div>
      </div>
      <button class="btn btn-primary" id="btn-add-room">
        + Add room
      </button>
    </div>

    <div class="rooms-grid">
      ${state.rooms
        .map(
          (room) => `
        <div class="room-card" id="room-card-${room.id}">
          <div>
            <div class="room-card-header">
              <div>
                <h2 class="room-title">${room.name}</h2>
                <div class="room-zone-sub">${room.zoneName} (${room.entityId})</div>
              </div>
              <button class="btn btn-danger-outline btn-delete-room" data-room-id="${room.id}">
                Delete
              </button>
            </div>

            <div class="room-status-line">
              <div class="status-row-main">
                ${
                  room.statusTarget
                    ? `
                  <div class="status-active-text">
                    <span class="target-pill">${room.statusTarget}</span>
                    <span>${room.statusVia}</span>
                  </div>
                  ${
                    room.hasClearPresence
                      ? `<button class="clear-presence-btn" data-room-id="${room.id}">Clear presence</button>`
                      : ""
                  }
                `
                    : `
                  <div class="status-not-active">${room.statusText || "Not active"}</div>
                `
                }
              </div>
              ${
                room.nextSched
                  ? `<div class="status-next-sched">${room.nextSched}</div>`
                  : ""
              }
            </div>

            <div class="room-inner-stats">
              <div class="stat-item temp-stat-row">
                <span class="stat-item-label">
                  <span class="hover-temp-icon">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>
                  </span>
                  Temp
                </span>
                <span class="stat-item-value">${room.temp}</span>
              </div>
              ${
                room.presence !== undefined && room.presence !== null
                  ? `
                <div class="stat-item">
                  <span class="stat-item-label">Presence</span>
                  <span class="stat-item-value">${room.presence}</span>
                </div>
              `
                  : ""
              }
              ${
                room.vents !== undefined && room.vents !== null
                  ? `
                <div class="stat-item">
                  <span class="stat-item-label">Vents</span>
                  <span class="vent-status-badge ${room.vents === "Open" ? "vent-open" : ""}">${room.vents}</span>
                </div>
              `
                  : ""
              }
            </div>

            <div class="room-badges-container">
              ${
                room.sensorsCount !== undefined
                  ? `<span class="badge badge-green">${room.sensorsCount} SENSOR</span>`
                  : ""
              }
              ${
                room.ventsCount !== undefined
                  ? `<span class="badge badge-blue">${room.ventsCount} VENT${room.ventsCount !== 1 ? "S" : ""}</span>`
                  : ""
              }
              ${
                room.presenceCount !== undefined
                  ? `<span class="badge badge-green">${room.presenceCount} PRESENCE</span>`
                  : ""
              }
              ${
                room.offset
                  ? `<span class="badge badge-orange">${room.offset}</span>`
                  : ""
              }
            </div>

            ${
              room.noVentsWarning
                ? `<div class="no-vents-alert">No vents — configure below.</div>`
                : ""
            }
          </div>

          <div class="room-card-actions">
            <button class="btn-config btn-configure-room" data-room-id="${room.id}">
              Configure sensors & vents →
            </button>
            <button class="btn-room-settings btn-room-settings-action" data-room-id="${room.id}">
              Settings
            </button>
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  // Handlers
  container.querySelector("#btn-add-room").addEventListener("click", () => {
    onAddRoom();
  });

  container.querySelectorAll(".btn-delete-room").forEach((btn) => {
    btn.addEventListener("click", () => {
      const roomId = btn.getAttribute("data-room-id");
      if (confirm("Are you sure you want to delete this room?")) {
        const updated = state.rooms.filter((r) => r.id !== roomId);
        setState({ rooms: updated });
      }
    });
  });

  container.querySelectorAll(".clear-presence-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const roomId = btn.getAttribute("data-room-id");
      const updated = state.rooms.map((r) => {
        if (r.id === roomId) {
          return {
            ...r,
            statusTarget: null,
            statusVia: null,
            hasClearPresence: false,
            statusText: "Not active",
            presence: "Unoccupied",
            vents: r.vents === "Open" ? "Closed" : r.vents
          };
        }
        return r;
      });
      setState({ rooms: updated });
    });
  });

  container.querySelectorAll(".btn-configure-room").forEach((btn) => {
    btn.addEventListener("click", () => {
      const roomId = btn.getAttribute("data-room-id");
      onConfigureRoom(roomId);
    });
  });

  container.querySelectorAll(".btn-room-settings-action").forEach((btn) => {
    btn.addEventListener("click", () => {
      const roomId = btn.getAttribute("data-room-id");
      onRoomSettings(roomId);
    });
  });

  return container;
}
