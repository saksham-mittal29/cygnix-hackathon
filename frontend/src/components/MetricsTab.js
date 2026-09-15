export function renderMetricsTab(state, selectedThermostat = "upstairs", onFilterChange) {
  const container = document.createElement("div");
  container.className = "tab-content metrics-tab";

  const data = state.metrics[selectedThermostat] || state.metrics.upstairs;

  // Heatmap helper matrix (7 rows x 24 cols)
  const heatmapData = [
    // Mon
    [0.1, 0.4, 0.4, 0.3, 0.2, 0.6, 0.1, 0.1, 0.2, 0.1, 0.1, 0.1, 0.2, 0.2, 0.4, 0.2, 0.1, 0.2, 0.3, 0.3, 0.4, 0.2, 0.1, 0.1],
    // Tue
    [0.1, 0.3, 0.3, 0.2, 0.2, 0.5, 0.1, 0.2, 0.3, 0.1, 0.2, 0.1, 0.1, 0.2, 0.3, 0.2, 0.4, 0.5, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
    // Wed
    [0.1, 0.3, 0.3, 0.2, 0.6, 0.3, 0.4, 0.2, 0.1, 0.1, 0.2, 0.1, 0.3, 0.4, 0.6, 0.4, 0.5, 0.6, 0.5, 0.6, 0.5, 0.4, 0.2, 0.1],
    // Thu
    [0.1, 0.4, 0.3, 0.2, 0.2, 0.5, 0.5, 0.1, 0.1, 0.1, 0.3, 0.3, 0.4, 0.5, 0.6, 0.5, 0.5, 0.6, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1],
    // Fri
    [0.1, 0.4, 0.3, 0.3, 0.3, 0.4, 0.3, 0.4, 0.2, 0.2, 0.2, 0.3, 0.4, 0.5, 0.5, 0.6, 0.6, 0.6, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
    // Sat
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4, 0.2, 0.1, 0.1, 0.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.1],
    // Sun
    [0.1, 0.3, 0.4, 0.4, 0.4, 0.4, 0.4, 0.3, 0.1, 0.1, 0.1, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.4, 0.5, 0.3, 0.2, 0.1]
  ];

  const daysLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Metrics</h1>
        <div class="page-subtitle">Heating & cooling analytics for the home and individual thermostats. Charts arrive in Phase 4 — this scaffold wires the data feed and filters.</div>
      </div>
    </div>

    <!-- Filter Card -->
    <div class="metrics-filter-card">
      <div class="metrics-filters-row">
        <div class="filter-group">
          <label>Thermostat</label>
          <select class="metrics-select" id="select-thermostat">
            <option value="upstairs" ${selectedThermostat === "upstairs" ? "selected" : ""}>Upstairs</option>
            <option value="all" ${selectedThermostat === "all" ? "selected" : ""}>All thermostats (home)</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Start</label>
          <input type="text" class="metrics-date-input" id="input-start-date" value="05/24/2026" />
        </div>

        <div class="filter-group">
          <label>End</label>
          <input type="text" class="metrics-date-input" id="input-end-date" value="05/30/2026" />
        </div>

        <div class="filter-actions">
          <button class="btn btn-outline" id="btn-last-7-days">Last 7 days</button>
          <button class="btn btn-outline" id="btn-export-csv">Export CSV</button>
        </div>
      </div>

      <div class="metrics-subtext" id="metrics-showing-text">
        ${data.showingText}
      </div>
    </div>

    <!-- KPI Cards Row -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">Heating time</span>
        <span class="kpi-value">${data.heatingTime}</span>
        ${data.heatingSub ? `<span class="kpi-sub">${data.heatingSub}</span>` : ""}
      </div>

      <div class="kpi-card">
        <span class="kpi-label">Cooling time</span>
        <span class="kpi-value">${data.coolingTime}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-label">Duty cycle</span>
        <span class="kpi-value">${data.dutyCycle}</span>
      </div>

      <div class="kpi-card">
        <span class="kpi-label">Cycles</span>
        <span class="kpi-value">${data.cycles}</span>
        ${data.cyclesSub ? `<span class="kpi-sub">${data.cyclesSub}</span>` : ""}
      </div>

      <div class="kpi-card">
        <span class="kpi-label">Avg outside temp</span>
        <span class="kpi-value">${data.avgOutsideTemp}</span>
        ${data.tempSub ? `<span class="kpi-sub">${data.tempSub}</span>` : ""}
      </div>
    </div>

    <!-- ROW 1 OF CHARTS -->
    <div class="charts-grid">
      <!-- 1. Heating & cooling hours per day -->
      <div class="chart-card">
        <h3 class="chart-title">Heating & cooling hours per day</h3>
        <div class="chart-subtitle">Stacked bars — total HVAC run-time bucketed by local date.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">16h</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">12h</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">8h</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">4h</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0h</text>

            <!-- 05-24 -->
            <rect x="55" y="165" width="34" height="15" fill="#f97316"/>
            <rect x="55" y="93" width="34" height="72" fill="#3b82f6"/>
            <text x="72" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-24</text>

            <!-- 05-25 -->
            <rect x="110" y="166" width="34" height="14" fill="#f97316"/>
            <rect x="110" y="87" width="34" height="79" fill="#3b82f6"/>
            <text x="127" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-25</text>

            <!-- 05-26 -->
            <rect x="165" y="164" width="34" height="16" fill="#f97316"/>
            <rect x="165" y="70" width="34" height="94" fill="#3b82f6"/>
            <text x="182" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-26</text>

            <!-- 05-27 -->
            <rect x="220" y="172" width="34" height="8" fill="#f97316"/>
            <rect x="220" y="49" width="34" height="123" fill="#3b82f6"/>
            <text x="237" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-27</text>

            <!-- 05-28 -->
            <rect x="275" y="169" width="34" height="11" fill="#f97316"/>
            <rect x="275" y="33" width="34" height="136" fill="#3b82f6"/>
            <text x="292" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-28</text>

            <!-- 05-29 -->
            <rect x="330" y="168" width="34" height="12" fill="#f97316"/>
            <rect x="330" y="51" width="34" height="117" fill="#3b82f6"/>
            <text x="347" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-29</text>

            <!-- 05-30 -->
            <rect x="385" y="174" width="34" height="6" fill="#f97316"/>
            <rect x="385" y="126" width="34" height="48" fill="#3b82f6"/>
            <text x="402" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-30</text>
          </svg>

          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #3b82f6;"></span>
              <span>Cooling</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #f97316;"></span>
              <span>Heating</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Cycles per day -->
      <div class="chart-card">
        <h3 class="chart-title">Cycles per day</h3>
        <div class="chart-subtitle">How many distinct heating/cooling cycles ran each day.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">60</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">45</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">30</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">15</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0</text>

            <rect x="55" y="79" width="34" height="101" fill="#3b82f6"/>
            <text x="72" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-24</text>

            <rect x="110" y="60" width="34" height="120" fill="#3b82f6"/>
            <text x="127" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-25</text>

            <rect x="165" y="60" width="34" height="120" fill="#3b82f6"/>
            <text x="182" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-26</text>

            <rect x="220" y="76" width="34" height="104" fill="#3b82f6"/>
            <text x="237" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-27</text>

            <rect x="275" y="76" width="34" height="104" fill="#3b82f6"/>
            <text x="292" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-28</text>

            <rect x="330" y="65" width="34" height="115" fill="#3b82f6"/>
            <text x="347" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-29</text>

            <rect x="385" y="111" width="34" height="69" fill="#3b82f6"/>
            <text x="402" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-30</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- ROW 2 OF CHARTS -->
    <div class="charts-grid">
      <!-- 3. Average cycle duration (Smooth teal curve) -->
      <div class="chart-card">
        <h3 class="chart-title">Average cycle duration</h3>
        <div class="chart-subtitle">Mean cycle length per day, in minutes.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">24m</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">18m</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">12m</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">6m</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0m</text>

            <!-- Curve path in teal #0d9488 -->
            <path d="M 55 90 C 80 100, 110 100, 140 85 C 180 65, 230 35, 275 32 C 320 30, 360 70, 420 105" 
                  fill="none" stroke="#0d9488" stroke-width="2.5" stroke-linecap="round"/>

            <text x="55" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-24</text>
            <text x="127" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-25</text>
            <text x="182" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-26</text>
            <text x="237" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-27</text>
            <text x="292" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-28</text>
            <text x="420" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-30</text>
          </svg>
        </div>
      </div>

      <!-- 4. Duty cycle (Smooth purple curve) -->
      <div class="chart-card">
        <h3 class="chart-title">Duty cycle</h3>
        <div class="chart-subtitle">HVAC run-time as a percentage of each day.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">80%</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">60%</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">40%</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">20%</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0%</text>

            <!-- Curve path in purple #8b5cf6 -->
            <path d="M 55 110 C 90 105, 150 90, 200 75 C 240 65, 275 60, 305 60 C 350 60, 380 95, 420 138" 
                  fill="none" stroke="#8b5cf6" stroke-width="2.5" stroke-linecap="round"/>

            <text x="55" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-24</text>
            <text x="127" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-25</text>
            <text x="182" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-26</text>
            <text x="237" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-27</text>
            <text x="292" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-28</text>
            <text x="420" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-30</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- ROW 3 OF CHARTS -->
    <div class="charts-grid">
      <!-- 5. Time to target -->
      <div class="chart-card">
        <h3 class="chart-title">Time to target</h3>
        <div class="chart-subtitle">Average minutes from cycle start to first room reaching target.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">8m</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">6m</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">4m</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">2m</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0m</text>

            <path d="M 55 45 C 90 48, 120 48, 150 32 C 180 20, 220 20, 260 26 C 300 30, 360 30, 420 52" 
                  fill="none" stroke="#0d9488" stroke-width="2.5" stroke-linecap="round"/>

            <text x="55" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-24</text>
            <text x="127" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-25</text>
            <text x="182" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-26</text>
            <text x="237" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-27</text>
            <text x="292" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-28</text>
            <text x="420" y="195" font-size="11" fill="#64748b" text-anchor="middle">05-30</text>
          </svg>
        </div>
      </div>

      <!-- 6. Cycle completion rate (Donut) -->
      <div class="chart-card">
        <h3 class="chart-title">Cycle completion rate</h3>
        <div class="chart-subtitle">275 cycles — 90.2% completed</div>
        
        <div class="chart-body">
          <svg viewBox="0 0 200 200" width="170" height="170">
            <!-- Completed (Green) 90.2% -->
            <circle cx="100" cy="100" r="70" fill="none" stroke="#10b981" stroke-width="26"
              stroke-dasharray="396 440" stroke-dashoffset="0" transform="rotate(-90 100 100)" />
            <!-- Aborted (Gray) ~7.0% -->
            <circle cx="100" cy="100" r="70" fill="none" stroke="#64748b" stroke-width="26"
              stroke-dasharray="31 440" stroke-dashoffset="-396" transform="rotate(-90 100 100)" />
            <!-- Timeout (Red) ~2.8% -->
            <circle cx="100" cy="100" r="70" fill="none" stroke="#ef4444" stroke-width="26"
              stroke-dasharray="13 440" stroke-dashoffset="-427" transform="rotate(-90 100 100)" />
          </svg>

          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #64748b;"></span>
              <span>Aborted</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #10b981;"></span>
              <span>Completed</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #ef4444;"></span>
              <span>Timeout</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ROW 4 OF CHARTS -->
    <div class="charts-grid">
      <!-- 7. Source breakdown (Donut) -->
      <div class="chart-card">
        <h3 class="chart-title">Source breakdown</h3>
        <div class="chart-subtitle">Which trigger started each cycle (counts cycles where each source was active for at least one room).</div>
        
        <div class="chart-body">
          <svg viewBox="0 0 200 200" width="170" height="170">
            <circle cx="100" cy="100" r="70" fill="none" stroke="#10b981" stroke-width="26"
              stroke-dasharray="220 440" stroke-dashoffset="0" transform="rotate(0 100 100)" />
            <circle cx="100" cy="100" r="70" fill="none" stroke="#2563eb" stroke-width="26"
              stroke-dasharray="220 440" stroke-dashoffset="-220" transform="rotate(0 100 100)" />
          </svg>

          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #10b981;"></span>
              <span>Presence</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #2563eb;"></span>
              <span>Schedule</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 8. Cycles vs outside temperature (Scatter Plot) -->
      <div class="chart-card">
        <h3 class="chart-title">Cycles vs outside temperature</h3>
        <div class="chart-subtitle">Each dot = one cycle. X = outside °F at start, Y = duration (min).</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">80m</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">60m</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">40m</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">20m</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0m</text>

            <!-- X Axis ticks: 66°F, 72°F, 78°F, 84°F, 90°F -->
            <text x="50" y="195" font-size="11" fill="#64748b" text-anchor="middle">66°F</text>
            <text x="140" y="195" font-size="11" fill="#64748b" text-anchor="middle">72°F</text>
            <text x="230" y="195" font-size="11" fill="#64748b" text-anchor="middle">78°F</text>
            <text x="320" y="195" font-size="11" fill="#64748b" text-anchor="middle">84°F</text>
            <text x="410" y="195" font-size="11" fill="#64748b" text-anchor="middle">90°F</text>

            <!-- Scatter Dots (Cooling in Blue, Heating in Orange) -->
            <!-- Clustered around (70-76, 10-35m) -->
            <circle cx="120" cy="155" r="3.5" fill="#3b82f6"/>
            <circle cx="125" cy="150" r="3.5" fill="#3b82f6"/>
            <circle cx="130" cy="145" r="3.5" fill="#3b82f6"/>
            <circle cx="135" cy="160" r="3.5" fill="#3b82f6"/>
            <circle cx="140" cy="130" r="3.5" fill="#3b82f6"/>
            <circle cx="145" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="150" cy="120" r="3.5" fill="#3b82f6"/>
            <circle cx="155" cy="150" r="3.5" fill="#3b82f6"/>
            <circle cx="160" cy="135" r="3.5" fill="#3b82f6"/>
            <circle cx="165" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="170" cy="125" r="3.5" fill="#3b82f6"/>
            <circle cx="175" cy="135" r="3.5" fill="#3b82f6"/>
            <circle cx="180" cy="150" r="3.5" fill="#3b82f6"/>
            <circle cx="185" cy="130" r="3.5" fill="#3b82f6"/>
            <circle cx="190" cy="145" r="3.5" fill="#3b82f6"/>
            <circle cx="195" cy="160" r="3.5" fill="#3b82f6"/>
            <circle cx="200" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="205" cy="130" r="3.5" fill="#3b82f6"/>
            <circle cx="210" cy="150" r="3.5" fill="#3b82f6"/>
            <circle cx="225" cy="135" r="3.5" fill="#3b82f6"/>
            <circle cx="235" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="240" cy="130" r="3.5" fill="#3b82f6"/>
            <circle cx="250" cy="150" r="3.5" fill="#3b82f6"/>
            <circle cx="260" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="270" cy="145" r="3.5" fill="#3b82f6"/>

            <!-- Higher durations / warm temps -->
            <circle cx="140" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="140" cy="100" r="3.5" fill="#3b82f6"/>
            <circle cx="200" cy="100" r="3.5" fill="#3b82f6"/>
            <circle cx="230" cy="95" r="3.5" fill="#3b82f6"/>
            <circle cx="250" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="255" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="265" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="260" cy="90" r="3.5" fill="#3b82f6"/>
            <circle cx="275" cy="80" r="3.5" fill="#3b82f6"/>
            <circle cx="295" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="300" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="320" cy="120" r="3.5" fill="#3b82f6"/>
            <circle cx="320" cy="140" r="3.5" fill="#3b82f6"/>
            <circle cx="330" cy="100" r="3.5" fill="#3b82f6"/>
            <circle cx="340" cy="60" r="3.5" fill="#3b82f6"/>
            <circle cx="395" cy="60" r="3.5" fill="#3b82f6"/>

            <!-- Heating Dots in Orange -->
            <circle cx="150" cy="165" r="3.5" fill="#f97316"/>
            <circle cx="175" cy="165" r="3.5" fill="#f97316"/>
            <circle cx="235" cy="168" r="3.5" fill="#f97316"/>
          </svg>

          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color-dot" style="background-color: #3b82f6;"></span>
              <span>Cooling</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-dot" style="background-color: #f97316;"></span>
              <span>Heating</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ROW 5 OF CHARTS -->
    <div class="charts-grid">
      <!-- 9. Degree-minutes (No data) -->
      <div class="chart-card">
        <h3 class="chart-title">Degree-minutes</h3>
        <div class="chart-subtitle">∫ |setpoint – thermostat temperature| dt — a single load proxy. Lower = closer to setpoint.</div>
        
        <div class="chart-body" style="color: var(--text-secondary); font-size: 13px;">
          No data for this range yet.
        </div>
      </div>

      <!-- 10. Overshoot histogram -->
      <div class="chart-card">
        <h3 class="chart-title">Overshoot histogram</h3>
        <div class="chart-subtitle">421/533 room-cycles overshoot — max 1.6°F, avg 0.5°F</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <line x1="45" y1="20" x2="430" y2="20" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="24" font-size="11" fill="#64748b" text-anchor="end">600</text>
            
            <line x1="45" y1="60" x2="430" y2="60" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="64" font-size="11" fill="#64748b" text-anchor="end">450</text>
            
            <line x1="45" y1="100" x2="430" y2="100" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="104" font-size="11" fill="#64748b" text-anchor="end">300</text>
            
            <line x1="45" y1="140" x2="430" y2="140" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="35" y="144" font-size="11" fill="#64748b" text-anchor="end">150</text>
            
            <line x1="45" y1="180" x2="430" y2="180" stroke="#cbd5e1" stroke-width="1"/>
            <text x="35" y="184" font-size="11" fill="#64748b" text-anchor="end">0</text>

            <!-- Bars: 0-1°F (height ~120px = 440), 1-2°F (height ~24px = 90) -->
            <rect x="55" y="60" width="50" height="120" fill="#ef4444"/>
            <text x="80" y="195" font-size="11" fill="#64748b" text-anchor="middle">0–1°F</text>

            <rect x="115" y="156" width="50" height="24" fill="#ef4444"/>
            <text x="140" y="195" font-size="11" fill="#64748b" text-anchor="middle">1–2°F</text>

            <text x="200" y="195" font-size="11" fill="#64748b" text-anchor="middle">2–3°F</text>
            <text x="260" y="195" font-size="11" fill="#64748b" text-anchor="middle">3–4°F</text>
            <text x="320" y="195" font-size="11" fill="#64748b" text-anchor="middle">4–5°F</text>
            <text x="380" y="195" font-size="11" fill="#64748b" text-anchor="middle">≥5°F</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- ROW 6 OF CHARTS -->
    <div class="charts-grid">
      <!-- 11. Per-room heating vs cooling (Horizontal Stacked Bar) -->
      <div class="chart-card">
        <h3 class="chart-title">Per-room heating vs cooling</h3>
        <div class="chart-subtitle">Total hours each room was actively cooled or heated.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <!-- Vertical Grid Lines: 0h, 15h, 30h, 45h, 60h -->
            <line x1="90" y1="15" x2="90" y2="170" stroke="#cbd5e1" stroke-width="1"/>
            <text x="90" y="185" font-size="11" fill="#64748b" text-anchor="middle">0h</text>

            <line x1="167" y1="15" x2="167" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="167" y="185" font-size="11" fill="#64748b" text-anchor="middle">15h</text>

            <line x1="245" y1="15" x2="245" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="245" y="185" font-size="11" fill="#64748b" text-anchor="middle">30h</text>

            <line x1="322" y1="15" x2="322" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="322" y="185" font-size="11" fill="#64748b" text-anchor="middle">45h</text>

            <line x1="400" y1="15" x2="400" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="400" y="185" font-size="11" fill="#64748b" text-anchor="middle">60h</text>

            <!-- Row 1: Bathroom -->
            <text x="82" y="32" font-size="11" fill="#64748b" text-anchor="end">Bathroom</text>
            <rect x="90" y="20" width="38" height="16" fill="#f97316"/>
            <rect x="128" y="20" width="160" height="16" fill="#3b82f6"/>

            <!-- Row 2: Bedroom -->
            <text x="82" y="58" font-size="11" fill="#64748b" text-anchor="end">Bedroom</text>
            <rect x="90" y="46" width="36" height="16" fill="#f97316"/>
            <rect x="126" y="46" width="262" height="16" fill="#3b82f6"/>

            <!-- Row 3: Gym -->
            <text x="82" y="84" font-size="11" fill="#64748b" text-anchor="end">Gym</text>
            <rect x="90" y="72" width="4" height="16" fill="#3b82f6"/>

            <!-- Row 4: Mom Room -->
            <text x="82" y="110" font-size="11" fill="#64748b" text-anchor="end">Mom Room</text>

            <!-- Row 5: Office -->
            <text x="82" y="136" font-size="11" fill="#64748b" text-anchor="end">Office</text>
            <rect x="90" y="124" width="120" height="16" fill="#3b82f6"/>

            <!-- Row 6: Office 2 -->
            <text x="82" y="162" font-size="11" fill="#64748b" text-anchor="end">Office 2</text>
            <rect x="90" y="150" width="4" height="16" fill="#f97316"/>
            <rect x="94" y="150" width="42" height="16" fill="#3b82f6"/>
          </svg>

          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #3b82f6;"></span>
              <span>Cooling</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: #f97316;"></span>
              <span>Heating</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 12. Room participation rate (Horizontal Sky Blue Bar) -->
      <div class="chart-card">
        <h3 class="chart-title">Room participation rate</h3>
        <div class="chart-subtitle">Percentage of cycles in which each room was an active participant.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <svg viewBox="0 0 450 200" width="100%" height="200" style="overflow: visible;">
            <!-- Vertical Grid Lines: 0%, 25%, 50%, 75%, 100% -->
            <line x1="90" y1="15" x2="90" y2="170" stroke="#cbd5e1" stroke-width="1"/>
            <text x="90" y="185" font-size="11" fill="#64748b" text-anchor="middle">0%</text>

            <line x1="167" y1="15" x2="167" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="167" y="185" font-size="11" fill="#64748b" text-anchor="middle">25%</text>

            <line x1="245" y1="15" x2="245" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="245" y="185" font-size="11" fill="#64748b" text-anchor="middle">50%</text>

            <line x1="322" y1="15" x2="322" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="322" y="185" font-size="11" fill="#64748b" text-anchor="middle">75%</text>

            <line x1="400" y1="15" x2="400" y2="170" stroke="#f1f5f9" stroke-dasharray="3 3" stroke-width="1"/>
            <text x="400" y="185" font-size="11" fill="#64748b" text-anchor="middle">100%</text>

            <!-- Row 1: Bathroom (73%) -->
            <text x="82" y="32" font-size="11" fill="#64748b" text-anchor="end">Bathroom</text>
            <rect x="90" y="20" width="226" height="16" fill="#0ea5e9"/>

            <!-- Row 2: Bedroom (100%) -->
            <text x="82" y="58" font-size="11" fill="#64748b" text-anchor="end">Bedroom</text>
            <rect x="90" y="46" width="310" height="16" fill="#0ea5e9"/>

            <!-- Row 3: Gym (1.5%) -->
            <text x="82" y="84" font-size="11" fill="#64748b" text-anchor="end">Gym</text>
            <rect x="90" y="72" width="6" height="16" fill="#0ea5e9"/>

            <!-- Row 4: Mom Room (0%) -->
            <text x="82" y="110" font-size="11" fill="#64748b" text-anchor="end">Mom Room</text>

            <!-- Row 5: Office (17%) -->
            <text x="82" y="136" font-size="11" fill="#64748b" text-anchor="end">Office</text>
            <rect x="90" y="124" width="53" height="16" fill="#0ea5e9"/>

            <!-- Row 6: Office 2 (8%) -->
            <text x="82" y="162" font-size="11" fill="#64748b" text-anchor="end">Office 2</text>
            <rect x="90" y="150" width="25" height="16" fill="#0ea5e9"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ROW 7 OF CHARTS -->
    <div class="charts-grid">
      <!-- 13. Hour-of-day heatmap -->
      <div class="chart-card">
        <h3 class="chart-title">Hour-of-day heatmap</h3>
        <div class="chart-subtitle">Total HVAC seconds per (day-of-week × hour) cell across the selected range.</div>
        
        <div class="chart-body" style="align-items: stretch;">
          <div class="heatmap-container">
            <table class="heatmap-table">
              <thead>
                <tr>
                  <th></th>
                  ${Array.from({ length: 24 })
                    .map((_, i) => `<th>${i}</th>`)
                    .join("")}
                </tr>
              </thead>
              <tbody>
                ${heatmapData
                  .map(
                    (row, rIdx) => `
                  <tr>
                    <td class="heatmap-row-label">${daysLabels[rIdx]}</td>
                    ${row
                      .map((val) => {
                        const alpha = Math.max(0.12, Math.min(0.9, val));
                        const bg = `rgba(139, 92, 246, ${alpha})`;
                        return `<td><div class="heatmap-cell" style="background-color: ${bg};" title="${daysLabels[rIdx]} hour: ${Math.round(val * 3600)}s"></div></td>`;
                      })
                      .join("")}
                  </tr>
                `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 14. Vent timeline -->
      <div class="chart-card">
        <h3 class="chart-title">Vent timeline</h3>
        <div class="chart-subtitle">Cycle-boundary vent events for the range, in chronological order.</div>
        
        <div class="chart-body" style="align-items: stretch; justify-content: flex-start;">
          <div class="vent-timeline-wrapper">
            <table class="vent-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Mode</th>
                  <th>Vent</th>
                </tr>
              </thead>
              <tbody>
                ${state.ventTimeline
                  .map(
                    (item) => `
                  <tr>
                    <td style="color: var(--text-primary);">${item.when}</td>
                    <td><span class="badge badge-blue">${item.mode}</span></td>
                    <td style="color: var(--text-secondary);">${item.vent}</td>
                  </tr>
                `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
          
          <div class="vent-timeline-footer">
            Cycle-boundary events only (opened_at_start, closed_reached_target, force_reopened_max_closed, closed_at_end). Mid-cycle vent movements are not currently tracked.
          </div>
        </div>
      </div>
    </div>
  `;

  // Handlers
  container.querySelector("#select-thermostat").addEventListener("change", (e) => {
    onFilterChange(e.target.value);
  });

  container.querySelector("#btn-export-csv").addEventListener("click", () => {
    alert("Exporting analytics data to CSV (2026-05-24 to 2026-05-30)...");
  });

  return container;
}
