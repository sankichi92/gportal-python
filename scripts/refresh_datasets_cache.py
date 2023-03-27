import json
from pathlib import Path

import gportal

target_path = Path(__file__).parent / "../gportal/data/datasets.json"

with target_path.open("w") as f:
    json.dump(gportal.datasets(), f, separators=(",", ":"))
