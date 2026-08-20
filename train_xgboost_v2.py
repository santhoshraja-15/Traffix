import os
import json
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)
from sklearn.utils.class_weight import compute_sample_weight


# ============================================================
# TRAFFICX - XGBOOST V2
# TEMPORAL CONGESTION PREDICTION
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_v2_dataset.csv"
)

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_FILE = (
    os.path.join(
        MODEL_DIR,
        "trafficx_xgboost_v2.json"
    )
)

FEATURE_FILE = (
    os.path.join(
        MODEL_DIR,
        "trafficx_xgboost_v2_features.json"
    )
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


print("""
========================================
 TRAFFICX - XGBOOST V2
========================================

Prediction:
Current traffic + temporal trends
                ↓
        Future congestion

Horizon         → 5 minutes
========================================
""")


# ============================================================
# LOAD DATA
# ============================================================

print("Loading dataset...")

df = pd.read_csv(INPUT_FILE)

print(
    f"Rows loaded: {len(df):,}"
)


# ============================================================
# TARGET ENCODING
# ============================================================

label_map = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}

reverse_label_map = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH",
    3: "CONGESTED"
}

df["target"] = (
    df["future_congestion"]
    .map(label_map)
)


# ============================================================
# SORT BY TIME
# ============================================================

df = df.sort_values(
    ["step", "scenario", "road_id"]
).reset_index(drop=True)


# ============================================================
# TEMPORAL SPLIT
# ============================================================

print("""
========================================
 TEMPORAL SPLIT
========================================
""")

train = df[
    df["step"] < 500
].copy()

validation = df[
    (df["step"] >= 500) &
    (df["step"] < 600)
].copy()

test = df[
    df["step"] >= 600
].copy()


print(
    f"TRAIN      : steps 0-499 "
    f"→ {len(train):,} rows"
)

print(
    f"VALIDATION : steps 500-599 "
    f"→ {len(validation):,} rows"
)

print(
    f"TEST       : steps 600-699 "
    f"→ {len(test):,} rows"
)


# ============================================================
# FEATURES
# ============================================================

EXCLUDE_COLUMNS = [
    "scenario",
    "step",
    "road_id",
    "future_congestion",
    "target"
]

feature_columns = [
    col
    for col in df.columns
    if col not in EXCLUDE_COLUMNS
]


print("""
========================================
 FEATURES
========================================
""")

print(
    f"Number of features: "
    f"{len(feature_columns)}"
)

for feature in feature_columns:
    print(
        f"  - {feature}"
    )


# ============================================================
# PREPARE X / Y
# ============================================================

X_train = train[
    feature_columns
]

y_train = train[
    "target"
]

X_validation = validation[
    feature_columns
]

y_validation = validation[
    "target"
]

X_test = test[
    feature_columns
]

y_test = test[
    "target"
]


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("""
========================================
 TRAINING CLASS DISTRIBUTION
========================================
""")

train_distribution = (
    train["future_congestion"]
    .value_counts()
)

print(
    train_distribution
)

print("\nPercentage:")

print(
    (
        train_distribution /
        len(train) *
        100
    ).round(2)
)


# ============================================================
# CLASS-BALANCED SAMPLE WEIGHTS
# ============================================================

print("""
========================================
 CALCULATING CLASS WEIGHTS
========================================
""")

sample_weights = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)

print(
    "Balanced sample weights calculated."
)


# ============================================================
# CREATE MODEL
# ============================================================

print("""
========================================
 CREATING XGBOOST V2 MODEL
========================================
""")

model = XGBClassifier(

    objective="multi:softprob",

    num_class=4,

    n_estimators=500,

    learning_rate=0.05,

    max_depth=8,

    min_child_weight=3,

    subsample=0.85,

    colsample_bytree=0.85,

    gamma=0.1,

    reg_alpha=0.05,

    reg_lambda=1.0,

    eval_metric="mlogloss",

    tree_method="hist",

    random_state=42,

    n_jobs=-1
)


# ============================================================
# TRAIN
# ============================================================

print("""
========================================
 TRAINING XGBOOST V2
========================================
""")

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

print("""
========================================
 VALIDATION
========================================
""")

validation_predictions = (
    model.predict(
        X_validation
    )
)

validation_accuracy = (
    accuracy_score(
        y_validation,
        validation_predictions
    )
)

validation_macro_f1 = (
    f1_score(
        y_validation,
        validation_predictions,
        average="macro"
    )
)

validation_weighted_f1 = (
    f1_score(
        y_validation,
        validation_predictions,
        average="weighted"
    )
)

print(
    f"Validation Accuracy : "
    f"{validation_accuracy:.4f}"
)

print(
    f"Validation Macro F1 : "
    f"{validation_macro_f1:.4f}"
)

print(
    f"Validation Weighted F1 : "
    f"{validation_weighted_f1:.4f}"
)


# ============================================================
# FINAL TEST
# ============================================================

print("""
========================================
 FINAL TEST
========================================
""")

test_predictions = (
    model.predict(
        X_test
    )
)

test_accuracy = (
    accuracy_score(
        y_test,
        test_predictions
    )
)

test_macro_f1 = (
    f1_score(
        y_test,
        test_predictions,
        average="macro"
    )
)

test_weighted_f1 = (
    f1_score(
        y_test,
        test_predictions,
        average="weighted"
    )
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

print("""
========================================
 CLASSIFICATION REPORT
========================================
""")

print(
    classification_report(
        y_test,
        test_predictions,
        labels=[0, 1, 2, 3],
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

print("""
========================================
 CONFUSION MATRIX
========================================
""")

cm = confusion_matrix(
    y_test,
    test_predictions,
    labels=[0, 1, 2, 3]
)

cm_df = pd.DataFrame(
    cm,
    index=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CONGESTED"
    ],
    columns=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CONGESTED"
    ]
)

print(
    cm_df
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("""
========================================
 FEATURE IMPORTANCE
========================================
""")

importance = pd.DataFrame({
    "feature": feature_columns,
    "importance": model.feature_importances_
})

importance = (
    importance
    .sort_values(
        "importance",
        ascending=False
    )
)

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

print("""
========================================
 SAVING MODEL
========================================
""")

model.save_model(
    MODEL_FILE
)

print(
    f"Model saved:\n"
    f"{MODEL_FILE}"
)


# ============================================================
# SAVE FEATURE LIST
# ============================================================

with open(
    FEATURE_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        feature_columns,
        f,
        indent=4
    )

print(
    f"Feature list saved:\n"
    f"{FEATURE_FILE}"
)


# ============================================================
# SAVE METRICS
# ============================================================

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v2_metrics.json"
)

metrics = {

    "model": "TRAFFICX XGBoost V2",

    "prediction_horizon_seconds": 300,

    "features": len(
        feature_columns
    ),

    "train_rows": len(train),

    "validation_rows": len(validation),

    "test_rows": len(test),

    "validation_accuracy":
        float(validation_accuracy),

    "validation_macro_f1":
        float(validation_macro_f1),

    "validation_weighted_f1":
        float(validation_weighted_f1),

    "test_accuracy":
        float(test_accuracy),

    "test_macro_f1":
        float(test_macro_f1),

    "test_weighted_f1":
        float(test_weighted_f1)
}

with open(
    METRICS_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )


# ============================================================
# COMPLETE
# ============================================================

print("""
========================================
 TRAFFICX XGBOOST V2 COMPLETE
========================================

Model:
trafficx_xgboost_v2.json

Features:
46 temporal + traffic features

Prediction:
5-minute future congestion

Next:
Compare V1 vs V2
========================================
""")