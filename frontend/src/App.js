import { initialData } from "./data/mockData.js";
import { renderNavbar } from "./components/Navbar.js";
import { renderPredictionsTab } from "./components/PredictionsTab.js?v=3";
import { renderDashboardTab } from "./components/DashboardTab.js";
import { renderMetricsTab } from "./components/MetricsTab.js";
import { renderThermostatsTab } from "./components/ThermostatsTab.js";
import { openAddRoomModal, openSettingsModal } from "./components/Modals.js";

export class App {
  constructor(rootElement) {
    this.root = rootElement;
    this.state = {
      ...initialData,
      activeTab: "dashboard",
      selectedThermostat: "all",
      predictionSource: "simulation", // "simulation" | "live"
      systemMode: "automatic", // "automatic" | "manual_pending" | "manual"
      manualSettings: { temp: 70, mode: "COOLING", airflow: "Auto" }
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
      case "predictions":
        mainContainer.appendChild(
          renderPredictionsTab(this.state)
        );
        break;

      case "dashboard":
        mainContainer.appendChild(
          renderDashboardTab(this.state, (patch) => this.setState(patch))
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
        mainContainer.appendChild(renderThermostatsTab(this.state, (patch) => this.setState(patch)));
        break;

      default:
        mainContainer.appendChild(
          renderDashboardTab(this.state, (patch) => this.setState(patch))
        );
    }

    this.root.appendChild(mainContainer);
  }
}
