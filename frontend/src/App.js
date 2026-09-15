import { initialData } from "./data/mockData.js";
import { renderNavbar } from "./components/Navbar.js";
import { renderPredictionsTab } from "./components/PredictionsTab.js?v=5";
import { renderDashboardTab } from "./components/DashboardTab.js";
import { renderMetricsTab } from "./components/MetricsTab.js";
import { renderThermostatsTab } from "./components/ThermostatsTab.js";
import { openAddRoomModal, openSettingsModal } from "./components/Modals.js";
import { renderLandingPage } from "./components/LandingPage.js";

export class App {
  constructor(rootElement) {
    this.root = rootElement;
    this.state = {
      ...initialData,
      activeTab: "dashboard",
      selectedThermostat: "all",
      predictionSource: "simulation",
      systemMode: "automatic",
      manualSettings: { temp: 70, mode: "COOLING", airflow: "Auto" },
      showLanding: true,
    };
    this._isTransitioning = false;
  }

  setState(partialState) {
    const prevTab = this.state.activeTab;
    this.state = { ...this.state, ...partialState };

    // If tab changed, animate the transition
    if (partialState.activeTab && partialState.activeTab !== prevTab) {
      this._transitionToTab(partialState.activeTab);
    } else {
      this.render();
    }
  }

  init() {
    if (this.state.showLanding) {
      this._showLanding();
    } else {
      this.render();
    }
  }

  _showLanding() {
    this.root.innerHTML = "";
    const landing = renderLandingPage(() => {
      this.state.showLanding = false;
      this._renderMainApp();
    });
    this.root.appendChild(landing);
  }

  _renderMainApp() {
    this.root.innerHTML = "";

    // Navbar
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

    // Main Container
    const mainContainer = document.createElement("main");
    mainContainer.className = "main-container";
    mainContainer.id = "main-content";

    // Tab Content
    const tabContent = this._getTabContent();
    mainContainer.appendChild(tabContent);
    this.root.appendChild(mainContainer);

    // Entrance animation for main app
    if (typeof gsap !== "undefined") {
      gsap.from(navbar, { y: -60, opacity: 0, duration: 0.5, ease: "power2.out" });
      gsap.from(mainContainer, { y: 30, opacity: 0, duration: 0.6, ease: "power2.out", delay: 0.15 });
    }
  }

  _getTabContent() {
    switch (this.state.activeTab) {
      case "predictions":
        return renderPredictionsTab(this.state);
      case "dashboard":
        return renderDashboardTab(this.state, (patch) => this.setState(patch));
      case "metrics":
        return renderMetricsTab(
          this.state,
          this.state.selectedThermostat,
          (newThermostat) => {
            this.setState({ selectedThermostat: newThermostat });
          }
        );
      case "thermostats":
        return renderThermostatsTab(this.state, (patch) => this.setState(patch));
      default:
        return renderDashboardTab(this.state, (patch) => this.setState(patch));
    }
  }

  _transitionToTab(newTab) {
    if (this._isTransitioning) return;

    const mainContent = document.getElementById("main-content");
    if (!mainContent || typeof gsap === "undefined") {
      // Fallback: no animation
      this.render();
      return;
    }

    this._isTransitioning = true;

    // Animate out the old content
    gsap.to(mainContent, {
      opacity: 0,
      y: -15,
      duration: 0.25,
      ease: "power2.in",
      onComplete: () => {
        // Replace content
        mainContent.innerHTML = "";
        const newContent = this._getTabContent();
        mainContent.appendChild(newContent);

        // Update navbar active state
        document.querySelectorAll(".nav-tab-btn").forEach(btn => {
          btn.classList.toggle("active", btn.dataset.tab === newTab);
        });

        // Animate in the new content
        gsap.fromTo(mainContent,
          { opacity: 0, y: 15 },
          {
            opacity: 1,
            y: 0,
            duration: 0.35,
            ease: "power2.out",
            onComplete: () => {
              this._isTransitioning = false;
            }
          }
        );
      }
    });
  }

  render() {
    if (this.state.showLanding) {
      this._showLanding();
      return;
    }
    this._renderMainApp();
  }
}
