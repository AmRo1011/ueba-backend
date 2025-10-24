import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelPath:
    name: str
    path: str
    kind: str  # "cbm" ?? "pkl"

def _exists(p: Optional[str]) -> bool:
    return bool(p) and os.path.exists(p) and os.path.isfile(p)

def pick_insider() -> Optional[ModelPath]:
    cbm = os.getenv("MODEL_INSIDER_CBM", "models/insider_catboost.cbm")
    pkl = os.getenv("MODEL_INSIDER_PKL", "models/insider_catboost.pkl")
    if _exists(cbm):
        return ModelPath("model_insider", cbm, "cbm")
    if _exists(pkl):
        return ModelPath("model_insider", pkl, "pkl")
    return None

def pick_ueba() -> Optional[ModelPath]:
    cbm = os.getenv("MODEL_UEBA_CBM", "models/ueba_catboost_model.cbm")
    if _exists(cbm):
        return ModelPath("model_ueba", cbm, "cbm")
    return None
