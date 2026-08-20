import os
import joblib
import pandas as pd

from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

from sklearn.utils.class_weight import compute_sample_weight


# ============================================================
# TRAFFICX - XGBOOST BASELINE
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_dataset.csv"
)

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v1.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_END = 499
VALIDATION_END = 599
TEST_END = 699


FEATURES = [
    "road_length_m",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m"
]


TARGET = "future_congestion"


LABELS = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}


REVERSE_LABELS = {
    value: key
    for key, value in LABELS.items()
}


# ============================================================
# HEADER
# ============================================================

print("\n========================================")
print(" TRAFFICX - XGBOOST BASELINE")
print("========================================")

print("\nPrediction:")
print("Current traffic → Future congestion")
print("Horizon         → 5 minutes")


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df):,}"
)


# ============================================================
# ENCODE TARGET
# ============================================================

df["target"] = (
    df[TARGET]
    .map(LABELS)
)


if df["target"].isna().any():

    raise ValueError(
        "Unknown target class detected."
    )


# ============================================================
# TEMPORAL SPLIT
# ============================================================

train_df = df[
    df["step"] <= TRAIN_END
].copy()


validation_df = df[
    (df["step"] > TRAIN_END) &
    (df["step"] <= VALIDATION_END)
].copy()


test_df = df[
    (df["step"] > VALIDATION_END) &
    (df["step"] <= TEST_END)
].copy()


print("\n========================================")
print(" TEMPORAL SPLIT")
print("========================================")

print(
    f"TRAIN      : "
    f"steps 0-{TRAIN_END} "
    f"→ {len(train_df):,} rows"
)

print(
    f"VALIDATION : "
    f"steps {TRAIN_END + 1}-{VALIDATION_END} "
    f"→ {len(validation_df):,} rows"
)

print(
    f"TEST       : "
    f"steps {VALIDATION_END + 1}-{TEST_END} "
    f"→ {len(test_df):,} rows"
)


# ============================================================
# FEATURE MATRICES
# ============================================================

X_train = train_df[FEATURES]

y_train = train_df["target"]


X_validation = validation_df[FEATURES]

y_validation = validation_df["target"]


X_test = test_df[FEATURES]

y_test = test_df["target"]


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("\n========================================")
print(" TRAINING CLASS DISTRIBUTION")
print("========================================")

print(
    train_df[TARGET]
    .value_counts()
)

print("\nPercentage:")

print(
    train_df[TARGET]
    .value_counts(
        normalize=True
    )
    .mul(100)
    .round(2)
)


# ============================================================
# SAMPLE WEIGHTS
# ============================================================

print("\nCalculating class-balanced weights...")

sample_weights = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)


# ============================================================
# CREATE MODEL
# ============================================================

print("\nCreating XGBoost model...")

model = XGBClassifier(

    objective="multi:softprob",

    num_class=4,

    n_estimators=400,

    max_depth=8,

    learning_rate=0.08,

    subsample=0.85,

    colsample_bytree=0.85,

    min_child_weight=3,

    gamma=0.1,

    reg_alpha=0.05,

    reg_lambda=1.0,

    tree_method="hist",

    eval_metric="mlogloss",

    random_state=42,

    n_jobs=-1

)


# ============================================================
# TRAIN
# ============================================================

print("\n========================================")
print(" TRAINING XGBOOST")
print("========================================")

model.fit(

    X_train,

    y_train,

    sample_weight=sample_weights,

    eval_set=[
        (
            X_validation,
            y_validation
        )
    ],

    verbose=True
)


# ============================================================
# VALIDATION
# ============================================================

print("\n========================================")
print(" VALIDATION")
print("========================================")


validation_predictions = model.predict(
    X_validation
)


validation_accuracy = accuracy_score(
    y_validation,
    validation_predictions
)


validation_f1 = f1_score(
    y_validation,
    validation_predictions,
    average="macro"
)


print(
    f"Validation Accuracy : "
    f"{validation_accuracy:.4f}"
)

print(
    f"Validation Macro F1 : "
    f"{validation_f1:.4f}"
)


# ============================================================
# TEST
# ============================================================

print("\n========================================")
print(" FINAL TEST")
print("========================================")


test_predictions = model.predict(
    X_test
)


test_accuracy = accuracy_score(
    y_test,
    test_predictions
)


test_macro_f1 = f1_score(
    y_test,
    test_predictions,
    average="macro"
)


test_weighted_f1 = f1_score(
    y_test,
    test_predictions,
    average="weighted"
)


print(
    f"Test Accuracy     : "
    f"{test_accuracy:.4f}"
)

print(
    f"Test Macro F1     : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Test Weighted F1  : "
    f"{test_weighted_f1:.4f}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print(" CLASSIFICATION REPORT")
print("========================================")


print(
    classification_report(
        y_test,
        test_predictions,
        target_names=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CONGESTED"
        ],
        digits=4
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n========================================")
print(" CONFUSION MATRIX")
print("========================================")


cm = confusion_matrix(
    y_test,
    test_predictions
)


print(
    "                 Predicted"
)

print(
    "             LOW MED HIGH CONG"
)

for i, row in enumerate(cm):

    print(
        f"{REVERSE_LABELS[i]:10s}"
        f"{row[0]:6d}"
        f"{row[1]:6d}"
        f"{row[2]:6d}"
        f"{row[3]:6d}"
    )


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n========================================")
print(" FEATURE IMPORTANCE")
print("========================================")


importance = pd.DataFrame({

    "feature": FEATURES,

    "importance": model.feature_importances_

})


importance = importance.sort_values(
    "importance",
    ascending=False
)


print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


model.save_model(
    MODEL_FILE
)


print("\n========================================")
print(" MODEL SAVED")
print("========================================")

print(
    f"Model: {MODEL_FILE}"
)

print("\n========================================")
print(" TRAFFICX XGBOOST V1 COMPLETE")
print("========================================")