from __future__ import annotations

import os
from functools import lru_cache

from smart_categorization.core.pipeline import SmartCategorizationPipeline


def _default_data_dir() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, "..", ".data")


@lru_cache(maxsize=1)
def get_pipeline() -> SmartCategorizationPipeline:
    data_dir = os.getenv("CATEGORIZER_DATA_DIR", _default_data_dir())
    os.makedirs(data_dir, exist_ok=True)

    feedback_path = os.getenv(
        "CATEGORIZER_FEEDBACK_PATH", os.path.join(data_dir, "feedback_store.json")
    )
    model_path = os.getenv(
        "CATEGORIZER_MODEL_PATH", os.path.join(data_dir, "cat_model.pkl")
    )
    custom_cat_path = os.getenv(
        "CUSTOM_CATEGORIES_PATH", os.path.join(data_dir, "custom_categories.json")
    )

    return SmartCategorizationPipeline(
        feedback_path=feedback_path, model_path=model_path, custom_cat_path=custom_cat_path
    )

