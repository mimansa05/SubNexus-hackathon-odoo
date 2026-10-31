import joblib
import pandas as pd

from pathlib import Path
from functools import lru_cache

from fastapi import HTTPException

from app.schemas.churn import ChurnPredictionRequest


# backend/ml/models/churn_model.pkl
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "ml" / "models" / "churn_model.pkl"


@lru_cache(maxsize=1)
def load_churn_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Churn model not found at: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


def predict_customer_churn(data: ChurnPredictionRequest):

    try:
        model = load_churn_model()

        # Convert validated input into DataFrame
        customer_df = pd.DataFrame([data.model_dump()])

        # Predict probability
        probability = float(
            model.predict_proba(customer_df)[0][1]
        )

        # Initial business risk thresholds
        if probability >= 0.70:
            risk = "High"
            recommendation = (
                "Offer a personalized retention plan "
                "or investigate payment issues."
            )

        elif probability >= 0.40:
            risk = "Medium"
            recommendation = (
                "Send a renewal reminder and engagement offer."
            )

        else:
            risk = "Low"
            recommendation = (
                "Continue regular customer engagement."
            )

        return {
            "churn_probability": round(probability, 4),
            "churn_percentage": round(probability * 100, 2),
            "risk_level": risk,
            "recommendation": recommendation,
            "model_version": "random-forest-v1"
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Churn prediction failed."
        ) from exc
