import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

N = 5000

df = pd.DataFrame({
    "customer_id": range(1001, 1001 + N),
    "tenure_months": np.random.randint(1, 49, N),
    "monthly_charges": np.round(np.random.uniform(199, 2999, N), 2),
    "payment_failures_90d": np.random.poisson(0.5, N),
    "days_since_last_payment": np.random.randint(0, 61, N),
    "support_tickets_90d": np.random.poisson(1.2, N),
    "usage_sessions_30d": np.random.poisson(25, N),
    "plan_type": np.random.choice(
        ["Basic", "Standard", "Premium"],
        N,
        p=[0.4, 0.4, 0.2]
    ),
    "discount_used": np.random.choice([0, 1], N, p=[0.65, 0.35]),
    "renewal_count": np.random.randint(0, 13, N),
    "auto_renew": np.random.choice([0, 1], N, p=[0.3, 0.7]),
    "late_payment_count": np.random.poisson(0.7, N)
})

log_odds = (
    -2.0
    - 0.035 * df["tenure_months"]
    + 0.65 * df["payment_failures_90d"]
    + 0.035 * df["days_since_last_payment"]
    + 0.35 * df["support_tickets_90d"]
    - 0.035 * df["usage_sessions_30d"]
    - 0.45 * df["auto_renew"]
    + 0.40 * df["late_payment_count"]
    - 0.025 * df["renewal_count"]
    + 0.30 * df["discount_used"]
)

probabilities = 1 / (1 + np.exp(-log_odds))

df["churn"] = np.random.binomial(1, probabilities)

output_path = Path(__file__).resolve().parents[1] / "data"
output_path.mkdir(parents=True, exist_ok=True)

df.to_csv(output_path / "churn_dataset.csv", index=False)

print("\nDATASET GENERATED SUCCESSFULLY!")
print("Total records:", len(df))
print("Total columns:", len(df.columns))
print("\nChurn distribution:")
print(df["churn"].value_counts())
print("\nChurn percentage:")
print(round(df["churn"].mean() * 100, 2), "%")
print("\nDataset preview:")
print(df.head())
print("\nSaved at:", output_path / "churn_dataset.csv")
