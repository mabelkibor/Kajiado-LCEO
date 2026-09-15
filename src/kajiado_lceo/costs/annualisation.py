"""Equations 8, 9 and 9a — annualisation and the Levelized Cost of Electricity.

Equation 8, the Capital Recovery Factor, converts a present capital sum into an
equal annual payment over ``n`` years at discount rate ``r``::

    CRF(r,n) = r*(1+r)^n / ((1+r)^n - 1)

Equation 9, the annualised LCOE, applied identically to all three technologies
so the comparison in Equation 10 is like-for-like::

    LCOE_i,c = (CAPEX_i,c * CRF(r,n) + OPEX_i,c) / E_c

Equation 9a, the discounted multi-year form, which the proposal gives as the
equivalent statement::

    NPC_i,c  = sum_t [ CAPEX*1{t=0} + OPEX_t - Salvage_t ] / (1+r)^t
    LCOE_i,c = NPC_i,c / sum_t [ E_c / (1+r)^t ]

The two forms coincide when OPEX is constant and there are no replacements or
salvage. They diverge — and 9a is the one to trust — once mid-life battery and
inverter replacements enter, which is precisely the case for mini-grids and SHS.
:func:`npc_lcoe` is therefore what the pipeline uses; :func:`lcoe` is retained
because it is the headline equation of the proposal and is what the sensitivity
discussion refers to.
"""

from __future__ import annotations

import numpy as np


def capital_recovery_factor(discount_rate: float, lifetime_years: int) -> float:
    """Equation 8 — Capital Recovery Factor.

    The zero-rate case is handled as the limit ``CRF -> 1/n``, which keeps a
    zero-discount sensitivity run from dividing by zero.
    """
    r = float(discount_rate)
    n = int(lifetime_years)
    if n <= 0:
        raise ValueError("lifetime_years must be positive")
    if abs(r) < 1e-12:
        return 1.0 / n
    factor = (1.0 + r) ** n
    return r * factor / (factor - 1.0)


def lcoe(
    capex: float | np.ndarray,
    opex: float | np.ndarray,
    annual_energy_kwh: float | np.ndarray,
    discount_rate: float,
    lifetime_years: int,
) -> np.ndarray:
    """Equation 9 — annualised LCOE, in currency units per kWh.

    Settlements with zero or missing demand return ``NaN`` rather than infinity,
    so that they are excluded from the argmin of Equation 10 instead of being
    silently ranked last.
    """
    crf = capital_recovery_factor(discount_rate, lifetime_years)
    capex_arr = np.asarray(capex, dtype=float)
    opex_arr = np.asarray(opex, dtype=float)
    energy = np.asarray(annual_energy_kwh, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (capex_arr * crf + opex_arr) / energy
    return np.where(energy > 0, result, np.nan)


def net_present_cost(
    capex: float | np.ndarray,
    opex: float | np.ndarray,
    discount_rate: float,
    lifetime_years: int,
    replacements: list[tuple[int, np.ndarray]] | None = None,
    salvage_fraction: float = 0.0,
    opex_escalation: float = 0.0,
) -> np.ndarray:
    """Net present cost ``NPC_i,c`` over the analysis period (Equation 9a).

    Args:
        capex: year-zero capital outlay.
        opex: first-year operating cost; escalated at ``opex_escalation``.
        discount_rate: ``r``.
        lifetime_years: ``n``, the analysis period.
        replacements: ``(year, cost)`` pairs for mid-life component renewal.
        salvage_fraction: terminal value as a share of CAPEX, credited in
            year ``n`` and therefore netted off the NPC.
        opex_escalation: real annual escalation applied to operating cost.
    """
    r = float(discount_rate)
    n = int(lifetime_years)
    capex_arr = np.asarray(capex, dtype=float)
    opex_arr = np.asarray(opex, dtype=float)

    npc = np.array(capex_arr, dtype=float, copy=True)
    for t in range(1, n + 1):
        npc = npc + opex_arr * ((1.0 + opex_escalation) ** (t - 1)) / ((1.0 + r) ** t)

    for year, cost in replacements or []:
        if 0 < year <= n:
            npc = npc + np.asarray(cost, dtype=float) / ((1.0 + r) ** year)

    if salvage_fraction:
        npc = npc - capex_arr * float(salvage_fraction) / ((1.0 + r) ** n)
    return npc


def discounted_energy(
    annual_energy_kwh: float | np.ndarray,
    discount_rate: float,
    lifetime_years: int,
    demand_growth: float = 0.0,
) -> np.ndarray:
    """Denominator of Equation 9a — the discounted lifetime energy delivered.

    Discounting energy as well as cost is what makes the LCOE a ratio of two
    present values; omitting it would systematically favour technologies whose
    costs fall late in the project.
    """
    r = float(discount_rate)
    n = int(lifetime_years)
    energy = np.asarray(annual_energy_kwh, dtype=float)
    total = np.zeros_like(energy, dtype=float)
    for t in range(1, n + 1):
        total = total + energy * ((1.0 + demand_growth) ** (t - 1)) / ((1.0 + r) ** t)
    return total


def npc_lcoe(
    capex: float | np.ndarray,
    opex: float | np.ndarray,
    annual_energy_kwh: float | np.ndarray,
    discount_rate: float,
    lifetime_years: int,
    replacements: list[tuple[int, np.ndarray]] | None = None,
    salvage_fraction: float = 0.0,
    opex_escalation: float = 0.0,
    demand_growth: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Equation 9a — returns ``(lcoe, npc)``.

    This is the form the pipeline uses, because mini-grid and SHS replacement
    cycles fall inside the analysis period and must be discounted at the year
    they occur rather than annualised flat.
    """
    npc = net_present_cost(
        capex,
        opex,
        discount_rate,
        lifetime_years,
        replacements=replacements,
        salvage_fraction=salvage_fraction,
        opex_escalation=opex_escalation,
    )
    energy = discounted_energy(annual_energy_kwh, discount_rate, lifetime_years, demand_growth)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = npc / energy
    return np.where(energy > 0, result, np.nan), npc
