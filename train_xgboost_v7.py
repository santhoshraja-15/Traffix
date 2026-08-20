import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score
)

# ============================================================
# TRAFFICX - XGBOOST V7
# HIERARCHICAL RISK-AWARE PREDICTION
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

DATASET = os.path.join(
    BASE_DIR,
    "road_datasets",
    "trafficx_xgboost_v3_dataset.csv"
)

V6_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v6.json"
)

V6_FEATURES = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v6_features.json"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

V7_MODEL = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7.json"
)

V7_FEATURES = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7_features.json"
)

V7_THRESHOLDS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7_thresholds.json"
)

V7_METRICS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7_metrics.json"
)

V7_CONFUSION = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7_confusion_matrix.csv"
)

V7_REPORT = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v7_classification_report.txt"
)


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_MAX_STEP = 499
VAL_MIN_STEP = 500
VAL_MAX_STEP = 599
TEST_MIN_STEP = 600
TEST_MAX_STEP = 699

CLASS_NAMES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CONGESTED"
]

CLASS_TO_ID = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}

ID_TO_CLASS = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH",
    3: "CONGESTED"
}


print("\n========================================")
print(" TRAFFICX - XGBOOST V7")
print(" HIERARCHICAL RISK-AWARE PREDICTION")
print("========================================")

print("\nDataset:")
print(DATASET)

print("\nV6 model:")
print(V6_MODEL)

print("\nPrediction horizon:")
print("5 minutes = 300 simulation steps")

print("\nTemporal split:")
print("Train      : steps 0-499")
print("Validation : steps 500-599")
print("Test       : steps 600-699")

print("\nV7 strategy:")
print("1. Load trained V6 probability model")
print("2. Generate class probabilities")
print("3. Calculate HIGH + CONGESTED risk probability")
print("4. Optimize risk threshold using validation only")
print("5. Freeze threshold")
print("6. Evaluate final test risk")
print("7. Preserve original 4-class prediction")


# ============================================================
# LOAD DATASET
# ============================================================

print("\n========================================")
print(" LOADING DATASET")
print("========================================")

df = pd.read_csv(DATASET)

print(f"Rows loaded: {len(df):,}")
print(f"Columns    : {len(df.columns)}")


# ============================================================
# DATASET VALIDATION
# ============================================================

print("\n========================================")
print(" DATASET VALIDATION")
print("========================================")

print(
    f"Step range: "
    f"{df['step'].min()} - {df['step'].max()}"
)

print(
    f"Unique roads: "
    f"{df['road_id'].nunique():,}"
)

print(
    f"Unique scenarios: "
    f"{df['scenario'].nunique()}"
)


# ============================================================
# LOAD FEATURE LIST
# ============================================================

print("\n========================================")
print(" LOADING V6 FEATURE LIST")
print("========================================")

with open(V6_FEATURES, "r") as f:
    features = json.load(f)

print(
    f"Number of features: {len(features)}"
)

for i, feature in enumerate(features, 1):
    print(
        f"{i:02d}. {feature}"
    )


# ============================================================
# FEATURE VALIDATION
# ============================================================

missing_features = [
    feature
    for feature in features
    if feature not in df.columns
]

if missing_features:

    print("\nERROR:")
    print("Missing features:")

    for feature in missing_features:
        print(feature)

    raise ValueError(
        "Dataset does not contain all V6 features."
    )


# ============================================================
# TARGET ENCODING
# ============================================================

print("\n========================================")
print(" TARGET ENCODING")
print("========================================")

print(
    df["future_congestion"].value_counts()
)


df["target_encoded"] = (
    df["future_congestion"]
    .map(CLASS_TO_ID)
)


if df["target_encoded"].isna().any():

    raise ValueError(
        "Unknown target class detected."
    )


df["target_encoded"] = (
    df["target_encoded"]
    .astype(int)
)


# ============================================================
# FEATURE CLEANING
# ============================================================

print("\n========================================")
print(" FEATURE CLEANING")
print("========================================")

X_all = df[features].copy()

X_all = X_all.replace(
    [np.inf, -np.inf],
    np.nan
)

nan_rows = X_all.isna().any(axis=1).sum()

print(
    f"Rows containing NaN/Inf: {nan_rows:,}"
)

if nan_rows > 0:

    print(
        "Removing invalid rows..."
    )

    valid_mask = ~X_all.isna().any(axis=1)

    df = df.loc[valid_mask].copy()

    X_all = X_all.loc[valid_mask].copy()


# ============================================================
# TEMPORAL SPLIT
# ============================================================

print("\n========================================")
print(" TEMPORAL SPLIT")
print("========================================")


train_mask = (
    df["step"] <= TRAIN_MAX_STEP
)

val_mask = (
    (df["step"] >= VAL_MIN_STEP)
    &
    (df["step"] <= VAL_MAX_STEP)
)

test_mask = (
    (df["step"] >= TEST_MIN_STEP)
    &
    (df["step"] <= TEST_MAX_STEP)
)


X_train = X_all.loc[train_mask]
X_val = X_all.loc[val_mask]
X_test = X_all.loc[test_mask]

y_train = df.loc[
    train_mask,
    "target_encoded"
]

y_val = df.loc[
    val_mask,
    "target_encoded"
]

y_test = df.loc[
    test_mask,
    "target_encoded"
]


print(
    f"Train rows      : {len(X_train):,}"
)

print(
    f"Validation rows : {len(X_val):,}"
)

print(
    f"Test rows       : {len(X_test):,}"
)

print("\nTrain step range:")
print(
    f"{df.loc[train_mask, 'step'].min()} - "
    f"{df.loc[train_mask, 'step'].max()}"
)

print("\nValidation step range:")
print(
    f"{df.loc[val_mask, 'step'].min()} - "
    f"{df.loc[val_mask, 'step'].max()}"
)

print("\nTest step range:")
print(
    f"{df.loc[test_mask, 'step'].min()} - "
    f"{df.loc[test_mask, 'step'].max()}"
)


# ============================================================
# LOAD V6 MODEL
# ============================================================

print("\n========================================")
print(" LOADING XGBOOST V6")
print("========================================")

model = xgb.XGBClassifier()

model.load_model(
    V6_MODEL
)

print(
    "V6 model loaded successfully."
)


# ============================================================
# GENERATE PROBABILITIES
# ============================================================

print("\n========================================")
print(" GENERATING VALIDATION PROBABILITIES")
print("========================================")

val_prob = model.predict_proba(
    X_val
)

print(
    f"Validation probability matrix:"
)

print(
    val_prob.shape
)


print("\n========================================")
print(" GENERATING TEST PROBABILITIES")
print("========================================")

test_prob = model.predict_proba(
    X_test
)

print(
    f"Test probability matrix:"
)

print(
    test_prob.shape
)


# ============================================================
# STANDARD V6 PREDICTION
# ============================================================

val_standard_pred = np.argmax(
    val_prob,
    axis=1
)

test_standard_pred = np.argmax(
    test_prob,
    axis=1
)


# ============================================================
# STANDARD VALIDATION METRICS
# ============================================================

print("\n========================================")
print(" STANDARD VALIDATION RESULT")
print("========================================")

standard_val_accuracy = accuracy_score(
    y_val,
    val_standard_pred
)

standard_val_macro_f1 = f1_score(
    y_val,
    val_standard_pred,
    average="macro"
)

standard_val_weighted_f1 = f1_score(
    y_val,
    val_standard_pred,
    average="weighted"
)

print(
    f"Accuracy    : "
    f"{standard_val_accuracy:.4f}"
)

print(
    f"Macro F1    : "
    f"{standard_val_macro_f1:.4f}"
)

print(
    f"Weighted F1 : "
    f"{standard_val_weighted_f1:.4f}"
)


# ============================================================
# RISK PROBABILITY
# ============================================================
#
# Operational risk:
#
# HIGH OR CONGESTED
#
# P(RISK) =
#
# P(HIGH) + P(CONGESTED)
#
# This converts the 4-class probability output
# into a traffic-risk probability.
# ============================================================

print("\n========================================")
print(" CALCULATING RISK PROBABILITY")
print("========================================")

val_risk_probability = (
    val_prob[:, CLASS_TO_ID["HIGH"]]
    +
    val_prob[:, CLASS_TO_ID["CONGESTED"]]
)

test_risk_probability = (
    test_prob[:, CLASS_TO_ID["HIGH"]]
    +
    test_prob[:, CLASS_TO_ID["CONGESTED"]]
)


print("\nValidation risk probability:")
print(
    pd.Series(
        val_risk_probability
    ).describe()
)

print("\nTest risk probability:")
print(
    pd.Series(
        test_risk_probability
    ).describe()
)


# ============================================================
# TRUE BINARY RISK
# ============================================================
#
# HIGH and CONGESTED are considered risk.
#
# LOW/MEDIUM = 0
# HIGH/CONGESTED = 1
# ============================================================

y_val_risk = (
    y_val
    .isin(
        [
            CLASS_TO_ID["HIGH"],
            CLASS_TO_ID["CONGESTED"]
        ]
    )
    .astype(int)
    .to_numpy()
)

y_test_risk = (
    y_test
    .isin(
        [
            CLASS_TO_ID["HIGH"],
            CLASS_TO_ID["CONGESTED"]
        ]
    )
    .astype(int)
    .to_numpy()
)


# ============================================================
# BASELINE RISK RESULT
# ============================================================

print("\n========================================")
print(" BASELINE RISK RESULT")
print("========================================")

baseline_threshold = 0.50

val_baseline_risk_pred = (
    val_risk_probability
    >= baseline_threshold
).astype(int)

baseline_precision = precision_score(
    y_val_risk,
    val_baseline_risk_pred,
    zero_division=0
)

baseline_recall = recall_score(
    y_val_risk,
    val_baseline_risk_pred,
    zero_division=0
)

baseline_f1 = f1_score(
    y_val_risk,
    val_baseline_risk_pred,
    zero_division=0
)

print(
    f"Threshold : "
    f"{baseline_threshold:.3f}"
)

print(
    f"Risk precision : "
    f"{baseline_precision:.4f}"
)

print(
    f"Risk recall    : "
    f"{baseline_recall:.4f}"
)

print(
    f"Risk F1        : "
    f"{baseline_f1:.4f}"
)


# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================
#
# IMPORTANT:
#
# Only validation data is used.
#
# Test data remains untouched.
# ============================================================

print("\n========================================")
print(" OPTIMIZING RISK THRESHOLD")
print("========================================")

print(
    "\nSearching validation thresholds..."
)


thresholds = np.arange(
    0.20,
    0.801,
    0.005
)


best_threshold = None
best_score = -1

best_metrics = {}


for threshold in thresholds:

    pred = (
        val_risk_probability
        >= threshold
    ).astype(int)

    precision = precision_score(
        y_val_risk,
        pred,
        zero_division=0
    )

    recall = recall_score(
        y_val_risk,
        pred,
        zero_division=0
    )

    f1 = f1_score(
        y_val_risk,
        pred,
        zero_division=0
    )

    #
    # F2 emphasizes recall.
    #
    # This is appropriate because
    # missing future dangerous congestion
    # is more costly than a false warning.
    #

    beta = 2.0

    if precision + recall == 0:

        f2 = 0.0

    else:

        f2 = (
            (1 + beta ** 2)
            * precision
            * recall
        ) / (
            (beta ** 2 * precision)
            + recall
        )

    #
    # Primary V7 objective:
    # maximize F2.
    #

    score = f2

    if score > best_score:

        best_score = score

        best_threshold = float(
            threshold
        )

        best_metrics = {
            "precision": float(
                precision
            ),
            "recall": float(
                recall
            ),
            "f1": float(
                f1
            ),
            "f2": float(
                f2
            )
        }


print("\n========================================")
print(" THRESHOLD SEARCH COMPLETE")
print("========================================")

print(
    f"Configurations tested: "
    f"{len(thresholds):,}"
)


# ============================================================
# BEST THRESHOLD
# ============================================================

print("\n========================================")
print(" BEST V7 RISK THRESHOLD")
print("========================================")

print(
    f"Risk threshold : "
    f"{best_threshold:.3f}"
)

print("\nValidation risk metrics:")

print(
    f"Precision : "
    f"{best_metrics['precision']:.4f}"
)

print(
    f"Recall    : "
    f"{best_metrics['recall']:.4f}"
)

print(
    f"F1        : "
    f"{best_metrics['f1']:.4f}"
)

print(
    f"F2        : "
    f"{best_metrics['f2']:.4f}"
)


# ============================================================
# FREEZE THRESHOLD
# ============================================================

risk_threshold = best_threshold


# ============================================================
# VALIDATION RISK PREDICTION
# ============================================================

val_risk_pred = (
    val_risk_probability
    >= risk_threshold
).astype(int)


# ============================================================
# TEST RISK PREDICTION
# ============================================================
#
# The threshold is now frozen.
#
# No test information is used to modify it.
# ============================================================

test_risk_pred = (
    test_risk_probability
    >= risk_threshold
).astype(int)


# ============================================================
# VALIDATION RISK METRICS
# ============================================================

val_risk_precision = precision_score(
    y_val_risk,
    val_risk_pred,
    zero_division=0
)

val_risk_recall = recall_score(
    y_val_risk,
    val_risk_pred,
    zero_division=0
)

val_risk_f1 = f1_score(
    y_val_risk,
    val_risk_pred,
    zero_division=0
)


# ============================================================
# TEST RISK METRICS
# ============================================================

test_risk_precision = precision_score(
    y_test_risk,
    test_risk_pred,
    zero_division=0
)

test_risk_recall = recall_score(
    y_test_risk,
    test_risk_pred,
    zero_division=0
)

test_risk_f1 = f1_score(
    y_test_risk,
    test_risk_pred,
    zero_division=0
)


# ============================================================
# RISK RECALL BY ORIGINAL CLASS
# ============================================================

def class_risk_recall(
    y_true,
    risk_prediction,
    class_id
):

    mask = (
        y_true == class_id
    )

    if mask.sum() == 0:
        return 0.0

    return float(
        risk_prediction[mask].mean()
    )


val_high_risk_recall = class_risk_recall(
    y_val.to_numpy(),
    val_risk_pred,
    CLASS_TO_ID["HIGH"]
)

val_congested_risk_recall = class_risk_recall(
    y_val.to_numpy(),
    val_risk_pred,
    CLASS_TO_ID["CONGESTED"]
)

test_high_risk_recall = class_risk_recall(
    y_test.to_numpy(),
    test_risk_pred,
    CLASS_TO_ID["HIGH"]
)

test_congested_risk_recall = class_risk_recall(
    y_test.to_numpy(),
    test_risk_pred,
    CLASS_TO_ID["CONGESTED"]
)


# ============================================================
# STANDARD 4-CLASS TEST RESULT
# ============================================================

print("\n========================================")
print(" STANDARD 4-CLASS TEST EVALUATION")
print("========================================")

test_accuracy = accuracy_score(
    y_test,
    test_standard_pred
)

test_macro_f1 = f1_score(
    y_test,
    test_standard_pred,
    average="macro"
)

test_weighted_f1 = f1_score(
    y_test,
    test_standard_pred,
    average="weighted"
)

print(
    f"Accuracy    : "
    f"{test_accuracy:.4f}"
)

print(
    f"Macro F1    : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Weighted F1 : "
    f"{test_weighted_f1:.4f}"
)


# ============================================================
# V7 RISK RESULT
# ============================================================

print("\n========================================")
print(" V7 RISK EVALUATION")
print("========================================")

print("\nValidation:")

print(
    f"Risk precision : "
    f"{val_risk_precision:.4f}"
)

print(
    f"Risk recall    : "
    f"{val_risk_recall:.4f}"
)

print(
    f"Risk F1        : "
    f"{val_risk_f1:.4f}"
)

print(
    f"HIGH detected as risk      : "
    f"{val_high_risk_recall:.4f}"
)

print(
    f"CONGESTED detected as risk : "
    f"{val_congested_risk_recall:.4f}"
)


print("\nFinal Test:")

print(
    f"Risk precision : "
    f"{test_risk_precision:.4f}"
)

print(
    f"Risk recall    : "
    f"{test_risk_recall:.4f}"
)

print(
    f"Risk F1        : "
    f"{test_risk_f1:.4f}"
)

print(
    f"HIGH detected as risk      : "
    f"{test_high_risk_recall:.4f}"
)

print(
    f"CONGESTED detected as risk : "
    f"{test_congested_risk_recall:.4f}"
)


# ============================================================
# STANDARD CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print(" TEST CLASSIFICATION REPORT")
print("========================================")

report = classification_report(
    y_test,
    test_standard_pred,
    target_names=CLASS_NAMES,
    digits=4,
    zero_division=0
)

print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n========================================")
print(" TEST CONFUSION MATRIX")
print("========================================")

cm = confusion_matrix(
    y_test,
    test_standard_pred
)

cm_df = pd.DataFrame(
    cm,
    index=CLASS_NAMES,
    columns=CLASS_NAMES
)

print(
    cm_df.to_string()
)


# ============================================================
# RISK CONFUSION MATRIX
# ============================================================

print("\n========================================")
print(" V7 RISK CONFUSION MATRIX")
print("========================================")

risk_cm = confusion_matrix(
    y_test_risk,
    test_risk_pred
)

risk_cm_df = pd.DataFrame(
    risk_cm,
    index=[
        "NON_RISK",
        "RISK"
    ],
    columns=[
        "PRED_NON_RISK",
        "PRED_RISK"
    ]
)

print(
    risk_cm_df.to_string()
)


# ============================================================
# SAVE MODEL
# ============================================================
#
# V7 uses the V6 model directly.
#
# We save a copy under the V7 name so the
# deployment pipeline can identify the complete
# V7 artifact.
# ============================================================

print("\n========================================")
print(" SAVING XGBOOST V7 MODEL")
print("========================================")

model.save_model(
    V7_MODEL
)

print(
    f"Model saved:\n{V7_MODEL}"
)


# ============================================================
# SAVE FEATURES
# ============================================================

with open(
    V7_FEATURES,
    "w"
) as f:

    json.dump(
        features,
        f,
        indent=4
    )

print(
    f"Feature list saved:\n{V7_FEATURES}"
)


# ============================================================
# SAVE THRESHOLD
# ============================================================

threshold_data = {

    "model_version": "v7",

    "base_model": "trafficx_xgboost_v6",

    "risk_definition": {
        "risk_classes": [
            "HIGH",
            "CONGESTED"
        ],
        "formula":
            "P(HIGH) + P(CONGESTED)"
    },

    "threshold": risk_threshold,

    "optimization": {
        "method":
            "validation_only",
        "objective":
            "F2",
        "beta":
            2.0
    },

    "validation_metrics": {
        "precision":
            val_risk_precision,
        "recall":
            val_risk_recall,
        "f1":
            val_risk_f1,
        "high_detected_as_risk":
            val_high_risk_recall,
        "congested_detected_as_risk":
            val_congested_risk_recall
    },

    "test_metrics": {
        "precision":
            test_risk_precision,
        "recall":
            test_risk_recall,
        "f1":
            test_risk_f1,
        "high_detected_as_risk":
            test_high_risk_recall,
        "congested_detected_as_risk":
            test_congested_risk_recall
    }
}


with open(
    V7_THRESHOLDS,
    "w"
) as f:

    json.dump(
        threshold_data,
        f,
        indent=4
    )


print(
    f"Risk threshold saved:\n{V7_THRESHOLDS}"
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

cm_df.to_csv(
    V7_CONFUSION
)

print(
    f"Confusion matrix saved:\n{V7_CONFUSION}"
)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

with open(
    V7_REPORT,
    "w"
) as f:

    f.write(
        report
    )

    f.write(
        "\n\n"
        "========================================\n"
        "V7 RISK METRICS\n"
        "========================================\n\n"
    )

    f.write(
        f"Risk threshold: "
        f"{risk_threshold:.4f}\n"
    )

    f.write(
        f"Risk precision: "
        f"{test_risk_precision:.4f}\n"
    )

    f.write(
        f"Risk recall: "
        f"{test_risk_recall:.4f}\n"
    )

    f.write(
        f"Risk F1: "
        f"{test_risk_f1:.4f}\n"
    )

    f.write(
        f"HIGH detected as risk: "
        f"{test_high_risk_recall:.4f}\n"
    )

    f.write(
        f"CONGESTED detected as risk: "
        f"{test_congested_risk_recall:.4f}\n"
    )


print(
    f"Classification report saved:\n{V7_REPORT}"
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {

    "model": "trafficx_xgboost_v7",

    "base_model": "trafficx_xgboost_v6",

    "dataset":
        "trafficx_xgboost_v3_dataset.csv",

    "prediction_horizon_steps": 300,

    "prediction_horizon_minutes": 5,

    "features": len(features),

    "split": {
        "train": "0-499",
        "validation": "500-599",
        "test": "600-699"
    },

    "standard_validation": {

        "accuracy":
            standard_val_accuracy,

        "macro_f1":
            standard_val_macro_f1,

        "weighted_f1":
            standard_val_weighted_f1
    },

    "standard_test": {

        "accuracy":
            test_accuracy,

        "macro_f1":
            test_macro_f1,

        "weighted_f1":
            test_weighted_f1
    },

    "risk": {

        "risk_definition":
            "HIGH + CONGESTED",

        "threshold":
            risk_threshold,

        "optimization":
            "validation_only_F2",

        "validation": {

            "precision":
                val_risk_precision,

            "recall":
                val_risk_recall,

            "f1":
                val_risk_f1,

            "high_detected_as_risk":
                val_high_risk_recall,

            "congested_detected_as_risk":
                val_congested_risk_recall
        },

        "test": {

            "precision":
                test_risk_precision,

            "recall":
                test_risk_recall,

            "f1":
                test_risk_f1,

            "high_detected_as_risk":
                test_high_risk_recall,

            "congested_detected_as_risk":
                test_congested_risk_recall
        }
    }
}


with open(
    V7_METRICS,
    "w"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )


print(
    f"Metrics saved:\n{V7_METRICS}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print(" TRAFFICX XGBOOST V7 COMPLETE")
print("========================================")

print("\nMODEL")
print("----------------------------------------")
print("trafficx_xgboost_v7.json")
print("(V6 probability model + V7 risk layer)")

print("\nDATASET")
print("----------------------------------------")
print("trafficx_xgboost_v3_dataset.csv")

print("\nFEATURES")
print("----------------------------------------")
print(f"{len(features)} temporal + traffic features")

print("\nPREDICTION")
print("----------------------------------------")
print("5-minute future congestion")

print("\nRISK DEFINITION")
print("----------------------------------------")
print("HIGH + CONGESTED")

print("\nRISK PROBABILITY")
print("----------------------------------------")
print("P(HIGH) + P(CONGESTED)")

print("\nRISK THRESHOLD")
print("----------------------------------------")
print(
    f"{risk_threshold:.3f}"
)

print("\nTHRESHOLD OPTIMIZATION")
print("----------------------------------------")
print("Validation only")
print("F2 objective")
print("Beta = 2.0")

print("\nTEMPORAL SPLIT")
print("----------------------------------------")
print("Train      : steps 0-499")
print("Validation : steps 500-599")
print("Test       : steps 600-699")

print("\nFINAL TEST")
print("----------------------------------------")

print(
    f"Accuracy            : "
    f"{test_accuracy:.4f}"
)

print(
    f"Macro F1            : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Weighted F1         : "
    f"{test_weighted_f1:.4f}"
)

print(
    f"Risk Precision      : "
    f"{test_risk_precision:.4f}"
)

print(
    f"Risk Recall         : "
    f"{test_risk_recall:.4f}"
)

print(
    f"Risk F1             : "
    f"{test_risk_f1:.4f}"
)

print(
    f"HIGH as Risk        : "
    f"{test_high_risk_recall:.4f}"
)

print(
    f"CONGESTED as Risk   : "
    f"{test_congested_risk_recall:.4f}"
)

print("\nOUTPUTS")
print("----------------------------------------")
print("Model:")
print(V7_MODEL)

print("\nFeatures:")
print(V7_FEATURES)

print("\nThresholds:")
print(V7_THRESHOLDS)

print("\nMetrics:")
print(V7_METRICS)

print("\nConfusion:")
print(V7_CONFUSION)

print("\nReport:")
print(V7_REPORT)

print("\n========================================")
print(" TRAFFICX V7 TRAINING FINISHED")
print("========================================")