import joblib
import pandas as pd

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "churn_model.pkl"

model = joblib.load(MODEL_PATH)

def predict_churn(customer_data):

    customer_df = pd.DataFrame([customer_data])

    probability = float(model.predict_proba(customer_df)[0][1])

    if probability >= 0.70:
        risk = "High"
        recommendation = "Offer a personalized retention plan or discount"

    elif probability >= 0.40:
        risk = "Medium"
        recommendation = "Send a renewal reminder and engagement offer"

    else:
        risk = "Low"
        recommendation = "Continue regular customer engagement"

    return {
        "churn_probability": round(probability, 4),
        "churn_percentage": round(probability * 100, 2),
        "risk_level": risk,
        "recommendation": recommendation
    }


if __name__ == "__main__":

    customer = {
        "tenure_months": 3,
        "monthly_charges": 1499,
        "payment_failures_90d": 3,
        "days_since_last_payment": 35,
        "support_tickets_90d": 4,
        "usage_sessions_30d": 5,
        "plan_type": "Basic",
        "discount_used": 0,
        "renewal_count": 0,
        "auto_renew": 0,
        "late_payment_count": 3
    }

    result = predict_churn(customer)

    print("\n========== CUSTOMER CHURN PREDICTION ==========")

    for key, value in result.items():
        print(f"{key}: {value}")
