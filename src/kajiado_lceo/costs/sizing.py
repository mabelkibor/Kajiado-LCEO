"""Physical sizing rules that feed the CAPEX equations.

Equations 5 and 6 both contain an internal-network length term (``L_LV,c`` and
``L_mg,c``) that the proposal states but does not parameterise. Both are
estimated here from settlement geometry using the standard reticulation
heuristic

    L = a * sqrt(H_c * A_c) + b * H_c

where ``A_c`` is the settlement footprint area in km^2. The first term scales
with the linear extent of the settlement — the backbone needed to traverse it —
and the second is the per-household service drop. The coefficients ``a`` and
``b`` are configuration, not constants, and should be calibrated against a
sample of built KPLC/REREC schemes before results are reported.
"""

from __future__ import annotations

import numpy as np


def lv_network_length_km(
    households: float | np.ndarray,
    area_km2: float | np.ndarray,
    area_coefficient: float,
    per_household_km: float,
) -> np.ndarray:
    """Internal reticulation length in km for a settlement.

    Args:
        households: household count ``H_c``.
        area_km2: settlement footprint area ``A_c``.
        area_coefficient: ``a``, the extent-scaling coefficient.
        per_household_km: ``b``, the per-household service-drop length.
    """
    h = np.asarray(households, dtype=float)
    a = np.asarray(area_km2, dtype=float)
    backbone = float(area_coefficient) * np.sqrt(np.clip(h * a, 0.0, None))
    drops = float(per_household_km) * h
    return backbone + drops


def transformers_required(
    peak_demand_kw: float | np.ndarray,
    transformer_capacity_kva: float,
    power_factor: float = 0.9,
    spare_capacity_kva: float | np.ndarray = 0.0,
) -> np.ndarray:
    """Number of new distribution transformers needed by a settlement.

    ``C_xfmr`` in Equation 5 is incurred "where existing capacity is
    insufficient", so spare capacity on the nearest existing transformer is
    netted off the settlement's apparent-power requirement before sizing.
    """
    kva_required = np.asarray(peak_demand_kw, dtype=float) / max(float(power_factor), 1e-9)
    deficit = np.clip(kva_required - np.asarray(spare_capacity_kva, dtype=float), 0.0, None)
    return np.ceil(deficit / max(float(transformer_capacity_kva), 1e-9))
