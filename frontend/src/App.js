import { initialData } from "./data/mockData.js";
import { renderNavbar } from "./components/Navbar.js";
import { renderDashboardTab } from "./components/DashboardTab.js";
import { renderRoomsTab } from "./components/RoomsTab.js";
import { renderSchedulesTab } from "./components/SchedulesTab.js";
import { renderMetricsTab } from "./components/MetricsTab.js";
import { renderThermostatsTab } from "./components/ThermostatsTab.js";
import { renderLogsTab } from "./components/LogsTab.js";
import { openAddRoomModal, openSettingsModal } from "./components/Modals.js";

export class App {
  constructor(rootElement) {
    this.root = rootElement;
    this.state = {
      ...initialData,
      activeTab: "dashboard",
      selectedThermostat: "all"
    };
  }

  setState(partialState) {
    this.state = { ...this.state, ...partialState };
    this.render();
  }

  init() {
    this.render();
  }

  render() {
    this.root.innerHTML = "";

    // 1. Navbar
    const navbar = renderNavbar(
      this.state.activeTab,
      (tabId) => {
        this.setState({ activeTab: tabId });
      },
      () => {
        openSettingsModal(this.state, () => {});
      }
    );
    this.root.appendChild(navbar);

    // 2. Main Container
    const mainContainer = document.createElement("main");
    mainContainer.className = "main-container";

    // 3. Tab Contents
    switch (this.state.activeTab) {
      case "dashboard":
        mainContainer.appendChild(
          renderDashboardTab(this.state, (patch) => this.setState(patch))
        );
        break;

      case "rooms":
        mainContainer.appendChild(
          renderRoomsTab(
            this.state,
            (patch) => this.setState(patch),
            () => {
              openAddRoomModal(this.state.zones, (newRoom) => {
                this.setState({
                  rooms: [...this.state.rooms, newRoom]
                });
              });
            },
            (roomId) => {
              alert(`Configuring sensors and smart vents for room: ${roomId}`);
            },
            (roomId) => {
              alert(`Opening settings for room: ${roomId}`);
            }
          )
        );
        break;

      case "schedules":
        mainContainer.appendChild(
          renderSchedulesTab(
            this.state,
            (patch) => this.setState(patch),
            (schedId) => {
              const days = prompt("Enter days (e.g. MTWTS, FS, Sun):", "MTWTS");
              if (!days) return;
              const start = prompt("Enter start time (e.g. 21:00:00):", "22:00:00");
              const end = prompt("Enter end time (e.g. 07:00:00):", "06:30:00");
              const target = prompt("Enter target temp (e.g. 68.0°F):", "68.0°F");

              const updated = this.state.schedules.map((s) => {
                if (s.id === schedId) {
                  return {
                    ...s,
                    expanded: true,
                    blocks: [
                      ...s.blocks,
                      {
                        id: "b_" + Date.now(),
                        days,
                        start,
                        end,
                        target
                      }
                    ]
                  };
                }
                return s;
              });
              this.setState({ schedules: updated });
            },
            (schedId, blockId) => {
              alert(`Editing schedule block ${blockId} for ${schedId}`);
            }
          )
        );
        break;

      case "metrics":
        mainContainer.appendChild(
          renderMetricsTab(
            this.state,
            this.state.selectedThermostat,
            (newThermostat) => {
              this.setState({ selectedThermostat: newThermostat });
            }
          )
        );
        break;

      case "thermostats":
        mainContainer.appendChild(renderThermostatsTab(this.state));
        break;

      case "logs":
        mainContainer.appendChild(
          renderLogsTab(this.state, (patch) => this.setState(patch))
        );
        break;

      default:
        mainContainer.appendChild(
          renderDashboardTab(this.state, (patch) => this.setState(patch))
        );
    }

    this.root.appendChild(mainContainer);
  }
}
