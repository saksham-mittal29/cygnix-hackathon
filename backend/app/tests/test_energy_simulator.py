"""
test_energy_simulator.py
------------------------
Unit tests for Phase 2: Energy + Tariff + Solar Simulator.

Tests:
A. No solar (Load = 3 kWh, Solar = 0 -> solar_used = 0, grid_import = 3)
B. Solar equals load (Load = 3 kWh, Solar = 3 -> solar_used = 3, grid_import = 0, surplus = 0)
C. Solar less than load (Load = 3 kWh, Solar = 2 -> solar_used = 2, grid_import = 1, surplus = 0)
D. Solar greater than load (Load = 3 kWh, Solar = 5 -> solar_used = 3, grid_import = 0, surplus = 2)
E. Tariff calculation (Load = 2 kWh, Solar = 0, Tariff = 8 -> cost = 16)
F. Solar reduces cost (Load = 3 kWh, Solar = 2, Tariff = 8 -> cost = 8)
G. Zero load (Load = 0 -> grid_import = 0, cost = 0)
H. 5-minute timestep conversion (6 kW * 5/60 = 0.5 kWh)
I. Different tariff periods validation
J. Solar profile interpolation validation
K. Rejection of invalid negative inputs
"""

import pytest
from datetime import datetime
from backend.app.energy.tariff import TariffModel
from backend.app.energy.solar import SolarModel
from backend.app.energy.simulator import EnergySimulator


@pytest.fixture
def simulator():
    return EnergySimulator(timestep_minutes=5.0)


# Test A: No solar
def test_a_no_solar(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=3.0,
        solar_energy_kwh=0.0,
        tariff_rate=10.0,
    )
    assert res.solar_used_kwh == 0.0
    assert res.grid_import_kwh == 3.0
    assert res.solar_surplus_kwh == 0.0


# Test B: Solar exactly equals load
def test_b_solar_equals_load(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=3.0,
        solar_energy_kwh=3.0,
        tariff_rate=10.0,
    )
    assert res.solar_used_kwh == 3.0
    assert res.grid_import_kwh == 0.0
    assert res.solar_surplus_kwh == 0.0
    assert res.electricity_cost == 0.0


# Test C: Solar less than load
def test_c_solar_less_than_load(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=3.0,
        solar_energy_kwh=2.0,
        tariff_rate=10.0,
    )
    assert res.solar_used_kwh == 2.0
    assert res.grid_import_kwh == 1.0
    assert res.solar_surplus_kwh == 0.0
    assert res.electricity_cost == 10.0


# Test D: Solar greater than load
def test_d_solar_greater_than_load(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=3.0,
        solar_energy_kwh=5.0,
        tariff_rate=10.0,
    )
    assert res.solar_used_kwh == 3.0
    assert res.grid_import_kwh == 0.0
    assert res.solar_surplus_kwh == 2.0
    assert res.electricity_cost == 0.0


# Test E: Tariff calculation
def test_e_tariff_calculation(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=2.0,
        solar_energy_kwh=0.0,
        tariff_rate=8.0,
    )
    assert res.grid_import_kwh == 2.0
    assert res.electricity_cost == 16.0


# Test F: Solar reduces cost
def test_f_solar_reduces_cost(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=3.0,
        solar_energy_kwh=2.0,
        tariff_rate=8.0,
    )
    assert res.grid_import_kwh == 1.0
    assert res.electricity_cost == 8.0


# Test G: Zero load
def test_g_zero_load(simulator):
    res = simulator.simulate_step(
        timestamp=12,
        load_energy_kwh=0.0,
        solar_energy_kwh=1.5,
        tariff_rate=10.0,
    )
    assert res.solar_used_kwh == 0.0
    assert res.grid_import_kwh == 0.0
    assert res.solar_surplus_kwh == 1.5
    assert res.electricity_cost == 0.0


# Test H: 5-minute timestep conversion
def test_h_five_minute_timestep_conversion(simulator):
    # 6 kW over 5 minutes = 6 * (5 / 60) = 0.5 kWh
    energy_kwh = simulator.power_kW_to_energy_kWh(6.0)
    assert pytest.approx(energy_kwh, rel=1e-5) == 0.5

    # Reverse: 0.5 kWh over 5 minutes = 0.5 / (5 / 60) = 6.0 kW
    power_kw = simulator.energy_kWh_to_power_kW(0.5)
    assert pytest.approx(power_kw, rel=1e-5) == 6.0


# Test I: Different tariff periods
def test_i_different_tariff_periods():
    tariff = TariffModel()
    # 00:00–06:00 -> 4.0
    assert tariff.get_tariff(datetime(2026, 1, 1, 2, 30)) == 4.0
    assert tariff.get_tariff(5) == 4.0

    # 06:00–12:00 -> 6.0
    assert tariff.get_tariff(datetime(2026, 1, 1, 9, 0)) == 6.0
    assert tariff.get_tariff(11) == 6.0

    # 12:00–18:00 -> 10.0
    assert tariff.get_tariff(datetime(2026, 1, 1, 14, 15)) == 10.0
    assert tariff.get_tariff(17) == 10.0

    # 18:00–22:00 -> 8.0
    assert tariff.get_tariff(datetime(2026, 1, 1, 19, 45)) == 8.0
    assert tariff.get_tariff(21) == 8.0

    # 22:00–24:00 -> 5.0
    assert tariff.get_tariff(datetime(2026, 1, 1, 23, 0)) == 5.0
    assert tariff.get_tariff(22) == 5.0


# Test J: Solar profile interpolation
def test_j_solar_profile():
    solar = SolarModel()
    # Night: 0 kW
    assert solar.get_solar_power_kW(2.0) == 0.0
    assert solar.get_solar_power_kW(datetime(2026, 6, 1, 23, 0)) == 0.0

    # Morning anchor: 8.0 -> 0.5 kW
    assert pytest.approx(solar.get_solar_power_kW(8.0), rel=1e-3) == 0.5

    # Mid-morning anchor: 10.0 -> 2.0 kW
    assert pytest.approx(solar.get_solar_power_kW(10.0), rel=1e-3) == 2.0

    # Noon peak anchor: 12.0 -> 4.0 kW
    assert pytest.approx(solar.get_solar_power_kW(12.0), rel=1e-3) == 4.0

    # Afternoon anchor: 14.0 -> 3.0 kW
    assert pytest.approx(solar.get_solar_power_kW(14.0), rel=1e-3) == 3.0

    # Evening: 18.0 -> 0.0 kW
    assert pytest.approx(solar.get_solar_power_kW(18.0), rel=1e-3) == 0.0


# Test K: Validation and invalid input rejection
def test_k_invalid_input_rejection(simulator):
    with pytest.raises(ValueError):
        simulator.simulate_step(timestamp=12, load_energy_kwh=-1.0)

    with pytest.raises(ValueError):
        simulator.simulate_step(timestamp=12, load_power_kw=-5.0)

    with pytest.raises(ValueError):
        simulator.simulate_step(timestamp=12, load_energy_kwh=2.0, solar_energy_kwh=-0.5)

    with pytest.raises(ValueError):
        simulator.simulate_step(timestamp=12, load_energy_kwh=2.0, tariff_rate=-2.0)

    with pytest.raises(ValueError):
        EnergySimulator(timestep_minutes=0)

    with pytest.raises(ValueError):
        TariffModel(schedule=[(0, 12, -4.0), (12, 24, 6.0)])
