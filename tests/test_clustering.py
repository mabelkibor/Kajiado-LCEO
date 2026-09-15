"""Equation 2 — DBSCAN clustering, the relaxed pass, and typology assignment."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.clustering.dbscan import (
    NOISE_LABEL,
    cluster_buildings,
    micro_cluster_noise,
    summarise_clusters,
)
from kajiado_lceo.clustering.typology import assign_typology


def _prepare(buildings: pd.DataFrame) -> pd.DataFrame:
    df = buildings.copy()
    df["households"] = 1.0
    df["distance_to_mv_km"] = 1.0
    df["distance_to_lv_km"] = 2.0
    return df


def test_tight_group_forms_a_single_cluster(config, toy_buildings):
    out = cluster_buildings(_prepare(toy_buildings), config)
    tight = out.iloc[:12]
    labels = set(tight["cluster_label"])
    assert labels != {NOISE_LABEL}
    assert len(labels) == 1, "a 12-dwelling village core must not fragment"


def test_isolated_building_is_labelled_noise(config, toy_buildings):
    out = cluster_buildings(_prepare(toy_buildings), config)
    assert out.iloc[-1]["cluster_label"] == NOISE_LABEL


def test_loose_pair_is_noise_at_primary_eps(config, toy_buildings):
    # ~350 m apart: outside the 50-100 m primary radius.
    out = cluster_buildings(_prepare(toy_buildings), config)
    assert (out.iloc[12:14]["cluster_label"] == NOISE_LABEL).all()


def test_relaxed_pass_recovers_the_loose_pair_as_a_micro_cluster(config, toy_buildings):
    out = micro_cluster_noise(cluster_buildings(_prepare(toy_buildings), config), config)
    pair = out.iloc[12:14]
    assert (pair["micro_cluster_label"] >= 0).all()
    assert pair["settlement_id"].nunique() == 1
    assert pair["settlement_id"].iloc[0].startswith("M")


def test_isolated_homestead_stays_its_own_settlement(config, toy_buildings):
    out = micro_cluster_noise(cluster_buildings(_prepare(toy_buildings), config), config)
    isolated = out.iloc[-1]
    assert isolated["micro_cluster_label"] == NOISE_LABEL
    assert isolated["settlement_id"].startswith("D")
    assert isolated["is_dispersed"]


def test_noise_points_are_never_discarded(config, toy_buildings):
    prepared = _prepare(toy_buildings)
    out = micro_cluster_noise(cluster_buildings(prepared, config), config)
    assert len(out) == len(prepared), "Section 3.5.3: noise points are carried forward"
    assert out["settlement_id"].notna().all()


def test_smaller_eps_produces_more_noise(config, sample_layers):
    prepared = _prepare(sample_layers["buildings"])
    tight = cluster_buildings(prepared, config, eps_m=25.0)
    loose = cluster_buildings(prepared, config, eps_m=150.0)
    assert (tight["cluster_label"] == NOISE_LABEL).sum() > (
        loose["cluster_label"] == NOISE_LABEL
    ).sum()


def test_summarise_preserves_the_household_total(config, toy_buildings):
    prepared = _prepare(toy_buildings)
    clustered = micro_cluster_noise(cluster_buildings(prepared, config), config)
    settlements = summarise_clusters(clustered, config)
    assert settlements["households"].sum() == prepared["households"].sum()
    assert settlements["n_buildings"].sum() == len(prepared)


def test_settlement_distance_is_the_nearest_member_building(config, toy_buildings):
    prepared = _prepare(toy_buildings)
    prepared.loc[prepared.index[:12], "distance_to_mv_km"] = np.linspace(5.0, 15.0, 12)
    clustered = micro_cluster_noise(cluster_buildings(prepared, config), config)
    settlements = summarise_clusters(clustered, config)
    village = settlements[settlements["n_buildings"] == 12].iloc[0]
    assert village["distance_to_mv_km"] == 5.0


def test_typology_thresholds(config):
    settlements = pd.DataFrame(
        {
            "settlement_id": ["a", "b", "c", "d"],
            "households": [1.0, 20.0, 200.0, 900.0],
            "density_bldg_per_km2": [10.0, 50.0, 100.0, 1200.0],
        }
    )
    out = assign_typology(settlements, config)
    assert list(out["typology"]) == ["dispersed", "small_rural", "large_rural", "peri_urban"]


def test_high_density_overrides_household_count(config):
    # A small but very dense cluster on the peri-urban fringe is peri-urban.
    settlements = pd.DataFrame(
        {"settlement_id": ["x"], "households": [30.0], "density_bldg_per_km2": [2000.0]}
    )
    assert assign_typology(settlements, config)["typology"].iloc[0] == "peri_urban"
