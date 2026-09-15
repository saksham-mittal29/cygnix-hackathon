export const initialData = {
  version: "v0.13.0",
  lastUpdated: "3:13:19 PM",
  vacationMode: false,
  
  zones: [
    {
      id: "downstairs",
      name: "Downstairs",
      entityId: "climate.downstairs_2",
      mode: "COOL",
      ambient: "70.0°F",
      setpoint: "70.0°F",
      cycle: "IDLE",
      activeRooms: "0 / 1"
    },
    {
      id: "upstairs",
      name: "Upstairs",
      entityId: "climate.upstairs_2",
      mode: "COOLING",
      ambient: "71.0°F",
      setpoint: "71.0°F",
      cycle: "IDLE",
      activeRooms: "0 / 6"
    }
  ],

  rooms: [
    {
      id: "bathroom",
      name: "Bathroom",
      zoneName: "Upstairs",
      entityId: "climate.upstairs_2",
      statusText: "Not active",
      nextSched: "next 68.0°F Sun 9:00 PM (29h 46m)",
      temp: "70.2°F",
      presence: "Unoccupied",
      vents: "Closed",
      sensorsCount: 1,
      ventsCount: 1,
      presenceCount: 2,
      offset: null,
      noVentsWarning: false
    },
    {
      id: "bedroom",
      name: "Bedroom",
      zoneName: "Upstairs",
      entityId: "climate.upstairs_2",
      statusTarget: "70.0°F",
      statusVia: "via Presence ends in 1h 21m",
      hasClearPresence: true,
      nextSched: "then 68.0°F Sat 10:30 PM (7h 16m)",
      temp: "71.4°F",
      presence: "Unoccupied",
      vents: "Open",
      sensorsCount: 1,
      ventsCount: 1,
      presenceCount: 2,
      offset: null,
      noVentsWarning: false
    },
    {
      id: "downstairs-room",
      name: "Downstairs",
      zoneName: "Downstairs",
      entityId: "climate.downstairs_2",
      statusTarget: "70.0°F",
      statusVia: "via Presence ends in 1h 31m",
      hasClearPresence: true,
      nextSched: null,
      temp: "70.0°F",
      presence: "Occupied (resets in 1h 31m)",
      vents: null,
      sensorsCount: 1,
      ventsCount: 0,
      presenceCount: 6,
      offset: null,
      noVentsWarning: true
    },
    {
      id: "gym",
      name: "Gym",
      zoneName: "Upstairs",
      entityId: "climate.upstairs_2",
      statusText: "Not active",
      nextSched: null,
      temp: "71.1°F",
      presence: "Unoccupied",
      vents: "Closed",
      sensorsCount: 1,
      ventsCount: 1,
      presenceCount: 2,
      offset: null,
      noVentsWarning: false
    },
    {
      id: "mom-room",
      name: "Mom Room",
      zoneName: "Upstairs",
      entityId: "climate.upstairs_2",
      statusText: "Not active",
      nextSched: null,
      temp: "65.8°F",
      presence: null,
      vents: "Closed",
      sensorsCount: 1,
      ventsCount: 1,
      presenceCount: 0,
      offset: null,
      noVentsWarning: false
    },
    {
      id: "office",
      name: "Office",
      zoneName: "Upstairs",
      entityId: "climate.upstairs_2",
      statusTarget: "70.0°F",
      statusVia: "via Presence ends in 25m 24s",
      hasClearPresence: true,
      nextSched: null,
      temp: "70.9°F",
      presence: "Occupied (resets in 25m 24s)",
      vents: "Open",
      sensorsCount: 1,
      ventsCount: 1,
      presenceCount: 3,
      offset: "OFFSET -1°F",
      noVentsWarning: false
    }
  ],

  schedules: [
    {
      id: "bathroom",
      name: "Bathroom",
      entityId: "climate.upstairs_2",
      expanded: false,
      blocks: [
        { id: "b1", days: "Sun", start: "21:00:00", end: "07:00:00", target: "68.0°F" }
      ]
    },
    {
      id: "bedroom",
      name: "Bedroom",
      entityId: "climate.upstairs_2",
      expanded: true,
      blocks: [
        { id: "b2_1", days: "MTWTS", start: "21:00:00", end: "07:00:00", target: "68.0°F" },
        { id: "b2_2", days: "FS", start: "22:30:00", end: "08:00:00", target: "68.0°F" }
      ]
    },
    {
      id: "downstairs",
      name: "Downstairs",
      entityId: "climate.downstairs_2",
      expanded: false,
      blocks: []
    },
    {
      id: "gym",
      name: "Gym",
      entityId: "climate.upstairs_2",
      expanded: false,
      blocks: []
    },
    {
      id: "mom-room",
      name: "Mom Room",
      entityId: "climate.upstairs_2",
      expanded: false,
      blocks: []
    },
    {
      id: "office",
      name: "Office",
      entityId: "climate.upstairs_2",
      expanded: false,
      blocks: []
    },
    {
      id: "office-2",
      name: "Office 2",
      entityId: "climate.upstairs_2",
      expanded: false,
      blocks: []
    }
  ],

  metrics: {
    all: {
      heatingTime: "7h 50m",
      heatingSub: "2 thermostats",
      coolingTime: "76h 1m",
      dutyCycle: "25.0%",
      cycles: "311",
      cyclesSub: "284 completed",
      avgOutsideTemp: "73.3°F",
      tempSub: "At cycle start",
      showingText: "Showing 2 thermostats for 2026-05-24 → 2026-05-30"
    },
    upstairs: {
      heatingTime: "7h 50m",
      coolingTime: "66h 20m",
      dutyCycle: "44.1%",
      cycles: "275",
      cyclesSub: "248 completed",
      avgOutsideTemp: "73.1°F",
      tempSub: "At cycle start",
      showingText: "Showing Upstairs for 2026-05-24 → 2026-05-30"
    }
  },

  ventTimeline: [
    { when: "2026-05-24T04:35:18.000708", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T04:35:18.000708", mode: "COOLING", vent: "cover.bedroom_f503_bed_vent" },
    { when: "2026-05-24T04:35:20.039569", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T04:43:54.242273", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T04:44:54.757738", mode: "COOLING", vent: "cover.bedroom_f503_bed_vent" },
    { when: "2026-05-24T04:47:54.716433", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T04:56:48.116970", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T04:56:48.116970", mode: "COOLING", vent: "cover.bedroom_f503_bed_vent" },
    { when: "2026-05-24T04:56:49.983163", mode: "COOLING", vent: "cover.bathroom_700d_vent" },
    { when: "2026-05-24T05:04:54.518442", mode: "COOLING", vent: "cover.bathroom_700d_vent" }
  ],

  thermostats: [
    {
      id: "downstairs_2",
      name: "Downstairs Thermostat",
      model: "Ecobee SmartThermostat",
      zone: "Downstairs",
      entity: "climate.downstairs_2",
      status: "Online",
      currentTemp: "70.0°F",
      targetTemp: "70.0°F",
      humidity: "42%",
      firmware: "v4.7.5.3"
    },
    {
      id: "upstairs_2",
      name: "Upstairs Thermostat",
      model: "Ecobee SmartThermostat",
      zone: "Upstairs",
      entity: "climate.upstairs_2",
      status: "Online",
      currentTemp: "71.0°F",
      targetTemp: "71.0°F",
      humidity: "46%",
      firmware: "v4.7.5.3"
    }
  ],

  detailedLogs: [
    { time: "2:43:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "2:45:02 PM", level: "INFO", tag: "[presence]", message: "Presence detected in Downstairs via binary_sensor.downstairs_motion" },
    { time: "2:48:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=running, ha_mode='cool', ha_setpoint=68, expected_mode='cool', expected_setpoint=68.0, active_rooms=2, cycle_id=1ed97f7a-867d-4346-a60e-383690708147" },
    { time: "2:48:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "2:53:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=running, ha_mode='cool', ha_setpoint=68, expected_mode='cool', expected_setpoint=68.0, active_rooms=2, cycle_id=1ed97f7a-867d-4346-a60e-383690708147" },
    { time: "2:54:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "2:58:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=running, ha_mode='cool', ha_setpoint=68, expected_mode='cool', expected_setpoint=68.0, active_rooms=2, cycle_id=1ed97f7a-867d-4346-a60e-383690708147" },
    { time: "3:00:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "3:03:56 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=running, ha_mode='cool', ha_setpoint=68, expected_mode='cool', expected_setpoint=68.0, active_rooms=2, cycle_id=1ed97f7a-867d-4346-a60e-383690708147" },
    { time: "3:05:56 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "3:06:53 PM", level: "INFO", tag: "[api]", message: "Room updated: Office 2" },
    { time: "3:09:14 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=running, ha_mode='cool', ha_setpoint=68, expected_mode='cool', expected_setpoint=68.0, active_rooms=2, cycle_id=1ed97f7a-867d-4346-a60e-383690708147" },
    { time: "3:11:15 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.downstairs_2: engine=idle, ha_mode='cool', ha_setpoint=70, expected_mode=None, expected_setpoint=70.0, active_rooms=0, cycle_id=none" },
    { time: "3:12:15 PM", level: "INFO", tag: "[engine]", message: "Closed vent cover.office_a9c9_vent (room at target)" },
    { time: "3:12:15 PM", level: "INFO", tag: "[engine]", message: "Room Office reached target 70.0°F (avg=70.9°F, effective=69.9°F, offset=-1.0°F) – vent closed" },
    { time: "3:12:15 PM", level: "INFO", tag: "[engine]", message: "Cycle terminated for climate.upstairs_2 – setpoint reset to ambient 71.0°F" },
    { time: "3:12:18 PM", level: "INFO", tag: "[engine]", message: "Opened vent cover.bedroom_f503_bed_vent" },
    { time: "3:12:18 PM", level: "INFO", tag: "[engine]", message: "Opened vent cover.office_a9c9_vent" },
    { time: "3:12:18 PM", level: "INFO", tag: "[engine]", message: "Cycle complete for climate.upstairs_2 – all zone vents re-opened" },
    { time: "3:14:14 PM", level: "INFO", tag: "[reconcile]", message: "Reconcile climate.upstairs_2: engine=idle, ha_mode='cool', ha_setpoint=71, expected_mode=None, expected_setpoint=71.0, active_rooms=0, cycle_id=none" },
    { time: "3:14:16 PM", level: "INFO", tag: "[engine]", message: "Opened vent cover.bathroom_700d_vent" },
    { time: "3:14:16 PM", level: "WARNING", tag: "[reconcile]", message: "Drift (idle): vent cover.bathroom_700d_vent found closed while zone is idle — re-opened" },
    { time: "3:14:16 PM", level: "INFO", tag: "[engine]", message: "Opened vent cover.gym_19fb_vent" },
    { time: "3:14:16 PM", level: "WARNING", tag: "[reconcile]", message: "Drift (idle): vent cover.gym_19fb_vent found closed while zone is idle — re-opened" },
    { time: "3:14:16 PM", level: "INFO", tag: "[engine]", message: "Opened vent cover.mom_room_3931_vent" }
  ]
};
