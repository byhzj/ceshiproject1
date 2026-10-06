import yaml
from pathlib import Path

def load_yaml(rel_path: str):
    root = Path(__file__).resolve().parent.parent
    p = root / rel_path
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)