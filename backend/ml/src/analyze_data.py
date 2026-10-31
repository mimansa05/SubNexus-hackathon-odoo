import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "churn_dataset.csv"

df = pd.read_csv(DATA_PATH)

print("\n========== DATASET INFORMATION ==========")
print(df.info())

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== STATISTICAL SUMMARY ==========")
print(df.describe())

print("\n========== CHURN DISTRIBUTION ==========")
print(df["churn"].value_counts())

print("\n========== CHURN PERCENTAGE ==========")
print(df["churn"].value_counts(normalize=True) * 100)

print("\n========== PLAN-WISE CHURN ==========")
print(df.groupby("plan_type")["churn"].mean() * 100)

print("\n========== HIGH PAYMENT FAILURE CUSTOMERS ==========")
print(
    df.groupby("payment_failures_90d")["churn"].mean() * 100
)
