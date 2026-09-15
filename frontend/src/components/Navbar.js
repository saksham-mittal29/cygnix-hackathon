export function renderNavbar(activeTab, onTabChange, onOpenSettings) {
  const tabs = [
    { id: "predictions", label: "Predictions" },
    { id: "dashboard", label: "Dashboard" },
    { id: "thermostats", label: "Thermostats" },
    { id: "metrics", label: "Metrics" }
  ];

  const nav = document.createElement("nav");
  nav.className = "navbar";

  nav.innerHTML = `
    <div class="nav-brand" id="brand-logo" title="Cygnix AI Climate Control">
      <div class="nav-logo-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="5" stroke="#2563eb" stroke-width="2" stroke-dasharray="16 16"/>
          <path d="M3 15h18" stroke="#1e293b" stroke-width="2" stroke-linecap="round"/>
          <path d="M7 19h10" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <span class="brand-name">Cygnix</span>
    </div>

    <div class="nav-tabs">
      ${tabs
        .map(
          (tab) => `
        <button 
          class="nav-tab-btn ${activeTab === tab.id ? "active" : ""}" 
          data-tab="${tab.id}"
          id="tab-${tab.id}"
        >
          ${tab.label}
        </button>
      `
        )
        .join("")}
    </div>

    <div class="nav-actions">
      <button class="settings-btn" id="btn-settings" title="Settings">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      </button>
    </div>
  `;

  // Attach event handlers
  nav.querySelectorAll(".nav-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      onTabChange(tabId);
    });
  });

  nav.querySelector("#btn-settings").addEventListener("click", () => {
    onOpenSettings();
  });

  nav.querySelector("#brand-logo").addEventListener("click", () => {
    onTabChange("dashboard");
  });

  return nav;
}
