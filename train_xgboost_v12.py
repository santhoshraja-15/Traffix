# ============================================================
# TRAFFICX - XGBOOST V12
# TEMPORAL RISK-AWARE TRAFFIC PREDICTION
# ============================================================

import os
import json
import warnings

import numpy as np
import pandas as pd

from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)


warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

DATASET = os.path.join(
    BASE_DIR,
    "road_datasets",
    "trafficx_ml_dataset_v2.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v12_risk.json"
)

RESULTS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v12_results.csv"
)

IMPORTANCE_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v12_feature_importance.csv"
)

PREDICTIONS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v12_test_predictions.csv"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

RANDOM_STATE = 42

TEST_FRACTION = 0.20

VALIDATION_FRACTION = 0.10

# Risk threshold.
#
# We initially use 0.50.
# Later V13/V14 can calibrate this threshold specifically
# for high recall / low false alarm operation.
#
RISK_THRESHOLD = 0.50


# ============================================================
# XGBOOST PARAMETERS
# ============================================================

XGB_PARAMS = {
    "n_estimators": 700,
    "max_depth": 8,
    "learning_rate": 0.05,

    "subsample": 0.85,
    "colsample_bytree": 0.85,

    "min_child_weight": 5,

    "gamma": 0.1,

    "reg_alpha": 0.1,
    "reg_lambda": 2.0,

    "objective": "binary:logistic",

    "eval_metric": "aucpr",

    "tree_method": "hist",

    "random_state": RANDOM_STATE,

    "n_jobs": -1,

    "verbosity": 1,
}


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX - XGBOOST V12")
print(" TEMPORAL RISK-AWARE TRAFFIC PREDICTION")
print("=" * 70)

print()
print("Dataset:")
print(DATASET)

print()
print("Target:")
print("NON_RISK = LOW + MEDIUM")
print("RISK     = HIGH + CONGESTED")

print()
print("Risk threshold:")
print(RISK_THRESHOLD)

print()


# ============================================================
# CHECK DATASET
# ============================================================

if not os.path.exists(DATASET):

    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET}"
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print(" LOADING DATASET")
print("=" * 70)

print()

df = pd.read_csv(DATASET)

print(f"Rows    : {len(df):,}")
print(f"Columns : {len(df.columns)}")

print()


# ============================================================
# CREATE RISK TARGET
# ============================================================

print("=" * 70)
print(" CREATING RISK TARGET")
print("=" * 70)

print()


RISK_CLASSES = {
    "HIGH",
    "CONGESTED"
}


df["risk_target"] = (
    df["future_congestion"]
    .isin(RISK_CLASSES)
    .astype(np.int8)
)


print(
    df["risk_target"]
    .value_counts()
    .sort_index()
)


print()

risk_distribution = (
    df["risk_target"]
    .value_counts(normalize=True)
    .sort_index()
    * 100
)

print(
    risk_distribution.round(3)
)


# ============================================================
# FEATURE SELECTION
# ============================================================

print()
print("=" * 70)
print(" SELECTING MODEL FEATURES")
print("=" * 70)

print()


# Current-state features
#
# These are available at prediction time.

FEATURE_COLUMNS = [

    "road_length_m",

    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",

    "density_veh_per_km",
    "queue_length_estimate_m",

    # Activity features

    "has_vehicles",
    "has_stopped_vehicles",
    "has_queue",

    "stopped_vehicle_ratio",
    "vehicles_per_100m",
    "queue_ratio",

    # Temporal features

    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",

    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",

    "speed_change_pct",
    "vehicle_change_pct",
]


# We intentionally DO NOT use:
#
# scenario
# road_id
# step
#
# because those can create memorization / leakage.
#
# We also intentionally exclude:
#
# congestion_level
#
# so the model learns directly from physical traffic features.
#
# Future columns are completely excluded.


print("Features:")

for i, feature in enumerate(FEATURE_COLUMNS, 1):

    print(
        f"{i:02d}. {feature}"
    )


print()
print(
    f"Total model features: {len(FEATURE_COLUMNS)}"
)


# ============================================================
# CHECK FEATURES
# ============================================================

missing_features = [
    c
    for c in FEATURE_COLUMNS
    if c not in df.columns
]

if missing_features:

    raise RuntimeError(
        "Missing required features:\n"
        + "\n".join(missing_features)
    )


# ============================================================
# TEMPORAL SORT
# ============================================================

print()
print("=" * 70)
print(" SORTING TEMPORAL DATA")
print("=" * 70)

print()


df = df.sort_values(
    [
        "scenario",
        "road_id",
        "step"
    ],
    kind="mergesort"
).reset_index(drop=True)


# ============================================================
# TEMPORAL TRAIN / VALIDATION / TEST SPLIT
# ============================================================
#
# IMPORTANT:
#
# We do NOT randomly split rows.
#
# For every scenario + road:
#
# EARLY   -> TRAIN
# MIDDLE  -> VALIDATION
# LATE    -> TEST
#
# This prevents future observations from appearing in training.
# ============================================================

print()
print("=" * 70)
print(" TEMPORAL TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

print()


def temporal_split(group):

    n = len(group)

    train_end = int(
        n * (1.0 - VALIDATION_FRACTION - TEST_FRACTION)
    )

    validation_end = int(
        n * (1.0 - TEST_FRACTION)
    )

    result = np.empty(
        n,
        dtype=np.int8
    )

    result[:train_end] = 0
    result[train_end:validation_end] = 1
    result[validation_end:] = 2

    return pd.Series(
        result,
        index=group.index
    )


df["split"] = (
    df.groupby(
        ["scenario", "road_id"],
        sort=False,
        group_keys=False
    )
    .apply(
        temporal_split,
        include_groups=False
    )
)


# ============================================================
# SPLIT SUMMARY
# ============================================================

print("Split distribution:")

split_names = {
    0: "TRAIN",
    1: "VALIDATION",
    2: "TEST"
}

for split_id, split_name in split_names.items():

    subset = df[
        df["split"] == split_id
    ]

    risk_count = int(
        subset["risk_target"].sum()
    )

    total = len(subset)

    risk_pct = (
        risk_count / total * 100
        if total > 0
        else 0
    )

    print()
    print(
        f"{split_name}:"
    )

    print(
        f"  Rows      : {total:,}"
    )

    print(
        f"  Risk      : {risk_count:,}"
    )

    print(
        f"  Non-risk  : {total - risk_count:,}"
    )

    print(
        f"  Risk %    : {risk_pct:.3f}%"
    )


# ============================================================
# EXTRACT SPLITS
# ============================================================

train_df = df[
    df["split"] == 0
]

validation_df = df[
    df["split"] == 1
]

test_df = df[
    df["split"] == 2
]


X_train = train_df[
    FEATURE_COLUMNS
].astype(np.float32)

y_train = train_df[
    "risk_target"
].astype(np.int8)


X_validation = validation_df[
    FEATURE_COLUMNS
].astype(np.float32)

y_validation = validation_df[
    "risk_target"
].astype(np.int8)


X_test = test_df[
    FEATURE_COLUMNS
].astype(np.float32)

y_test = test_df[
    "risk_target"
].astype(np.int8)


# ============================================================
# CLASS IMBALANCE
# ============================================================

print()
print("=" * 70)
print(" CALCULATING CLASS WEIGHT")
print("=" * 70)

print()


negative_count = int(
    (y_train == 0).sum()
)

positive_count = int(
    (y_train == 1).sum()
)


scale_pos_weight = (
    negative_count / positive_count
)


print(
    f"Non-risk training samples : {negative_count:,}"
)

print(
    f"Risk training samples     : {positive_count:,}"
)

print(
    f"scale_pos_weight          : "
    f"{scale_pos_weight:.3f}"
)


# ============================================================
# CREATE MODEL
# ============================================================

print()
print("=" * 70)
print(" INITIALIZING XGBOOST")
print("=" * 70)

print()


model = XGBClassifier(
    **XGB_PARAMS,
    scale_pos_weight=scale_pos_weight
)


# ============================================================
# TRAIN
# ============================================================

print()
print("=" * 70)
print(" TRAINING")
print("=" * 70)

print()

print(
    "Training rows:",
    f"{len(X_train):,}"
)

print(
    "Validation rows:",
    f"{len(X_validation):,}"
)

print(
    "Test rows:",
    f"{len(X_test):,}"
)

print()

print(
    "This may take several minutes depending on CPU/RAM."
)

print()


model.fit(
    X_train,
    y_train,

    eval_set=[
        (
            X_train,
            y_train
        ),
        (
            X_validation,
            y_validation
        )
    ],

    verbose=True
)


# ============================================================
# SAVE MODEL
# ============================================================

print()
print("=" * 70)
print(" SAVING MODEL")
print("=" * 70)

print()


model.save_model(
    MODEL_PATH
)


print(
    "Model saved:"
)

print(
    MODEL_PATH
)


# ============================================================
# TEST PREDICTIONS
# ============================================================

print()
print("=" * 70)
print(" TEST PREDICTION")
print("=" * 70)

print()


test_probability = model.predict_proba(
    X_test
)[:, 1]


test_prediction = (
    test_probability >= RISK_THRESHOLD
).astype(np.int8)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    test_prediction
)

precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0
)

recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0
)

f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    test_probability
)

pr_auc = average_precision_score(
    y_test,
    test_probability
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    test_prediction
)


tn, fp, fn, tp = cm.ravel()


false_alarm_rate = (
    fp / (fp + tn)
    if (fp + tn) > 0
    else 0
)


print()
print("=" * 70)
print(" TEST RESULTS")
print("=" * 70)

print()

print(
    f"Accuracy          : {accuracy:.4f}"
)

print(
    f"Precision         : {precision:.4f}"
)

print(
    f"Risk Recall       : {recall:.4f}"
)

print(
    f"F1 Score          : {f1:.4f}"
)

print(
    f"ROC-AUC           : {roc_auc:.4f}"
)

print(
    f"PR-AUC            : {pr_auc:.4f}"
)

print(
    f"False Alarm Rate   : {false_alarm_rate:.4f}"
)


print()
print("Confusion Matrix:")
print()

print(
    "                 Predicted"
)

print(
    "              NON-RISK   RISK"
)

print(
    f"Actual NON-RISK "
    f"{tn:10,d} {fp:8,d}"
)

print(
    f"Actual RISK     "
    f"{fn:10,d} {tp:8,d}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print()
print("=" * 70)
print(" CLASSIFICATION REPORT")
print("=" * 70)

print()

print(
    classification_report(
        y_test,
        test_prediction,
        target_names=[
            "NON_RISK",
            "RISK"
        ],
        digits=4,
        zero_division=0
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print()
print("=" * 70)
print(" FEATURE IMPORTANCE")
print("=" * 70)

print()


importance = pd.DataFrame({

    "feature": FEATURE_COLUMNS,

    "importance": model.feature_importances_

})


importance = importance.sort_values(
    "importance",
    ascending=False
).reset_index(drop=True)


for _, row in importance.iterrows():

    print(
        f"{row['feature']:30s} "
        f"{row['importance']:.6f}"
    )


importance.to_csv(
    IMPORTANCE_PATH,
    index=False
)


# ============================================================
# SAVE TEST PREDICTIONS
# ============================================================

print()
print("=" * 70)
print(" SAVING TEST PREDICTIONS")
print("=" * 70)

print()


prediction_output = test_df[
    [
        "scenario",
        "step",
        "road_id",
        "future_congestion",
        "risk_target"
    ]
].copy()


prediction_output[
    "risk_probability"
] = test_probability


prediction_output[
    "predicted_risk"
] = test_prediction


prediction_output.to_csv(
    PREDICTIONS_PATH,
    index=False
)


print(
    PREDICTIONS_PATH
)


# ============================================================
# SAVE RESULTS
# ============================================================

results = pd.DataFrame({

    "model": [
        "TRAFFICX XGBoost V12"
    ],

    "dataset": [
        os.path.basename(DATASET)
    ],

    "features": [
        len(FEATURE_COLUMNS)
    ],

    "train_rows": [
        len(X_train)
    ],

    "validation_rows": [
        len(X_validation)
    ],

    "test_rows": [
        len(X_test)
    ],

    "risk_train": [
        positive_count
    ],

    "non_risk_train": [
        negative_count
    ],

    "scale_pos_weight": [
        scale_pos_weight
    ],

    "threshold": [
        RISK_THRESHOLD
    ],

    "accuracy": [
        accuracy
    ],

    "precision": [
        precision
    ],

    "recall": [
        recall
    ],

    "f1": [
        f1
    ],

    "roc_auc": [
        roc_auc
    ],

    "pr_auc": [
        pr_auc
    ],

    "false_alarm_rate": [
        false_alarm_rate
    ],

    "true_negative": [
        tn
    ],

    "false_positive": [
        fp
    ],

    "false_negative": [
        fn
    ],

    "true_positive": [
        tp
    ]

})


results.to_csv(
    RESULTS_PATH,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX V12 COMPLETE")
print("=" * 70)

print()

print(
    "Model:"
)

print(
    MODEL_PATH
)

print()

print(
    "Results:"
)

print(
    RESULTS_PATH
)

print()

print(
    "Feature importance:"
)

print(
    IMPORTANCE_PATH
)

print()

print(
    "Test predictions:"
)

print(
    PREDICTIONS_PATH
)

print()

print("=" * 70)