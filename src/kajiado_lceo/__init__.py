"""GIS-aided techno-economic modelling of least-cost electrification pathways.

Reference implementation of the modelling framework specified in Chapter 3 of
*GIS-Aided Techno-Economic Modelling of Least Cost Electrification Pathways in
Kajiado County in Kenya* (M. C. Kibor, Strathmore University, 2026).

Equation numbers quoted throughout the package refer to Section 3.5.3 of the
proposal; see docs/METHODOLOGY.md for the full statement of each equation.
"""

__version__ = "0.1.0"
__author__ = "Mabel Chelagat Kibor"

from kajiado_lceo.config import Config, load_config

__all__ = ["Config", "__version__", "load_config"]
