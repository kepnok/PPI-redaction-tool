import yaml
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    """Class to manage loading and accessing configuration from YAML files."""
    
    def __init__(self, config_path: str = "config/presidio_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    @property
    def analyzer_config(self) -> Dict[str, Any]:
        return self.config.get("analyzer", {})

    @property
    def anonymizer_config(self) -> Dict[str, Any]:
        return self.config.get("anonymizer", {})
