# ============================================================
# TRAFFICX - XGBOOST V13
# TEMPORAL RISK PREDICTION + THRESHOLD OPTIMIZATION
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
    "trafficx_xgboost_v13_risk.json"
)

RESULTS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v13_results.csv"
)

THRESHOLD_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v13_thresholds.csv"
)

IMPORTANCE_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v13_feature_importance.csv"
)

PREDICTIONS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v13_test_predictions.csv"
)

RANDOM_STATE = 42

# ------------------------------------------------------------
# Temporal split
# ------------------------------------------------------------

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

# ------------------------------------------------------------
# Risk definition
# ------------------------------------------------------------

RISK_CLASSES = {
    "HIGH",
    "CONGESTED"
}

NON_RISK_CLASSES = {
    "LOW",
    "MEDIUM"
}

# ------------------------------------------------------------
# Desired operating point
# ------------------------------------------------------------

MIN_RECALL = 0.70

# We prefer lower false alarms when several thresholds
# provide similar recall.
MAX_FALSE_ALARM = 0.07


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX - XGBOOST V13")
print(" TEMPORAL RISK PREDICTION + THRESHOLD OPTIMIZATION")
print("=" * 70)

print()
print("Dataset:")
print(DATASET)

print()
print("Model:")
print(MODEL_PATH)

print()
print("Risk definition:")
print("NON_RISK = LOW + MEDIUM")
print("RISK     = HIGH + CONGESTED")

print()
print("Split:")
print(f"TRAIN      = {TRAIN_RATIO * 100:.0f}%")
print(f"VALIDATION = {VALIDATION_RATIO * 100:.0f}%")
print(f"TEST       = {TEST_RATIO * 100:.0f}%")

print()
print("Minimum desired recall:")
print(f"{MIN_RECALL:.0%}")

print()
print("=" * 70)


# ============================================================
# FEATURES
# ============================================================

FEATURE_COLUMNS = [

    "road_length_m",

    "vehicle_count",

    "average_speed_kmh",

    "stopped_vehicles",

    "average_waiting_time",

    "density_veh_per_km",

    "queue_length_estimate_m",

    "has_vehicles",

    "has_stopped_vehicles",

    "has_queue",

    "stopped_vehicle_ratio",

    "vehicles_per_100m",

    "queue_ratio",

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


TARGET_COLUMN = "future_congestion"


REQUIRED_COLUMNS = [
    "scenario",
    "step",
    "road_id",
    TARGET_COLUMN,
] + FEATURE_COLUMNS


# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 70)
print(" LOADING DATASET")
print("=" * 70)

if not os.path.exists(DATASET):
    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET}"
    )

print()
print("Reading dataset...")

df = pd.read_csv(
    DATASET,
    usecols=REQUIRED_COLUMNS
)

print()
print(f"Rows loaded: {len(df):,}")

print()
print("Columns loaded:")
for c in df.columns:
    print(f"  {c}")


# ============================================================
# BASIC VALIDATION
# ============================================================

print()
print("=" * 70)
print(" DATA VALIDATION")
print("=" * 70)

missing_columns = [
    c for c in REQUIRED_COLUMNS
    if c not in df.columns
]

if missing_columns:

    raise RuntimeError(
        "Missing required columns:\n"
        + "\n".join(missing_columns)
    )

print()
print("All required columns present.")


# ============================================================
# SORT TEMPORALLY
# ============================================================

print()
print("=" * 70)
print(" TEMPORAL SORTING")
print("=" * 70)

df = df.sort_values(
    [
        "step",
        "scenario",
        "road_id"
    ]
).reset_index(drop=True)

print()
print("Temporal sorting complete.")


# ============================================================
# CREATE BINARY RISK TARGET
# ============================================================

print()
print("=" * 70)
print(" CREATING RISK TARGET")
print("=" * 70)

df["risk_target"] = (
    df[TARGET_COLUMN]
    .isin(RISK_CLASSES)
    .astype(np.int8)
)

print()
print("Future congestion:")
print(
    df[TARGET_COLUMN]
    .value_counts()
    .to_string()
)

print()
print("Binary risk distribution:")
print(
    df["risk_target"]
    .value_counts()
    .sort_index()
    .to_string()
)

risk_percentage = (
    df["risk_target"].mean() * 100
)

print()
print(
    f"Overall future risk: {risk_percentage:.3f}%"
)


# ============================================================
# TEMPORAL SPLIT
# ============================================================

print()
print("=" * 70)
print(" TEMPORAL TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

unique_steps = np.sort(
    df["step"].unique()
)

n_steps = len(unique_steps)

train_end = int(
    n_steps * TRAIN_RATIO
)

validation_end = int(
    n_steps *
    (TRAIN_RATIO + VALIDATION_RATIO)
)

train_steps = unique_steps[
    :train_end
]

validation_steps = unique_steps[
    train_end:validation_end
]

test_steps = unique_steps[
    validation_end:
]

train_mask = df["step"].isin(
    train_steps
)

validation_mask = df["step"].isin(
    validation_steps
)

test_mask = df["step"].isin(
    test_steps
)

train_df = df.loc[
    train_mask
].copy()

validation_df = df.loc[
    validation_mask
].copy()

test_df = df.loc[
    test_mask
].copy()

print()
print(f"Total simulation steps: {n_steps:,}")

print()
print("Step boundaries:")

print(
    f"TRAIN      : "
    f"{train_steps.min()} -> "
    f"{train_steps.max()}"
)

print(
    f"VALIDATION : "
    f"{validation_steps.min()} -> "
    f"{validation_steps.max()}"
)

print(
    f"TEST       : "
    f"{test_steps.min()} -> "
    f"{test_steps.max()}"
)

print()
print("Rows:")

print(
    f"TRAIN      : {len(train_df):,}"
)

print(
    f"VALIDATION : {len(validation_df):,}"
)

print(
    f"TEST       : {len(test_df):,}"
)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print()
print("=" * 70)
print(" TARGET DISTRIBUTION BY SPLIT")
print("=" * 70)


def print_distribution(name, data):

    total = len(data)

    risk = int(
        data["risk_target"].sum()
    )

    non_risk = total - risk

    print()
    print(name)

    print(
        f"  NON_RISK : "
        f"{non_risk:,} "
        f"({non_risk / total * 100:.3f}%)"
    )

    print(
        f"  RISK     : "
        f"{risk:,} "
        f"({risk / total * 100:.3f}%)"
    )


print_distribution(
    "TRAIN",
    train_df
)

print_distribution(
    "VALIDATION",
    validation_df
)

print_distribution(
    "TEST",
    test_df
)


# ============================================================
# PREPARE MATRICES
# ============================================================

print()
print("=" * 70)
print(" PREPARING FEATURES")
print("=" * 70)

X_train = train_df[
    FEATURE_COLUMNS
]

y_train = train_df[
    "risk_target"
]

X_validation = validation_df[
    FEATURE_COLUMNS
]

y_validation = validation_df[
    "risk_target"
]

X_test = test_df[
    FEATURE_COLUMNS
]

y_test = test_df[
    "risk_target"
]

print()
print(
    f"Number of features: "
    f"{len(FEATURE_COLUMNS)}"
)

print()
print("Features:")

for i, feature in enumerate(
    FEATURE_COLUMNS,
    start=1
):

    print(
        f"{i:02d}. {feature}"
    )


# ============================================================
# CLASS IMBALANCE
# ============================================================

negative = int(
    (y_train == 0).sum()
)

positive = int(
    (y_train == 1).sum()
)

scale_pos_weight = (
    negative / positive
    if positive > 0
    else 1.0
)

print()
print("=" * 70)
print(" CLASS IMBALANCE")
print("=" * 70)

print()
print(
    f"NON_RISK samples: {negative:,}"
)

print(
    f"RISK samples    : {positive:,}"
)

print(
    f"scale_pos_weight: "
    f"{scale_pos_weight:.4f}"
)


# ============================================================
# TRAIN XGBOOST
# ============================================================

print()
print("=" * 70)
print(" TRAINING XGBOOST V13")
print("=" * 70)

model = XGBClassifier(

    objective="binary:logistic",

    eval_metric="aucpr",

    n_estimators=700,

    max_depth=7,

    learning_rate=0.05,

    subsample=0.85,

    colsample_bytree=0.85,

    min_child_weight=3,

    gamma=0.05,

    reg_alpha=0.05,

    reg_lambda=1.5,

    scale_pos_weight=scale_pos_weight,

    tree_method="hist",

    n_jobs=-1,

    random_state=RANDOM_STATE,

)


print()
print("Training parameters:")

print(
    f"n_estimators      : "
    f"{model.get_params()['n_estimators']}"
)

print(
    f"max_depth         : "
    f"{model.get_params()['max_depth']}"
)

print(
    f"learning_rate     : "
    f"{model.get_params()['learning_rate']}"
)

print(
    f"scale_pos_weight  : "
    f"{scale_pos_weight:.4f}"
)

print()
print("Training...")

model.fit(
    X_train,
    y_train,
    eval_set=[
        (X_validation, y_validation)
    ],
    verbose=50
)

print()
print("Training complete.")


# ============================================================
# VALIDATION PROBABILITIES
# ============================================================

print()
print("=" * 70)
print(" VALIDATION PROBABILITIES")
print("=" * 70)

validation_probability = model.predict_proba(
    X_validation
)[:, 1]

validation_roc_auc = roc_auc_score(
    y_validation,
    validation_probability
)

validation_pr_auc = average_precision_score(
    y_validation,
    validation_probability
)

print()
print(
    f"Validation ROC-AUC : "
    f"{validation_roc_auc:.4f}"
)

print(
    f"Validation PR-AUC  : "
    f"{validation_pr_auc:.4f}"
)


# ============================================================
# THRESHOLD SWEEP
# ============================================================

print()
print("=" * 70)
print(" THRESHOLD OPTIMIZATION")
print("=" * 70)

thresholds = np.arange(
    0.05,
    0.951,
    0.01
)

threshold_results = []


for threshold in thresholds:

    predictions = (
        validation_probability >= threshold
    ).astype(np.int8)

    tn, fp, fn, tp = confusion_matrix(
        y_validation,
        predictions,
        labels=[0, 1]
    ).ravel()

    precision = precision_score(
        y_validation,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_validation,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_validation,
        predictions,
        zero_division=0
    )

    accuracy = accuracy_score(
        y_validation,
        predictions
    )

    false_alarm_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0
    )

    miss_rate = (
        fn / (fn + tp)
        if (fn + tp) > 0
        else 0
    )

    threshold_results.append({

        "threshold": threshold,

        "accuracy": accuracy,

        "precision": precision,

        "recall": recall,

        "f1": f1,

        "false_alarm_rate":
            false_alarm_rate,

        "miss_rate":
            miss_rate,

        "true_negative": tn,

        "false_positive": fp,

        "false_negative": fn,

        "true_positive": tp,

    })


threshold_df = pd.DataFrame(
    threshold_results
)


# ============================================================
# SELECT THRESHOLD
# ============================================================

print()
print("=" * 70)
print(" SELECTING OPERATING THRESHOLD")
print("=" * 70)

eligible = threshold_df[
    (threshold_df["recall"] >= MIN_RECALL)
    &
    (
        threshold_df["false_alarm_rate"]
        <= MAX_FALSE_ALARM
    )
].copy()

if len(eligible) > 0:

    # Among acceptable thresholds:
    # maximize precision first,
    # then F1,
    # then recall.

    eligible = eligible.sort_values(
        [
            "precision",
            "f1",
            "recall"
        ],
        ascending=False
    )

    selected = eligible.iloc[0]

else:

    # If no threshold meets both constraints,
    # maximize F1 subject to recall >= MIN_RECALL.

    recall_eligible = threshold_df[
        threshold_df["recall"] >= MIN_RECALL
    ].copy()

    if len(recall_eligible) > 0:

        recall_eligible = (
            recall_eligible
            .sort_values(
                [
                    "f1",
                    "precision"
                ],
                ascending=False
            )
        )

        selected = recall_eligible.iloc[0]

    else:

        selected = (
            threshold_df
            .sort_values(
                "f1",
                ascending=False
            )
            .iloc[0]
        )


BEST_THRESHOLD = float(
    selected["threshold"]
)


print()
print(
    f"Selected threshold: "
    f"{BEST_THRESHOLD:.2f}"
)

print()
print(
    f"Validation precision : "
    f"{selected['precision']:.4f}"
)

print(
    f"Validation recall    : "
    f"{selected['recall']:.4f}"
)

print(
    f"Validation F1        : "
    f"{selected['f1']:.4f}"
)

print(
    f"False alarm rate     : "
    f"{selected['false_alarm_rate']:.4f}"
)


# ============================================================
# SAVE THRESHOLD RESULTS
# ============================================================

threshold_df.to_csv(
    THRESHOLD_PATH,
    index=False
)

print()
print(
    f"Threshold results saved:"
)

print(
    THRESHOLD_PATH
)


# ============================================================
# TEST EVALUATION
# ============================================================

print()
print("=" * 70)
print(" FINAL TEST EVALUATION")
print("=" * 70)

test_probability = model.predict_proba(
    X_test
)[:, 1]

test_prediction = (
    test_probability >= BEST_THRESHOLD
).astype(np.int8)


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

test_accuracy = accuracy_score(
    y_test,
    test_prediction
)

test_precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0
)

test_recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0
)

test_f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0
)

test_roc_auc = roc_auc_score(
    y_test,
    test_probability
)

test_pr_auc = average_precision_score(
    y_test,
    test_probability
)


tn, fp, fn, tp = confusion_matrix(
    y_test,
    test_prediction,
    labels=[0, 1]
).ravel()


false_alarm_rate = (
    fp / (fp + tn)
    if (fp + tn) > 0
    else 0
)

miss_rate = (
    fn / (fn + tp)
    if (fn + tp) > 0
    else 0
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print(" V13 TEST RESULTS")
print("=" * 70)

print()

print(
    f"Threshold         : "
    f"{BEST_THRESHOLD:.2f}"
)

print(
    f"Accuracy          : "
    f"{test_accuracy:.4f}"
)

print(
    f"Precision         : "
    f"{test_precision:.4f}"
)

print(
    f"Risk Recall       : "
    f"{test_recall:.4f}"
)

print(
    f"F1 Score          : "
    f"{test_f1:.4f}"
)

print(
    f"ROC-AUC           : "
    f"{test_roc_auc:.4f}"
)

print(
    f"PR-AUC            : "
    f"{test_pr_auc:.4f}"
)

print(
    f"False Alarm Rate  : "
    f"{false_alarm_rate:.4f}"
)

print(
    f"Miss Rate         : "
    f"{miss_rate:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

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
    f"{tn:10,} "
    f"{fp:8,}"
)

print(
    f"Actual RISK     "
    f"{fn:10,} "
    f"{tp:8,}"
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

importance = pd.DataFrame({

    "feature":
        FEATURE_COLUMNS,

    "importance":
        model.feature_importances_

})

importance = importance.sort_values(
    "importance",
    ascending=False
)

for _, row in importance.iterrows():

    print(
        f"{row['feature']:<32}"
        f"{row['importance']:.6f}"
    )


importance.to_csv(
    IMPORTANCE_PATH,
    index=False
)


# ============================================================
# SAVE MODEL
# ============================================================

print()
print("=" * 70)
print(" SAVING MODEL")
print("=" * 70)

model.save_model(
    MODEL_PATH
)

print()
print(
    f"Model saved:"
)

print(
    MODEL_PATH
)


# ============================================================
# SAVE TEST PREDICTIONS
# ============================================================

print()
print("=" * 70)
print(" SAVING TEST PREDICTIONS")
print("=" * 70)

prediction_output = test_df[
    [
        "scenario",
        "step",
        "road_id",
        TARGET_COLUMN
    ]
].copy()

prediction_output[
    "risk_probability"
] = test_probability

prediction_output[
    "risk_prediction"
] = test_prediction

prediction_output[
    "prediction_label"
] = np.where(
    test_prediction == 1,
    "RISK",
    "NON_RISK"
)

prediction_output[
    "threshold"
] = BEST_THRESHOLD

prediction_output.to_csv(
    PREDICTIONS_PATH,
    index=False
)

print()
print(
    PREDICTIONS_PATH
)


# ============================================================
# SAVE SUMMARY RESULTS
# ============================================================

results = pd.DataFrame([
    {
        "model": "TRAFFICX_XGBOOST_V13",

        "threshold":
            BEST_THRESHOLD,

        "accuracy":
            test_accuracy,

        "precision":
            test_precision,

        "risk_recall":
            test_recall,

        "f1":
            test_f1,

        "roc_auc":
            test_roc_auc,

        "pr_auc":
            test_pr_auc,

        "false_alarm_rate":
            false_alarm_rate,

        "miss_rate":
            miss_rate,

        "true_negative":
            tn,

        "false_positive":
            fp,

        "false_negative":
            fn,

        "true_positive":
            tp,

        "train_rows":
            len(train_df),

        "validation_rows":
            len(validation_df),

        "test_rows":
            len(test_df),

        "num_features":
            len(FEATURE_COLUMNS),

        "future_risk_percentage":
            df["risk_target"].mean() * 100
    }
])

results.to_csv(
    RESULTS_PATH,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print(" TRAFFICX V13 COMPLETE")
print("=" * 70)

print()

print("Model:")
print(MODEL_PATH)

print()

print("Results:")
print(RESULTS_PATH)

print()

print("Threshold analysis:")
print(THRESHOLD_PATH)

print()

print("Feature importance:")
print(IMPORTANCE_PATH)

print()

print("Test predictions:")
print(PREDICTIONS_PATH)

print()

print("Final metrics:")
print(
    f"  Threshold        : "
    f"{BEST_THRESHOLD:.2f}"
)

print(
    f"  Precision        : "
    f"{test_precision:.4f}"
)

print(
    f"  Risk Recall      : "
    f"{test_recall:.4f}"
)

print(
    f"  F1               : "
    f"{test_f1:.4f}"
)

print(
    f"  ROC-AUC          : "
    f"{test_roc_auc:.4f}"
)

print(
    f"  PR-AUC           : "
    f"{test_pr_auc:.4f}"
)

print(
    f"  False Alarm Rate : "
    f"{false_alarm_rate:.4f}"
)

print()
print("=" * 70)