"""
simulator.py
------------
Energy and electricity cost simulator for Wisp Person 3.
Calculates solar self-consumption, grid import, solar surplus, and electricity cost.

Energy Flow:
  Load
    |
    v
  Solar supplies load first
    |
    v
  Remaining demand -> Grid Import

Units:
- Power: kW
- Energy: kWh (Energy = Power * timestep_minutes / 60)
- Electricity Tariff: currency / kWh
- Timestep: Configurable minutes (default: 5.0 minutes)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union
from backend.app.energy.tariff import TariffModel
from backend.app.energy.solar import SolarModel


@dataclass(frozen=True)
class EnergySimulationResult:
    """
    Structured outcome of an energy simulation step.
    """
    timestamp: Any
    timestep_minutes: float
    load_power_kw: float
    load_energy_kwh: float
    solar_power_kw: float
    solar_energy_kwh: float
    solar_used_kwh: float
    grid_import_kwh: float
    solar_surplus_kwh: float
    tariff_rate: float
    electricity_cost: float


class EnergySimulator:
    """
    Modular energy balance and electricity cost simulator.
    Independent of data sources (supports live telemetry, synthetic models, or BDG2 providers).
    """

    def __init__(
        self,
        tariff_model: Optional[TariffModel] = None,
        solar_model: Optional[SolarModel] = None,
        timestep_minutes: float = 5.0,
    ):
        """
        Initializes the EnergySimulator.

        Args:
            tariff_model: Configured TariffModel instance (uses default schedule if None).
            solar_model: Configured SolarModel instance (uses default profile if None).
            timestep_minutes: Simulation interval in minutes (default: 5.0 min).
        """
        if timestep_minutes <= 0:
            raise ValueError(f"timestep_minutes must be positive, got {timestep_minutes}")

        self.timestep_minutes = float(timestep_minutes)
        self.tariff_model = tariff_model if tariff_model is not None else TariffModel()
        self.solar_model = solar_model if solar_model is not None else SolarModel()

    def power_kW_to_energy_kWh(self, power_kw: float) -> float:
        """Converts power (kW) to energy (kWh) over the simulation timestep."""
        if power_kw < 0:
            raise ValueError(f"Power cannot be negative: {power_kw} kW")
        return power_kw * (self.timestep_minutes / 60.0)

    def energy_kWh_to_power_kW(self, energy_kwh: float) -> float:
        """Converts energy (kWh) to average power (kW) over the simulation timestep."""
        if energy_kwh < 0:
            raise ValueError(f"Energy cannot be negative: {energy_kwh} kWh")
        return energy_kwh / (self.timestep_minutes / 60.0)

    def simulate_step(
        self,
        timestamp: Any,
        load_power_kw: Optional[float] = None,
        load_energy_kwh: Optional[float] = None,
        solar_power_kw: Optional[float] = None,
        solar_energy_kwh: Optional[float] = None,
        tariff_rate: Optional[float] = None,
    ) -> EnergySimulationResult:
        """
        Executes an energy balance and cost simulation step for a single timestep.

        Args:
            timestamp: Simulation timestamp (datetime, epoch seconds, or hour).
            load_power_kw: Building/HVAC demand power in kW (optional if load_energy_kwh provided).
            load_energy_kwh: Building/HVAC demand energy in kWh (optional if load_power_kw provided).
            solar_power_kw: Solar PV generation in kW (optional; uses solar_model if None).
            solar_energy_kwh: Solar PV energy in kWh (optional; uses solar_model if None).
            tariff_rate: Explicit tariff rate in currency/kWh (optional; uses tariff_model if None).

        Returns:
            EnergySimulationResult containing detailed power, energy, surplus, and cost.
        """
        # 1. Resolve and Validate Load
        if load_energy_kwh is not None:
            if load_energy_kwh < 0:
                raise ValueError(f"load_energy_kwh cannot be negative: {load_energy_kwh}")
            load_kwh = float(load_energy_kwh)
            load_kw = self.energy_kWh_to_power_kW(load_kwh) if load_power_kw is None else float(load_power_kw)
        elif load_power_kw is not None:
            if load_power_kw < 0:
                raise ValueError(f"load_power_kw cannot be negative: {load_power_kw}")
            load_kw = float(load_power_kw)
            load_kwh = self.power_kW_to_energy_kWh(load_kw)
        else:
            raise ValueError("Either load_power_kw or load_energy_kwh must be provided")

        # 2. Resolve and Validate Solar Generation
        if solar_energy_kwh is not None:
            if solar_energy_kwh < 0:
                raise ValueError(f"solar_energy_kwh cannot be negative: {solar_energy_kwh}")
            solar_kwh = float(solar_energy_kwh)
            solar_kw = self.energy_kWh_to_power_kW(solar_kwh) if solar_power_kw is None else float(solar_power_kw)
        elif solar_power_kw is not None:
            if solar_power_kw < 0:
                raise ValueError(f"solar_power_kw cannot be negative: {solar_power_kw}")
            solar_kw = float(solar_power_kw)
            solar_kwh = self.power_kW_to_energy_kWh(solar_kw)
        else:
            # Query SolarModel
            solar_kw = self.solar_model.get_solar_power_kW(timestamp)
            solar_kwh = self.power_kW_to_energy_kWh(solar_kw)

        # 3. Resolve and Validate Tariff Rate
        if tariff_rate is not None:
            if tariff_rate < 0:
                raise ValueError(f"tariff_rate cannot be negative: {tariff_rate}")
            rate = float(tariff_rate)
        else:
            rate = self.tariff_model.get_tariff(timestamp)

        # 4. Energy Balance (Solar -> Load, Remaining -> Grid)
        if solar_kwh >= load_kwh:
            solar_used_kwh = load_kwh
            solar_surplus_kwh = solar_kwh - load_kwh
            grid_import_kwh = 0.0
        else:
            solar_used_kwh = solar_kwh
            solar_surplus_kwh = 0.0
            grid_import_kwh = load_kwh - solar_kwh

        # 5. Electricity Cost Calculation
        electricity_cost = grid_import_kwh * rate

        return EnergySimulationResult(
            timestamp=timestamp,
            timestep_minutes=self.timestep_minutes,
            load_power_kw=round(load_kw, 6),
            load_energy_kwh=round(load_kwh, 6),
            solar_power_kw=round(solar_kw, 6),
            solar_energy_kwh=round(solar_kwh, 6),
            solar_used_kwh=round(solar_used_kwh, 6),
            grid_import_kwh=round(grid_import_kwh, 6),
            solar_surplus_kwh=round(solar_surplus_kwh, 6),
            tariff_rate=round(rate, 6),
            electricity_cost=round(electricity_cost, 6),
        )
