export function renderSchedulesTab(state, setState, onAddScheduleBlock, onEditScheduleBlock) {
  const container = document.createElement("div");
  container.className = "tab-content schedules-tab";

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Schedules</h1>
        <div class="page-subtitle">Time-based temperature targets per room</div>
      </div>
    </div>

    <div class="schedules-list">
      ${state.schedules
        .map((sched) => {
          const blockCount = sched.blocks.length;
          const arrow = sched.expanded ? "▲" : "▼";

          return `
          <div class="schedule-card" id="schedule-card-${sched.id}">
            <div class="schedule-card-header" data-sched-id="${sched.id}">
              <div class="schedule-header-left">
                <h2 class="schedule-room-title">${sched.name}</h2>
                <div class="schedule-entity-id">${sched.entityId}</div>
              </div>
              <div class="schedule-blocks-badge">
                <span>${blockCount} BLOCKS</span>
                <span class="schedule-arrow">${arrow}</span>
              </div>
            </div>

            ${
              sched.expanded
                ? `
              <div class="schedule-card-body">
                ${
                  blockCount > 0
                    ? `
                  <div class="schedule-table-wrapper">
                    <table class="schedule-table">
                      <thead>
                        <tr>
                          <th>Days</th>
                          <th>Start</th>
                          <th>End</th>
                          <th>Target</th>
                          <th style="text-align: right;"></th>
                        </tr>
                      </thead>
                      <tbody>
                        ${sched.blocks
                          .map(
                            (block) => `
                          <tr>
                            <td><strong>${block.days}</strong></td>
                            <td>${block.start}</td>
                            <td>${block.end}</td>
                            <td class="schedule-target-temp">${block.target}</td>
                            <td>
                              <div class="schedule-actions-cell">
                                <button class="btn-sched-edit" data-sched-id="${sched.id}" data-block-id="${block.id}">
                                  Edit
                                </button>
                                <button class="btn-sched-del" data-sched-id="${sched.id}" data-block-id="${block.id}">
                                  Del
                                </button>
                              </div>
                            </td>
                          </tr>
                        `
                          )
                          .join("")}
                      </tbody>
                    </table>
                  </div>
                `
                    : `
                  <div style="padding: 16px 0; color: var(--text-secondary); font-size: 13px;">
                    No scheduled temperature blocks set for this room.
                  </div>
                `
                }
                
                <button class="btn btn-primary btn-add-sched-block" data-sched-id="${sched.id}">
                  + Add schedule block
                </button>
              </div>
            `
                : ""
            }
          </div>
        `;
        })
        .join("")}
    </div>
  `;

  // Accordion toggle handlers
  container.querySelectorAll(".schedule-card-header").forEach((header) => {
    header.addEventListener("click", () => {
      const schedId = header.getAttribute("data-sched-id");
      const updated = state.schedules.map((s) =>
        s.id === schedId ? { ...s, expanded: !s.expanded } : s
      );
      setState({ schedules: updated });
    });
  });

  // Schedule block actions
  container.querySelectorAll(".btn-add-sched-block").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const schedId = btn.getAttribute("data-sched-id");
      onAddScheduleBlock(schedId);
    });
  });

  container.querySelectorAll(".btn-sched-edit").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const schedId = btn.getAttribute("data-sched-id");
      const blockId = btn.getAttribute("data-block-id");
      onEditScheduleBlock(schedId, blockId);
    });
  });

  container.querySelectorAll(".btn-sched-del").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const schedId = btn.getAttribute("data-sched-id");
      const blockId = btn.getAttribute("data-block-id");
      if (confirm("Delete this schedule block?")) {
        const updated = state.schedules.map((s) => {
          if (s.id === schedId) {
            return {
              ...s,
              blocks: s.blocks.filter((b) => b.id !== blockId)
            };
          }
          return s;
        });
        setState({ schedules: updated });
      }
    });
  });

  return container;
}
