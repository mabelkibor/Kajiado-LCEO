"""Equations 11-14 — dual-perspective discounted cash flow.

    CF_t = R_t - O_t - C_t                                        (11)
    NPV  = sum_t CF_t / (1+r)^t  -  CAPEX_0                        (12)
    0    = sum_t CF_t / (1+IRR)^t  -  CAPEX_0                      (13)
    DPP  = min { T : sum_{t<=T} CF_t / (1+r)^t  >=  CAPEX_0 }      (14)

Two conventions matter for reading the code against the equations.

**Capital outlay is counted once.** Equations 12-14 as written contain both a
``C_t`` term inside ``CF_t`` and a separate ``- CAPEX_0``. Taken literally that
charges year-zero capital twice. This implementation builds ``CF_t`` for
``t >= 1`` from revenue and operating cost only, keeps capital in the explicit
``CAPEX_0`` term, and adds year-zero connection-fee revenue to that same term
where the household bears the fee. The results are therefore consistent with the
stated intent of Section 3.5.4, which gives the developer case as
``CF_0 = H_c * Fee_household - CAPEX_dev,c``.

**The connection fee moves between sides of the ledger by perspective.** Where
a utility or REREC subsidises the connection, the fee is a cost inside CAPEX
(Equations 5-6). Where the household or a private developer bears it directly,
it is a one-off inflow to the developer at ``t = 0``. The
``connection_fee_subsidy_share`` parameter of each perspective selects between
these treatments, which makes the fee a first-class object of the sensitivity
analysis rather than a buried constant.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from kajiado_lceo.config import Config
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CashFlowResult:
    """Year-zero outlay and the ``t >= 1`` net cash flows of one settlement."""

    capex_0: float
    cash_flows: np.ndarray  # index 0 == year 1

    def as_series(self) -> np.ndarray:
        """Full ``t = 0..n`` vector, with the year-zero outlay negative."""
        return np.concatenate([[-self.capex_0], self.cash_flows])


def build_cash_flows(
    capex: float,
    opex: float,
    annual_energy_kwh: float,
    households: float,
    perspective: dict,
    config: Config,
    connection_fee_per_household: float = 0.0,
) -> CashFlowResult:
    """Construct ``CF_t`` for one settlement under one perspective (Equation 11).

    Revenue is tariff income on energy actually delivered, which is reduced by
    the utilisation ramp (new connections take several years to reach their
    modelled tier) and by collection efficiency (billed is not collected).
    Both are explicit parameters rather than an assumed 100%, because assuming
    full revenue from year one is the single most common way an electrification
    appraisal overstates viability.
    """
    period = int(config.require("finance.analysis_period_years"))
    cash_cfg = config.section("finance.cash_flow")
    tariff = float(perspective.get("tariff_per_kwh", 0.0))
    tariff_escalation = float(cash_cfg.get("tariff_escalation", 0.0))
    opex_escalation = float(cash_cfg.get("opex_escalation", 0.0))
    collection = float(perspective.get("collection_efficiency", 1.0))
    growth = float(config.get("demand.annual_growth_rate", 0.0))
    ramp = list(cash_cfg.get("utilisation_ramp", [1.0])) or [1.0]

    subsidy_share = float(perspective.get("connection_fee_subsidy_share", 1.0))
    # The unsubsidised share of the fee is paid by the household to the
    # investor at t = 0, offsetting capital (Section 3.5.4).
    fee_revenue_0 = households * connection_fee_per_household * (1.0 - subsidy_share)
    rbf = float(perspective.get("results_based_finance_per_connection", 0.0)) * households

    flows = np.zeros(period, dtype=float)
    for t in range(1, period + 1):
        utilisation = float(ramp[min(t - 1, len(ramp) - 1)])
        energy_t = annual_energy_kwh * ((1.0 + growth) ** (t - 1)) * utilisation
        revenue_t = energy_t * tariff * ((1.0 + tariff_escalation) ** (t - 1)) * collection
        opex_t = opex * ((1.0 + opex_escalation) ** (t - 1))
        flows[t - 1] = revenue_t - opex_t

    salvage_fraction = float(cash_cfg.get("salvage_fraction", 0.0))
    if salvage_fraction:
        flows[-1] += capex * salvage_fraction

    return CashFlowResult(capex_0=float(capex - fee_revenue_0 - rbf), cash_flows=flows)


def net_present_value(cash_flows: np.ndarray, capex_0: float, discount_rate: float) -> float:
    """Equation 12 — NPV of a ``t >= 1`` cash-flow stream net of year-zero capital."""
    flows = np.asarray(cash_flows, dtype=float)
    t = np.arange(1, len(flows) + 1)
    return float(np.sum(flows / (1.0 + discount_rate) ** t) - capex_0)


def internal_rate_of_return(cash_flows: np.ndarray, capex_0: float, config: Config) -> float:
    """Equation 13 — IRR, solved numerically.

    Returns ``NaN`` where no sign change brackets a root: a project that never
    turns cash-positive has no IRR, and reporting one would be meaningless. Such
    settlements are the ones the viability flag routes to public support.
    """
    irr_cfg = config.section("finance.irr")
    lower = float(irr_cfg.get("lower_bound", -0.95))
    upper = float(irr_cfg.get("upper_bound", 3.0))
    tolerance = float(irr_cfg.get("tolerance", 1e-7))

    def npv_at(rate: float) -> float:
        return net_present_value(cash_flows, capex_0, rate)

    try:
        low_value, high_value = npv_at(lower), npv_at(upper)
    except (OverflowError, ZeroDivisionError):
        return float("nan")

    if not np.isfinite(low_value) or not np.isfinite(high_value):
        return float("nan")
    if low_value * high_value > 0:
        return float("nan")

    try:
        return float(
            brentq(
                npv_at,
                lower,
                upper,
                xtol=tolerance,
                maxiter=int(irr_cfg.get("max_iterations", 200)),
            )
        )
    except (ValueError, RuntimeError):
        return float("nan")


def discounted_payback_period(
    cash_flows: np.ndarray, capex_0: float, discount_rate: float
) -> float:
    """Equation 14 — discounted payback period, in years.

    Linear interpolation is applied within the recovery year so the result is
    continuous, which matters when payback is used to rank schemes. ``NaN``
    means capital is never recovered inside the analysis period.
    """
    flows = np.asarray(cash_flows, dtype=float)
    cumulative = 0.0
    for t, flow in enumerate(flows, start=1):
        discounted = flow / (1.0 + discount_rate) ** t
        if cumulative + discounted >= capex_0:
            if discounted <= 0:
                return float(t)
            return float(t - 1 + (capex_0 - cumulative) / discounted)
        cumulative += discounted
    return float("nan")


def evaluate_viability(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Run Equations 11-14 for every settlement under every perspective.

    Adds, for each perspective key ``p``: ``npv_p``, ``irr_p``, ``dpp_p``,
    ``viable_p`` and a ``subsidy_gap_p`` — the present-value grant that would
    bring a non-viable settlement to NPV = 0, which is the number a county
    budget submission or a results-based-finance application actually needs.
    """
    df = settlements.copy()
    perspectives = config.section("finance.perspectives")
    flag_public = bool(config.get("finance.viability_flags.flag_for_public_support", True))

    for key, perspective in perspectives.items():
        npvs, irrs, dpps, viable, gaps = [], [], [], [], []
        hurdle = float(perspective.get("hurdle_rate", perspective.get("wacc", 0.0)))
        discount_rate = float(perspective.get("wacc", config.require("finance.discount_rate")))

        for row in df.itertuples(index=False):
            technology = getattr(row, "least_cost_technology", "none")
            capex = getattr(row, "least_cost_capex", np.nan)
            opex = getattr(row, "least_cost_opex", np.nan)

            if technology == "none" or not np.isfinite(capex):
                npvs.append(np.nan)
                irrs.append(np.nan)
                dpps.append(np.nan)
                viable.append(False)
                gaps.append(np.nan)
                continue

            fee = float(config.get(f"technologies.{technology}.connection_cost_per_household", 0.0))
            result = build_cash_flows(
                capex=float(capex),
                opex=float(opex),
                annual_energy_kwh=float(row.annual_energy_kwh),
                households=float(row.households),
                perspective=perspective,
                config=config,
                connection_fee_per_household=fee,
            )
            npv = net_present_value(result.cash_flows, result.capex_0, discount_rate)
            irr = internal_rate_of_return(result.cash_flows, result.capex_0, config)
            dpp = discounted_payback_period(result.cash_flows, result.capex_0, discount_rate)

            is_viable = bool(npv >= 0.0 or (np.isfinite(irr) and irr >= hurdle))
            npvs.append(npv)
            irrs.append(irr)
            dpps.append(dpp)
            viable.append(is_viable)
            gaps.append(0.0 if is_viable else float(-npv))

        df[f"npv_{key}"] = npvs
        df[f"irr_{key}"] = irrs
        df[f"dpp_{key}"] = dpps
        df[f"viable_{key}"] = viable
        df[f"subsidy_gap_{key}"] = gaps

        logger.info(
            "%s perspective: %d of %d settlements viable (hurdle %.1f%%)",
            perspective.get("label", key),
            int(np.sum(viable)),
            len(df),
            100.0 * hurdle,
        )

    if flag_public and "viable_utility" in df.columns:
        developer = df.get("viable_developer", pd.Series(False, index=df.index))
        df["requires_public_support"] = ~(df["viable_utility"] | developer)
    return df
