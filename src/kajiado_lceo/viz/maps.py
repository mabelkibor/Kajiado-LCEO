"""Settlement maps.

A scatter map of settlement centroids, coloured by recommended technology and
sized by household count, over the MV network. This is a quick-look map for
checking results during development; publication cartography belongs in
QGIS, using the layer styles in ``qgis/styles/`` applied to the exported
settlement table (see qgis/README.md).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from kajiado_lceo.logging_setup import get_logger
from kajiado_lceo.viz.charts import TECHNOLOGY_COLOURS, TECHNOLOGY_LABELS

logger = get_logger(__name__)


def plot_settlement_map(
    settlements: pd.DataFrame,
    path: str | Path,
    mv_lines: np.ndarray | None = None,
    title: str = "Least-cost electrification technology by settlement",
) -> Path:
    """Plot settlement centroids coloured by recommended technology."""
    path = Path(path)
    fig, ax = plt.subplots(figsize=(8, 9))

    if mv_lines is not None and np.asarray(mv_lines).size:
        for lat1, lon1, lat2, lon2 in np.atleast_2d(mv_lines):
            ax.plot([lon1, lon2], [lat1, lat2], color="#444444", linewidth=1.1, alpha=0.8, zorder=1)
        ax.plot([], [], color="#444444", linewidth=1.1, label="Existing MV network")

    for technology, block in settlements.groupby("least_cost_technology"):
        ax.scatter(
            block["longitude"],
            block["latitude"],
            s=np.clip(block["households"].to_numpy(dtype=float) * 0.6, 6, 220),
            color=TECHNOLOGY_COLOURS.get(str(technology), "#777777"),
            alpha=0.7,
            edgecolors="none",
            zorder=2,
            label=TECHNOLOGY_LABELS.get(str(technology), str(technology)),
        )

    ax.set_xlabel("Longitude (deg E)")
    ax.set_ylabel("Latitude (deg N)")
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.2, linestyle=":")
    ax.legend(frameon=False, loc="lower left", fontsize=8)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("wrote map %s", path)
    return path
