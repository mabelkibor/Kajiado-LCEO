"""Configuration loading: YAML includes, deep merge, scenario overlays.

The model reads every parameter from ``config/``. Nothing numeric is hard-coded
in the modelling modules, so a run is fully described by (config files, scenario
id, input data). :func:`load_config` resolves the include list in
``config/default.yaml``, deep-merges each component file, then overlays the
requested scenario.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path("config")
DEFAULT_CONFIG_FILE = "default.yaml"
_MISSING = object()


def deep_merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto ``base`` without mutating either.

    Mappings are merged key-by-key; every other type (including lists) is
    replaced wholesale, so a scenario that redefines a list replaces it rather
    than appending to it.
    """
    merged = dict(copy.deepcopy(base))
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"configuration file must contain a mapping at top level: {path}")
    return data


@dataclass(frozen=True)
class Config:
    """Immutable view over the merged configuration tree.

    Values are addressed with dotted paths so that call sites read like the
    YAML they come from::

        cfg.get("technologies.grid.cost_mv_per_km")
        cfg.require("finance.discount_rate")
    """

    data: dict[str, Any] = field(default_factory=dict)
    sources: tuple[Path, ...] = ()
    scenario: str = "baseline"
    root: Path = Path()

    # -- access ----------------------------------------------------------
    def get(self, path: str, default: Any = None) -> Any:
        """Return the value at a dotted ``path``, or ``default`` if absent."""
        node: Any = self.data
        for part in path.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def require(self, path: str) -> Any:
        """Return the value at a dotted ``path`` or raise :class:`KeyError`."""
        value = self.get(path, _MISSING)
        if value is _MISSING:
            raise KeyError(
                f"required configuration key '{path}' is missing "
                f"(loaded from: {', '.join(str(s) for s in self.sources)})"
            )
        return value

    def section(self, path: str) -> dict[str, Any]:
        """Return a mapping section as a plain dict (empty if absent)."""
        value = self.get(path, {})
        return dict(value) if isinstance(value, Mapping) else {}

    def with_overrides(self, overrides: Mapping[str, Any]) -> Config:
        """Return a copy with ``overrides`` (a nested mapping) merged in."""
        return Config(
            data=deep_merge(self.data, overrides),
            sources=self.sources,
            scenario=self.scenario,
            root=self.root,
        )

    def with_override_path(self, path: str, value: Any) -> Config:
        """Return a copy with a single dotted ``path`` set to ``value``.

        Used by the sensitivity sweep, which addresses parameters by path.
        """
        nested: dict[str, Any] = {}
        node = nested
        parts = path.split(".")
        for part in parts[:-1]:
            node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        return self.with_overrides(nested)

    # -- paths -----------------------------------------------------------
    def path(self, key: str) -> Path:
        """Resolve a ``paths.*`` entry against the project root."""
        return (self.root / str(self.require(f"paths.{key}"))).resolve()

    def input_path(self, key: str) -> Path:
        """Resolve an ``inputs.*`` entry against the project data directory."""
        value = Path(str(self.require(f"inputs.{key}")))
        if value.is_absolute():
            return value
        return (self.root / "data" / value).resolve()

    def output_path(self, key: str) -> Path:
        """Resolve an ``outputs_spec.*`` entry against ``paths.outputs``."""
        value = Path(str(self.require(f"outputs_spec.{key}")))
        if value.is_absolute():
            return value
        return (self.path("outputs") / value).resolve()


def load_config(
    config_dir: str | Path = DEFAULT_CONFIG_DIR,
    scenario: str | None = None,
    overrides: Mapping[str, Any] | None = None,
    root: str | Path | None = None,
) -> Config:
    """Load the merged configuration.

    Args:
        config_dir: directory holding ``default.yaml`` and the component files.
        scenario: scenario id; resolves to ``config/scenarios/<id>.yaml``.
            Defaults to ``run.scenario`` in ``default.yaml``.
        overrides: nested mapping merged last, after the scenario.
        root: project root that relative ``paths.*`` entries resolve against.
            Defaults to the parent of ``config_dir``.

    Returns:
        A :class:`Config` carrying the merged tree and its provenance.
    """
    config_dir = Path(config_dir)
    project_root = Path(root) if root is not None else config_dir.parent
    base_file = config_dir / DEFAULT_CONFIG_FILE

    data = _read_yaml(base_file)
    sources: list[Path] = [base_file]

    for include in _as_list(data.pop("include", [])):
        include_path = config_dir / str(include)
        data = deep_merge(data, _read_yaml(include_path))
        sources.append(include_path)

    scenario_id = scenario or str(data.get("run", {}).get("scenario", "baseline"))
    scenario_file = config_dir / "scenarios" / f"{scenario_id}.yaml"
    if scenario_file.is_file():
        data = deep_merge(data, _read_yaml(scenario_file))
        sources.append(scenario_file)
    elif scenario is not None:
        raise FileNotFoundError(
            f"scenario '{scenario_id}' not found at {scenario_file}. "
            f"Available: {', '.join(sorted(p.stem for p in (config_dir / 'scenarios').glob('*.yaml')))}"
        )

    if overrides:
        data = deep_merge(data, overrides)

    data.setdefault("run", {})["scenario"] = scenario_id
    return Config(
        data=data,
        sources=tuple(sources),
        scenario=scenario_id,
        root=project_root if project_root != Path() else Path(),
    )


def _as_list(value: Any) -> Iterable[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return value
    return [value]
