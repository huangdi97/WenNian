"""Centralized configuration management with YAML loading and environment overrides.

Supports dot-notation key access (e.g., config.clocks.phenoage_weight)
and environment variable overrides prefixed with WENNIAN_.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import ConfigurationError


class AppConfig:
    """Singleton configuration container that combines YAML config
    with environment variable overrides.

    Environment variables take precedence over YAML values.
    Keys in environment variables use double-underscore as separator
    (e.g., WENNIAN_CLOCKS__PHENOAGE_WEIGHT=0.5).

    Attributes:
        _data: The raw configuration dictionary.
    """

    _instance: Optional["AppConfig"] = None
    _data: Dict[str, Any]

    def __new__(cls, *args: Any, **kwargs: Any) -> "AppConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[Path] = None) -> None:
        if "_loaded" in self.__dict__:
            return
        self.__dict__["_loaded"] = True
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
        self._data = self._load_yaml(config_path)
        self._apply_env_overrides()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load and parse the YAML configuration file.

        Args:
            path: Path to the YAML file.

        Returns:
            Parsed configuration dictionary.

        Raises:
            ConfigurationError: If the file cannot be read or parsed.
        """
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"YAML parse error in {path}: {e}") from e
        if not isinstance(data, dict):
            raise ConfigurationError(f"Configuration must be a mapping, got {type(data)}")
        return data

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the configuration.

        Variables with prefix WENNIAN_ are mapped to config keys,
        with __ acting as a nested separator.
        """
        prefix = "WENNIAN_"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix):].lower().replace("__", ".")
            self._set_nested(config_key, self._coerce_value(value))

    def _set_nested(self, key: str, value: Any) -> None:
        """Set a value in the configuration dictionary using dot-notation.

        Args:
            key: Dot-separated path (e.g., 'clocks.phenoage_weight').
            value: The value to set.
        """
        parts = key.split(".")
        d = self._data
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    @staticmethod
    def _coerce_value(raw: str) -> Any:
        """Attempt to coerce a string environment value to its native type.

        Args:
            raw: Raw string value from environment.

        Returns:
            Coerced value (bool, int, float, or original string).
        """
        lower = raw.lower()
        if lower in ("true", "yes", "1"):
            return True
        if lower in ("false", "no", "0"):
            return False
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        return raw

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value using dot-notation.

        Args:
            key: Dot-separated path (e.g., 'clocks.phenoage_weight').
            default: Value to return if the key is not found.

        Returns:
            The configuration value or default.
        """
        parts = key.split(".")
        node = self._data
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def __getattr__(self, name: str) -> Any:
        """Support attribute-style access to top-level config keys.

        Args:
            name: Top-level configuration key.

        Returns:
            The configuration subtree as a _ConfigProxy for further dot-access.

        Raises:
            AttributeError: If the key does not exist.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        _data = self.__dict__.get("_data", {})
        if name in _data:
            return _ConfigProxy(_data[name])
        raise AttributeError(f"'{type(self).__name__}' has no config key '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the raw configuration dictionary.

        Returns:
            Full configuration dictionary.
        """
        import copy
        return copy.deepcopy(self._data)  # noqa: S414 — intentional deep copy for safety


class _ConfigProxy:
    """Proxy object that enables recursive dot-notation access
    to nested configuration dictionaries.

    Args:
        data: The dictionary subtree to proxy.
    """

    def __init__(self, data: Any) -> None:
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if isinstance(data, dict) and name in data:
            value = data[name]
            return _ConfigProxy(value) if isinstance(value, dict) else value
        raise AttributeError(f"Config key '{name}' not found")

    def __repr__(self) -> str:
        return repr(object.__getattribute__(self, "_data"))


def load_config(env: str = "default") -> AppConfig:
    """Load configuration for the specified environment.

    Args:
        env: Environment name ('default', 'production', etc.).

    Returns:
        The singleton AppConfig instance.

    Raises:
        ConfigurationError: If the config file for the environment is not found.
    """
    config_dir = Path(__file__).parent.parent.parent / "config"
    config_path = config_dir / f"{env}.yaml"
    if not config_path.exists():
        config_path = config_dir / "default.yaml"
    if not config_path.exists():
        raise ConfigurationError(f"No configuration file found for env '{env}'")
    return AppConfig(config_path)
