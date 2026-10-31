import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "churn_dataset.csv"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

X = df.drop(columns=["customer_id", "churn"])
y = df["churn"]

numeric_features = [
    "tenure_months",
    "monthly_charges",
    "payment_failures_90d",
    "days_since_last_payment",
    "support_tickets_90d",
    "usage_sessions_30d",
    "discount_used",
    "renewal_count",
    "auto_renew",
    "late_payment_count"
]

categorical_features = ["plan_type"]

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer(transformers=[
    ("numeric", numeric_transformer, numeric_features),
    ("categorical", categorical_transformer, categorical_features)
])

classifier = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", classifier)
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training started...")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "precision": precision_score(y_test, y_pred, zero_division=0),
    "recall": recall_score(y_test, y_pred, zero_division=0),
    "f1_score": f1_score(y_test, y_pred, zero_division=0),
    "roc_auc": roc_auc_score(y_test, y_prob)
}

print("\n========== MODEL PERFORMANCE ==========")

for name, value in metrics.items():
    print(f"{name.upper()}: {value:.4f}")

print("\n========== CLASSIFICATION REPORT ==========")
print(classification_report(y_test, y_pred, zero_division=0))

print("\n========== CONFUSION MATRIX ==========")
print(confusion_matrix(y_test, y_pred))

# Save trained pipeline
joblib.dump(model, MODEL_DIR / "churn_model.pkl")

# Save evaluation metrics
pd.DataFrame([metrics]).to_csv(
    MODEL_DIR / "model_metrics.csv",
    index=False
)

# Extract feature importance
preprocessor_fitted = model.named_steps["preprocessor"]
classifier_fitted = model.named_steps["classifier"]

feature_names = preprocessor_fitted.get_feature_names_out()
importance = classifier_fitted.feature_importances_

importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importance
}).sort_values(by="importance", ascending=False)

importance_df.to_csv(
    MODEL_DIR / "feature_importance.csv",
    index=False
)

print("\n========== TOP 10 IMPORTANT FEATURES ==========")
print(importance_df.head(10).to_string(index=False))

print("\nModel saved:", MODEL_DIR / "churn_model.pkl")
print("Metrics saved:", MODEL_DIR / "model_metrics.csv")
print("Feature importance saved:", MODEL_DIR / "feature_importance.csv")
