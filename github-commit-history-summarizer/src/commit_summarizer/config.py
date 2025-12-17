"""Configuration file handling."""

from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager for the commit summarizer."""

    def __init__(self, config_path: Path):
        """Initialize configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self._data = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load and parse the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Configuration file is empty")

        return data

    @property
    def repositories(self) -> list[str]:
        """Get the list of repositories to summarize."""
        repos = self._data.get("repositories", [])
        if not repos:
            raise ValueError("No repositories specified in configuration")
        return repos

    @property
    def output_dir(self) -> Path:
        """Get the output directory path."""
        output_dir = self._data.get("output_dir", "./summaries")
        return Path(output_dir)
