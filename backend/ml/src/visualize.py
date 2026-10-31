import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "churn_dataset.csv"
IMPORTANCE_PATH = BASE_DIR / "models" / "feature_importance.csv"
OUTPUT_DIR = BASE_DIR / "models"

df = pd.read_csv(DATA_PATH)
importance = pd.read_csv(IMPORTANCE_PATH)

sns.set_theme(style="whitegrid")

# Churn distribution
plt.figure(figsize=(7, 5))
sns.countplot(data=df, x="churn")
plt.title("Customer Churn Distribution")
plt.xlabel("Churn (0 = Retained, 1 = Churned)")
plt.ylabel("Number of Customers")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "churn_distribution.png")
plt.close()

# Feature importance
plt.figure(figsize=(9, 6))
sns.barplot(
    data=importance.head(10),
    x="importance",
    y="feature"
)
plt.title("Top 10 Churn Prediction Features")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "feature_importance.png")
plt.close()

# Payment failures vs churn
plt.figure(figsize=(8, 5))
sns.barplot(
    data=df,
    x="payment_failures_90d",
    y="churn"
)
plt.title("Payment Failures vs Churn Rate")
plt.xlabel("Payment Failures in Last 90 Days")
plt.ylabel("Churn Rate")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "payment_failures_vs_churn.png")
plt.close()

print("All visualizations saved successfully!")
