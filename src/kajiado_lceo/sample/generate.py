"""Generate a synthetic Kajiado-like county for testing and demonstration.

The real inputs of Table 3.2 include KPLC and REREC network and meter data,
which are obtained under a data-sharing agreement and are not redistributable
(see docs/ETHICS_AND_DATA_GOVERNANCE.md). Without a substitute, nobody could run
this repository — so this module fabricates a county with the *structural*
properties the model must handle:

* a dense peri-urban corridor in the north (Kitengela/Ngong analogue) sitting on
  the existing MV network;
* mid-sized rural villages at varying distance from that network;
* dispersed pastoralist homesteads in the southern rangelands, which should fall
  out of Equation 2 as noise and exercise the Equation 10 override;
* ancillary structures inside homestead compounds, which the Table 3.3 filter
  must remove before household counts are taken.

The data is synthetic. It is fit for testing code paths and for demonstrating
the workflow; it is not fit for any statement about Kajiado County.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Approximate bounding box of Kajiado County, used only to place synthetic
# points in a plausible coordinate range.
LAT_RANGE = (-3.10, -1.30)
LON_RANGE = (36.10, 37.85)


def generate_sample_county(seed: int = 42) -> dict[str, pd.DataFrame | np.ndarray]:
    """Build a synthetic county. Returns the same layer dict as ``load_inputs``."""
    rng = np.random.default_rng(seed)

    buildings: list[dict] = []
    building_index = 0

    def add_structure(lat: float, lon: float, area: float, kind: str) -> None:
        nonlocal building_index
        # Perimeter is derived from area with a shape factor that separates
        # compact dwellings from elongated or irregular enclosures, so the
        # compactness criterion of Table 3.3 has something real to act on.
        shape_factor = 4.2 if kind == "dwelling" else 7.5
        buildings.append(
            {
                "building_id": f"B{building_index:08d}",
                "latitude": lat,
                "longitude": lon,
                "area_m2": area,
                "perimeter_m": shape_factor * np.sqrt(max(area, 1.0)),
                "structure_kind": kind,
            }
        )
        building_index += 1

    # --- peri-urban corridor: dense, on-grid, high demand ---------------
    # Two dense corridors. Meter coverage below is partial, so a share of these
    # dwellings remains unelectrified and exercises the peri-urban typology.
    for centre_lat, centre_lon, count in [(-1.47, 36.96, 900), (-1.36, 36.66, 700)]:
        lat = centre_lat + rng.normal(0, 0.006, count)
        lon = centre_lon + rng.normal(0, 0.006, count)
        area = rng.lognormal(mean=np.log(70), sigma=0.45, size=count)
        for i in range(count):
            add_structure(lat[i], lon[i], float(area[i]), "dwelling")

    # --- rural villages: mid-sized clusters at varying grid distance ----
    # Spread is deliberately tight (sigma ~ 200-300 m) so that a village core
    # satisfies the density condition of Equation 2 at eps = 75 m, as a real
    # nucleated settlement does. Distances to the MV corridor vary from a few
    # hundred metres to tens of kilometres, which is what makes the grid /
    # off-grid crossover visible in the results.
    village_centres = [
        (-1.845, 36.795, 220, 0.0022),  # close to the Kajiado town spur
        (-2.105, 36.905, 140, 0.0020),  # near the southern MV terminus
        (-2.350, 37.250, 90, 0.0018),  # remote east
        (-1.980, 37.420, 110, 0.0020),  # on the eastern spur
        (-2.620, 37.100, 70, 0.0016),  # deep south, far from any line
        (-2.200, 36.450, 60, 0.0016),  # far west
    ]
    for centre_lat, centre_lon, count, spread in village_centres:
        lat = centre_lat + rng.normal(0, spread, count)
        lon = centre_lon + rng.normal(0, spread, count)
        area = rng.lognormal(mean=np.log(45), sigma=0.40, size=count)
        for i in range(count):
            add_structure(lat[i], lon[i], float(area[i]), "dwelling")
            # Each rural dwelling has ancillary structures nearby: a store and,
            # for some, a livestock enclosure. These must not be counted as
            # households (Section 3.4.3).
            if rng.random() < 0.7:
                add_structure(
                    lat[i] + rng.normal(0, 8e-5),
                    lon[i] + rng.normal(0, 8e-5),
                    float(rng.uniform(3.0, 6.5)),
                    "store",
                )
            if rng.random() < 0.4:
                add_structure(
                    lat[i] + rng.normal(0, 1.2e-4),
                    lon[i] + rng.normal(0, 1.2e-4),
                    float(rng.uniform(40.0, 160.0)),
                    "enclosure",
                )

    # --- dispersed pastoralist homesteads in the southern rangelands ----
    n_homesteads = 260
    lat = rng.uniform(-3.05, -2.30, n_homesteads)
    lon = rng.uniform(36.30, 37.70, n_homesteads)
    for i in range(n_homesteads):
        dwellings = rng.integers(1, 3)
        for _ in range(int(dwellings)):
            add_structure(
                lat[i] + rng.normal(0, 6e-5),
                lon[i] + rng.normal(0, 6e-5),
                float(rng.uniform(18.0, 55.0)),
                "dwelling",
            )
        for _ in range(int(rng.integers(1, 4))):
            add_structure(
                lat[i] + rng.normal(0, 1.0e-4),
                lon[i] + rng.normal(0, 1.0e-4),
                float(rng.uniform(2.5, 6.0)),
                "store",
            )

    buildings_df = pd.DataFrame(buildings)
    buildings_df["terrain_class"] = np.where(buildings_df["latitude"] > -1.60, "undulating", "flat")

    # --- MV backbone: a northern corridor plus two southward spurs ------
    mv_lines = np.array(
        [
            [-1.33, 36.60, -1.50, 36.99],  # Ngong - Kitengela corridor
            [-1.50, 36.99, -1.88, 36.80],  # spur towards Kajiado town
            [-1.88, 36.80, -2.15, 36.93],  # continuation south
            [-1.95, 37.35, -2.05, 37.50],  # eastern spur
        ],
        dtype=float,
    )
    # LV reticulation exists only where the network has been built out.
    lv_lines = np.array(
        [
            [-1.46, 36.94, -1.48, 36.98],
            [-1.35, 36.64, -1.37, 36.68],
            [-1.86, 36.77, -1.87, 36.79],
        ],
        dtype=float,
    )

    transformers = pd.DataFrame(
        {
            "transformer_id": [f"T{i:04d}" for i in range(6)],
            "latitude": [-1.47, -1.36, -1.86, -2.12, -1.99, -2.34],
            "longitude": [36.96, 36.66, 36.78, 36.91, 37.43, 37.24],
            "capacity_kva": [200.0, 200.0, 100.0, 50.0, 50.0, 50.0],
            "spare_capacity_kva": [40.0, 25.0, 10.0, 0.0, 0.0, 0.0],
        }
    )

    # Meters: existing connections concentrated in the peri-urban corridor.
    n_meters = 600
    meters = pd.DataFrame(
        {
            "meter_id": [f"M{i:06d}" for i in range(n_meters)],
            "latitude": np.concatenate(
                [
                    -1.47 + rng.normal(0, 0.010, n_meters // 2),
                    -1.36 + rng.normal(0, 0.010, n_meters - n_meters // 2),
                ]
            ),
            "longitude": np.concatenate(
                [
                    36.96 + rng.normal(0, 0.010, n_meters // 2),
                    36.66 + rng.normal(0, 0.010, n_meters - n_meters // 2),
                ]
            ),
        }
    )

    return {
        "buildings": buildings_df,
        "mv_lines": mv_lines,
        "lv_lines": lv_lines,
        "transformers": transformers,
        "meters": meters,
    }


def write_sample_data(output_dir: str | Path, seed: int = 42) -> dict[str, Path]:
    """Write the synthetic county to CSV at the paths the config expects."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    layers = generate_sample_county(seed=seed)

    paths: dict[str, Path] = {}
    written = {
        "building_footprints": layers["buildings"],
        "transformers": layers["transformers"],
        "meters": layers["meters"],
        "mv_lines": pd.DataFrame(layers["mv_lines"], columns=["lat1", "lon1", "lat2", "lon2"]),
        "lv_lines": pd.DataFrame(layers["lv_lines"], columns=["lat1", "lon1", "lat2", "lon2"]),
    }
    for name, frame in written.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths
