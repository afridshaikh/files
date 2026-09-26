from pathlib import Path
from typing import Union
import yaml


def load_config(path: Union[str, Path]) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
