export function renderModal({ title, bodyHtml, onSave, onClose }) {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";

  backdrop.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">${title}</h2>
        <button class="modal-close" id="modal-close-btn">&times;</button>
      </div>
      <div class="modal-body">
        ${bodyHtml}
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" id="modal-cancel-btn">Cancel</button>
        <button class="btn btn-primary" id="modal-save-btn">Save changes</button>
      </div>
    </div>
  `;

  const cleanup = () => {
    backdrop.remove();
  };

  backdrop.querySelector("#modal-close-btn").addEventListener("click", cleanup);
  backdrop.querySelector("#modal-cancel-btn").addEventListener("click", cleanup);

  backdrop.querySelector("#modal-save-btn").addEventListener("click", () => {
    if (onSave(backdrop)) {
      cleanup();
    }
  });

  // Close on outside click
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) {
      cleanup();
    }
  });

  document.body.appendChild(backdrop);
}

export function openAddRoomModal(zones, onRoomAdded) {
  renderModal({
    title: "Add New Room",
    bodyHtml: `
      <div class="form-group">
        <label class="form-label">Room Name</label>
        <input type="text" class="form-input" id="input-room-name" placeholder="e.g. Guest Bedroom" />
      </div>
      <div class="form-group">
        <label class="form-label">Zone</label>
        <select class="form-select" id="input-room-zone">
          ${zones.map((z) => `<option value="${z.id}">${z.name} (${z.entityId})</option>`).join("")}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Initial Temperature (°F)</label>
        <input type="text" class="form-input" id="input-room-temp" value="70.0°F" />
      </div>
      <div class="form-group">
        <label class="form-label">Sensors Count</label>
        <input type="number" class="form-input" id="input-room-sensors" value="1" min="0" />
      </div>
      <div class="form-group">
        <label class="form-label">Vents Count</label>
        <input type="number" class="form-input" id="input-room-vents" value="1" min="0" />
      </div>
    `,
    onSave: (modalEl) => {
      const name = modalEl.querySelector("#input-room-name").value.trim();
      const zoneId = modalEl.querySelector("#input-room-zone").value;
      const temp = modalEl.querySelector("#input-room-temp").value.trim() || "70.0°F";
      const sensors = parseInt(modalEl.querySelector("#input-room-sensors").value) || 1;
      const vents = parseInt(modalEl.querySelector("#input-room-vents").value) || 0;

      if (!name) {
        alert("Please enter a room name.");
        return false;
      }

      const zone = zones.find((z) => z.id === zoneId);

      onRoomAdded({
        id: "room-" + Date.now(),
        name: name,
        zoneName: zone ? zone.name : "Upstairs",
        entityId: zone ? zone.entityId : "climate.upstairs_2",
        statusText: "Not active",
        temp: temp.includes("°F") ? temp : `${temp}°F`,
        presence: "Unoccupied",
        vents: vents > 0 ? "Closed" : null,
        sensorsCount: sensors,
        ventsCount: vents,
        presenceCount: 1,
        noVentsWarning: vents === 0
      });

      return true;
    }
  });
}

export function openSettingsModal(state, onSettingsSaved) {
  renderModal({
    title: "System Settings",
    bodyHtml: `
      <div class="form-group">
        <label class="form-label">HVAC Cycle Deadband (°F)</label>
        <input type="number" class="form-input" value="1.0" step="0.1" />
      </div>
      <div class="form-group">
        <label class="form-label">Presence Timeout (Minutes)</label>
        <input type="number" class="form-input" value="45" />
      </div>
      <div class="form-group">
        <label class="form-label">Telemetry Polling Interval</label>
        <select class="form-select">
          <option>10 seconds (Recommended)</option>
          <option>30 seconds</option>
          <option>60 seconds</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Weather Provider</label>
        <input type="text" class="form-input" value="National Weather Service (OpenMeteo)" />
      </div>
    `,
    onSave: () => {
      alert("Settings saved successfully!");
      return true;
    }
  });
}
