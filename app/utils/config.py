"""Helpers for locating the repository root and loading YAML configuration."""

from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_yaml(relative_path: str) -> dict:
    """Load a YAML file stored relative to the repository root."""
    with (ROOT_DIR / relative_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
