import os
from typing import Iterable, Dict, Any, List, Tuple
import pandas as pd

# ???: path -> (kind, model, expected_feature_names or None)
_MODEL_CACHE: dict[str, Tuple[str, object, List[str] | None]] = {}

class CatBoostDetector:
    name = "model_generic"

    def __init__(self, path: str):
        self.model_path = path

    def load(self):
        if self.model_path in _MODEL_CACHE:
            return
        ext = (self.model_path or "").lower()
        if ext.endswith(".cbm"):
            from catboost import CatBoostClassifier
            m = CatBoostClassifier()
            m.load_model(self.model_path)
            # ???? ?????? ????? ???????? ????????
            expected = None
            try:
                # ??? ????????? ?????? feature_names_
                expected = list(getattr(m, "feature_names_", None) or []) or None
            except Exception:
                expected = None
            _MODEL_CACHE[self.model_path] = ("cb", m, expected)
        elif ext.endswith(".pkl"):
            import joblib
            m = joblib.load(self.model_path)
            # Pipelines ?? ?????? ??????? ?? ???????? ??? ????? expected
            _MODEL_CACHE[self.model_path] = ("sk", m, None)
        else:
            raise RuntimeError(f"Unsupported model type: {self.model_path}")

    def _align_features(self, X: pd.DataFrame, expected: List[str] | None) -> pd.DataFrame:
        # ???? ????? bool ??? int ????? NaN
        for col in X.columns:
            if X[col].dtype == "bool":
                X[col] = X[col].astype(int)
        X = X.fillna(0)

        if expected:
            # reindex: ???? ??????? ???????? ???????? ????? ??????? ????? ????? ???????
            X = X.reindex(columns=expected, fill_value=0)
        return X

    def infer(self, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.model_path not in _MODEL_CACHE:
            self.load()

        kind, model, expected = _MODEL_CACHE[self.model_path]
        batch = list(rows)
        if not batch:
            return []

        X = pd.DataFrame(batch)
        if "user_id" not in X.columns:
            raise RuntimeError("feature rows must include 'user_id'")

        user_ids = X["user_id"].tolist()
        X = X.drop(columns=["user_id"])

        # ?????? ??????? ????? ?????? ??????? (?? ?????)
        X = self._align_features(X, expected)

        # inference
        if kind == "cb":
            probs = model.predict_proba(X)[:, 1]
        else:  # sklearn pipeline
            probs = model.predict_proba(X)[:, 1]

        out = []
        for uid, p in zip(user_ids, probs):
            p = float(p)
            risk = round(100 * (0.7 * p + 0.3), 2)
            out.append({
                "user_id": int(uid),
                "score": p,
                "risk": risk,
                "confidence": 0.8,
                "evidence": {
                    "features_used": list(X.columns),
                    "model_path": self.model_path
                }
            })
        return out
