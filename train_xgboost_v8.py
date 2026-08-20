import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    fbeta_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score
)

# ============================================================
# TRAFFICX - XGBOOST V8
# DEDICATED BINARY RISK MODEL
#
# NON_RISK = LOW + MEDIUM
# RISK     = HIGH + CONGESTED
#
# IMPORTANT:
# - Same dataset as V6/V7
# - Same V6 feature list
# - Same temporal split
# - Independently trained XGBoost model
# - Threshold optimized ONLY on validation using F2
# - Test set remains untouched until final evaluation
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

DATASET = os.path.join(
    BASE_DIR,
    "road_datasets",
    "trafficx_xgboost_v3_dataset.csv"
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

V8_MODEL = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8.json"
)

V8_FEATURES = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8_features.json"
)

V8_THRESHOLDS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8_thresholds.json"
)

V8_METRICS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8_metrics.json"
)

V8_CONFUSION = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8_confusion_matrix.csv"
)

V8_REPORT = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v8_classification_report.txt"
)


os.makedirs(
    MODEL_DIR,
    exist_ok=True
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


# Binary risk mapping
#
# NON_RISK = 0
# RISK     = 1

BINARY_CLASS_NAMES = [
    "NON_RISK",
    "RISK"
]


BINARY_CLASS_TO_ID = {
    "NON_RISK": 0,
    "RISK": 1
}


# ============================================================
# HEADER
# ============================================================

print("\n========================================")
print(" TRAFFICX - XGBOOST V8")
print(" DEDICATED BINARY RISK MODEL")
print("========================================")


print("\nDataset:")
print(DATASET)


print("\nModel type:")
print("Independent binary XGBoost classifier")


print("\nRisk definition:")
print("NON_RISK = LOW + MEDIUM")
print("RISK     = HIGH + CONGESTED")


print("\nPrediction horizon:")
print("5 minutes = 300 simulation steps")


print("\nTemporal split:")
print("Train      : steps 0-499")
print("Validation : steps 500-599")
print("Test       : steps 600-699")


print("\nThreshold strategy:")
print("Validation-only optimization")
print("Objective: F2")
print("Beta = 2.0")


# ============================================================
# LOAD DATASET
# ============================================================

print("\n========================================")
print(" LOADING DATASET")
print("========================================")


df = pd.read_csv(
    DATASET
)


print(
    f"Rows loaded: {len(df):,}"
)


print(
    f"Columns    : {len(df.columns)}"
)


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
# TARGET VALIDATION
# ============================================================

print("\n========================================")
print(" TARGET VALIDATION")
print("========================================")


print(
    "Original target distribution:"
)


print(
    df["future_congestion"].value_counts()
)


unknown_classes = set(
    df["future_congestion"].dropna().unique()
) - set(CLASS_NAMES)


if unknown_classes:

    raise ValueError(
        "Unknown future_congestion classes detected: "
        + str(unknown_classes)
    )


# ============================================================
# LOAD V6 FEATURE LIST
# ============================================================
#
# V8 intentionally uses the exact same feature space
# as V6/V7 for a fair model comparison.
# ============================================================

print("\n========================================")
print(" LOADING V6 FEATURE LIST")
print("========================================")


with open(
    V6_FEATURES,
    "r"
) as f:

    features = json.load(
        f
    )


print(
    f"Number of features: {len(features)}"
)


for i, feature in enumerate(
    features,
    1
):

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

        print(
            feature
        )

    raise ValueError(
        "Dataset does not contain all V6 features."
    )


# ============================================================
# TARGET ENCODING
# ============================================================

print("\n========================================")
print(" TARGET ENCODING")
print("========================================")


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
# BINARY RISK TARGET
# ============================================================
#
# LOW       -> NON_RISK = 0
# MEDIUM    -> NON_RISK = 0
# HIGH      -> RISK = 1
# CONGESTED -> RISK = 1
# ============================================================

df["risk_target"] = (
    df["target_encoded"]
    .isin(
        [
            CLASS_TO_ID["HIGH"],
            CLASS_TO_ID["CONGESTED"]
        ]
    )
    .astype(int)
)


print("\nBinary target distribution:")


binary_distribution = (
    df["risk_target"]
    .value_counts()
    .sort_index()
)


print(
    binary_distribution.rename(
        index={
            0: "NON_RISK",
            1: "RISK"
        }
    )
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


nan_rows = (
    X_all
    .isna()
    .any(axis=1)
    .sum()
)


print(
    f"Rows containing NaN/Inf: "
    f"{nan_rows:,}"
)


if nan_rows > 0:

    print(
        "Removing invalid rows..."
    )

    valid_mask = (
        ~X_all
        .isna()
        .any(axis=1)
    )

    df = (
        df
        .loc[valid_mask]
        .copy()
    )

    X_all = (
        X_all
        .loc[valid_mask]
        .copy()
    )


# ============================================================
# TEMPORAL SPLIT
# ============================================================
#
# EXACTLY MATCHES V7.
#
# Train      : 0-499
# Validation : 500-599
# Test       : 600-699
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


X_train = X_all.loc[
    train_mask
]


X_val = X_all.loc[
    val_mask
]


X_test = X_all.loc[
    test_mask
]


y_train = df.loc[
    train_mask,
    "risk_target"
]


y_val = df.loc[
    val_mask,
    "risk_target"
]


y_test = df.loc[
    test_mask,
    "risk_target"
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
# BINARY CLASS DISTRIBUTION BY SPLIT
# ============================================================

print("\n========================================")
print(" SPLIT CLASS DISTRIBUTION")
print("========================================")


print("\nTRAIN:")

print(
    y_train
    .value_counts()
    .sort_index()
    .rename(
        index={
            0: "NON_RISK",
            1: "RISK"
        }
    )
)


print("\nVALIDATION:")

print(
    y_val
    .value_counts()
    .sort_index()
    .rename(
        index={
            0: "NON_RISK",
            1: "RISK"
        }
    )
)


print("\nTEST:")

print(
    y_test
    .value_counts()
    .sort_index()
    .rename(
        index={
            0: "NON_RISK",
            1: "RISK"
        }
    )
)


# ============================================================
# CLASS IMBALANCE
# ============================================================

negative_count = int(
    (y_train == 0).sum()
)


positive_count = int(
    (y_train == 1).sum()
)


if positive_count == 0:

    raise ValueError(
        "Training set contains no RISK samples."
    )


scale_pos_weight = (
    negative_count
    /
    positive_count
)


print("\n========================================")
print(" CLASS BALANCE")
print("========================================")


print(
    f"NON_RISK samples : "
    f"{negative_count:,}"
)


print(
    f"RISK samples     : "
    f"{positive_count:,}"
)


print(
    f"scale_pos_weight : "
    f"{scale_pos_weight:.4f}"
)


# ============================================================
# TRAIN V8
# ============================================================
#
# This is a genuinely independent binary classifier.
#
# Unlike V7, V8 does NOT load V6 probabilities.
# ============================================================

print("\n========================================")
print(" TRAINING V8")
print("========================================")


v8_model = xgb.XGBClassifier(

    objective="binary:logistic",

    n_estimators=1000,

    learning_rate=0.03,

    max_depth=6,

    min_child_weight=3,

    subsample=0.85,

    colsample_bytree=0.85,

    reg_alpha=0.05,

    reg_lambda=1.5,

    gamma=0.0,

    scale_pos_weight=scale_pos_weight,

    eval_metric="logloss",

    tree_method="hist",

    random_state=42,

    n_jobs=-1,

    early_stopping_rounds=60
)


v8_model.fit(

    X_train,

    y_train,

    eval_set=[
        (X_train, y_train),
        (X_val, y_val)
    ],

    verbose=False
)


print(
    "\nV8 training completed."
)


if hasattr(
    v8_model,
    "best_iteration"
):

    print(
        f"Best iteration: "
        f"{v8_model.best_iteration}"
    )


# ============================================================
# VALIDATION PROBABILITY
# ============================================================

print("\n========================================")
print(" VALIDATION RISK PROBABILITY")
print("========================================")


val_risk_probability = (
    v8_model
    .predict_proba(
        X_val
    )[:, 1]
)


print(
    pd.Series(
        val_risk_probability
    ).describe()
)


# ============================================================
# BASELINE VALIDATION RESULT
# ============================================================

print("\n========================================")
print(" BASELINE VALIDATION RESULT")
print("========================================")


baseline_threshold = 0.50


val_baseline_pred = (
    val_risk_probability
    >= baseline_threshold
).astype(int)


baseline_precision = precision_score(
    y_val,
    val_baseline_pred,
    zero_division=0
)


baseline_recall = recall_score(
    y_val,
    val_baseline_pred,
    zero_division=0
)


baseline_f1 = f1_score(
    y_val,
    val_baseline_pred,
    zero_division=0
)


baseline_f2 = fbeta_score(
    y_val,
    val_baseline_pred,
    beta=2.0,
    zero_division=0
)


print(
    f"Threshold      : "
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


print(
    f"Risk F2        : "
    f"{baseline_f2:.4f}"
)


# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================
#
# ONLY VALIDATION DATA.
#
# Test data is NOT touched.
# ============================================================

print("\n========================================")
print(" OPTIMIZING V8 RISK THRESHOLD")
print("========================================")


thresholds = np.arange(
    0.20,
    0.801,
    0.005
)


best_threshold = None

best_f2 = -1.0

best_metrics = {}


threshold_results = []


for threshold in thresholds:

    pred = (
        val_risk_probability
        >= threshold
    ).astype(int)


    precision = precision_score(
        y_val,
        pred,
        zero_division=0
    )


    recall = recall_score(
        y_val,
        pred,
        zero_division=0
    )


    f1 = f1_score(
        y_val,
        pred,
        zero_division=0
    )


    f2 = fbeta_score(
        y_val,
        pred,
        beta=2.0,
        zero_division=0
    )


    threshold_results.append({

        "threshold":
            float(threshold),

        "precision":
            float(precision),

        "recall":
            float(recall),

        "f1":
            float(f1),

        "f2":
            float(f2)
    })


    #
    # Primary objective:
    # maximize F2.
    #
    # Tie-break:
    # choose the higher threshold.
    #

    if f2 > best_f2:

        best_f2 = f2

        best_threshold = (
            float(threshold)
        )

        best_metrics = {

            "precision":
                float(precision),

            "recall":
                float(recall),

            "f1":
                float(f1),

            "f2":
                float(f2)
        }


    elif np.isclose(
        f2,
        best_f2
    ):

        if (
            best_threshold is None
            or
            threshold > best_threshold
        ):

            best_threshold = (
                float(threshold)
            )

            best_metrics = {

                "precision":
                    float(precision),

                "recall":
                    float(recall),

                "f1":
                    float(f1),

                "f2":
                    float(f2)
            }


threshold_results_df = pd.DataFrame(
    threshold_results
)


# ============================================================
# BEST THRESHOLD
# ============================================================

print("\n========================================")
print(" BEST V8 RISK THRESHOLD")
print("========================================")


print(
    f"Configurations tested: "
    f"{len(thresholds):,}"
)


print(
    f"\nRisk threshold : "
    f"{best_threshold:.3f}"
)


print(
    "\nValidation metrics:"
)


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
# FINAL TEST PROBABILITY
# ============================================================
#
# Threshold has already been frozen.
#
# Now the test set is evaluated exactly once.
# ============================================================

print("\n========================================")
print(" FINAL TEST EVALUATION")
print("========================================")


test_risk_probability = (
    v8_model
    .predict_proba(
        X_test
    )[:, 1]
)


# ============================================================
# FINAL TEST PREDICTION
# ============================================================

test_risk_pred = (
    test_risk_probability
    >= risk_threshold
).astype(int)


# ============================================================
# TEST RISK METRICS
# ============================================================

test_risk_precision = precision_score(
    y_test,
    test_risk_pred,
    zero_division=0
)


test_risk_recall = recall_score(
    y_test,
    test_risk_pred,
    zero_division=0
)


test_risk_f1 = f1_score(
    y_test,
    test_risk_pred,
    zero_division=0
)


test_risk_f2 = fbeta_score(
    y_test,
    test_risk_pred,
    beta=2.0,
    zero_division=0
)


test_accuracy = accuracy_score(
    y_test,
    test_risk_pred
)


# ============================================================
# TEST CONFUSION MATRIX
# ============================================================

risk_cm = confusion_matrix(
    y_test,
    test_risk_pred,
    labels=[
        0,
        1
    ]
)


risk_cm_df = pd.DataFrame(

    risk_cm,

    index=[
        "ACTUAL_NON_RISK",
        "ACTUAL_RISK"
    ],

    columns=[
        "PRED_NON_RISK",
        "PRED_RISK"
    ]
)


# ============================================================
# TEST CLASSIFICATION REPORT
# ============================================================

binary_report = classification_report(

    y_test,

    test_risk_pred,

    labels=[
        0,
        1
    ],

    target_names=[
        "NON_RISK",
        "RISK"
    ],

    digits=4,

    zero_division=0
)


# ============================================================
# PRINT FINAL BINARY RESULT
# ============================================================

print("\n========================================")
print(" V8 BINARY RISK PERFORMANCE")
print("========================================")


print(
    f"Risk Precision : "
    f"{test_risk_precision:.4f}"
)


print(
    f"Risk Recall    : "
    f"{test_risk_recall:.4f}"
)


print(
    f"Risk F1        : "
    f"{test_risk_f1:.4f}"
)


print(
    f"Risk F2        : "
    f"{test_risk_f2:.4f}"
)


print(
    f"Accuracy       : "
    f"{test_accuracy:.4f}"
)


print("\nRisk confusion matrix:")


print(
    risk_cm_df.to_string()
)


print("\nClassification report:")


print(
    binary_report
)


# ============================================================
# HIGH / CONGESTED DETECTION
# ============================================================
#
# Although V8 is binary, we retain the original four-class
# ground truth to determine:
#
# - What percentage of HIGH samples were detected as RISK?
# - What percentage of CONGESTED samples were detected as RISK?
#
# This is useful for hackathon interpretation.
# ============================================================

print("\n========================================")
print(" HIGH / CONGESTED RISK DETECTION")
print("========================================")


test_original_classes = (
    df.loc[
        test_mask,
        "target_encoded"
    ]
    .to_numpy()
)


def class_detected_as_risk(
    y_original,
    risk_prediction,
    class_id
):

    mask = (
        y_original == class_id
    )

    if mask.sum() == 0:

        return 0.0

    return float(
        risk_prediction[mask]
        .mean()
    )


test_high_detected_as_risk = (
    class_detected_as_risk(
        test_original_classes,
        test_risk_pred,
        CLASS_TO_ID["HIGH"]
    )
)


test_congested_detected_as_risk = (
    class_detected_as_risk(
        test_original_classes,
        test_risk_pred,
        CLASS_TO_ID["CONGESTED"]
    )
)


print(
    f"HIGH detected as RISK      : "
    f"{test_high_detected_as_risk:.4f}"
)


print(
    f"CONGESTED detected as RISK : "
    f"{test_congested_detected_as_risk:.4f}"
)


# ============================================================
# 4-CLASS GROUND-TRUTH DISTRIBUTION
# ============================================================
#
# V8 is binary, so this is NOT a 4-class prediction metric.
#
# It simply documents the original test distribution.
# ============================================================

test_four_class_distribution = (

    df.loc[
        test_mask,
        "future_congestion"
    ]

    .value_counts()

    .reindex(
        CLASS_NAMES,
        fill_value=0
    )

    .to_dict()
)


print("\n========================================")
print(" ORIGINAL 4-CLASS TEST DISTRIBUTION")
print("========================================")


for class_name in CLASS_NAMES:

    print(
        f"{class_name:10s}: "
        f"{test_four_class_distribution[class_name]:,}"
    )


# ============================================================
# SAVE MODEL
# ============================================================

print("\n========================================")
print(" SAVING V8 MODEL")
print("========================================")


v8_model.save_model(
    V8_MODEL
)


print(
    f"Model saved:\n{V8_MODEL}"
)


# ============================================================
# SAVE FEATURES
# ============================================================

feature_data = {

    "model_version":
        "trafficx_xgboost_v8",

    "base_feature_source":
        "trafficx_xgboost_v6_features.json",

    "task":
        "binary_risk_classification",

    "features":
        features,

    "feature_count":
        len(features),

    "target":
        "future_congestion",

    "binary_mapping": {

        "NON_RISK": [
            "LOW",
            "MEDIUM"
        ],

        "RISK": [
            "HIGH",
            "CONGESTED"
        ]
    },

    "prediction_horizon_steps":
        300,

    "prediction_horizon_minutes":
        5
}


with open(
    V8_FEATURES,
    "w"
) as f:

    json.dump(
        feature_data,
        f,
        indent=4
    )


print(
    f"Feature list saved:\n{V8_FEATURES}"
)


# ============================================================
# SAVE THRESHOLD DATA
# ============================================================

threshold_data = {

    "model_version":
        "v8",

    "model_type":
        "independent_binary_xgboost",

    "risk_definition": {

        "non_risk_classes": [
            "LOW",
            "MEDIUM"
        ],

        "risk_classes": [
            "HIGH",
            "CONGESTED"
        ]
    },

    "threshold":
        risk_threshold,

    "optimization": {

        "method":
            "validation_only",

        "objective":
            "F2",

        "beta":
            2.0,

        "threshold_range":
            "0.20-0.80",

        "threshold_step":
            0.005
    },

    "validation_metrics": {

        "precision":
            best_metrics["precision"],

        "recall":
            best_metrics["recall"],

        "f1":
            best_metrics["f1"],

        "f2":
            best_metrics["f2"]
    },

    "test_metrics": {

        "precision":
            test_risk_precision,

        "recall":
            test_risk_recall,

        "f1":
            test_risk_f1,

        "f2":
            test_risk_f2
    }
}


with open(
    V8_THRESHOLDS,
    "w"
) as f:

    json.dump(
        threshold_data,
        f,
        indent=4
    )


print(
    f"Threshold data saved:\n{V8_THRESHOLDS}"
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

risk_cm_df.to_csv(
    V8_CONFUSION
)


print(
    f"Confusion matrix saved:\n{V8_CONFUSION}"
)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

with open(
    V8_REPORT,
    "w"
) as f:

    f.write(
        "TRAFFICX XGBOOST V8\n"
    )

    f.write(
        "DEDICATED BINARY RISK MODEL\n"
    )

    f.write(
        "========================================\n\n"
    )

    f.write(
        "Risk definition:\n"
    )

    f.write(
        "NON_RISK = LOW + MEDIUM\n"
    )

    f.write(
        "RISK     = HIGH + CONGESTED\n\n"
    )

    f.write(
        f"Risk threshold: "
        f"{risk_threshold:.4f}\n\n"
    )

    f.write(
        "BINARY RISK PERFORMANCE\n"
    )

    f.write(
        "----------------------------------------\n"
    )

    f.write(
        f"Risk Precision : "
        f"{test_risk_precision:.4f}\n"
    )

    f.write(
        f"Risk Recall    : "
        f"{test_risk_recall:.4f}\n"
    )

    f.write(
        f"Risk F1        : "
        f"{test_risk_f1:.4f}\n"
    )

    f.write(
        f"Risk F2        : "
        f"{test_risk_f2:.4f}\n"
    )

    f.write(
        f"Accuracy       : "
        f"{test_accuracy:.4f}\n\n"
    )

    f.write(
        f"HIGH detected as RISK      : "
        f"{test_high_detected_as_risk:.4f}\n"
    )

    f.write(
        f"CONGESTED detected as RISK : "
        f"{test_congested_detected_as_risk:.4f}\n\n"
    )

    f.write(
        "CLASSIFICATION REPORT\n"
    )

    f.write(
        "----------------------------------------\n"
    )

    f.write(
        binary_report
    )

    f.write(
        "\n\n"
        "ORIGINAL 4-CLASS TEST DISTRIBUTION\n"
    )

    f.write(
        "----------------------------------------\n"
    )

    for class_name in CLASS_NAMES:

        f.write(
            f"{class_name:10s}: "
            f"{test_four_class_distribution[class_name]:,}\n"
        )


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {

    "model":
        "trafficx_xgboost_v8",

    "model_type":
        "independent_binary_xgboost",

    "dataset":
        "trafficx_xgboost_v3_dataset.csv",

    "feature_source":
        "trafficx_xgboost_v6_features.json",

    "features":
        len(features),

    "prediction_horizon_steps":
        300,

    "prediction_horizon_minutes":
        5,

    "risk_definition":
        "HIGH + CONGESTED",

    "binary_mapping": {

        "NON_RISK":
            "LOW + MEDIUM",

        "RISK":
            "HIGH + CONGESTED"
    },

    "split": {

        "train":
            "0-499",

        "validation":
            "500-599",

        "test":
            "600-699"
    },

    "threshold": {

        "value":
            risk_threshold,

        "optimization":
            "validation_only_F2",

        "beta":
            2.0
    },

    "validation": {

        "risk_precision":
            best_metrics["precision"],

        "risk_recall":
            best_metrics["recall"],

        "risk_f1":
            best_metrics["f1"],

        "risk_f2":
            best_metrics["f2"]
    },

    "test": {

        "accuracy":
            test_accuracy,

        "risk_precision":
            test_risk_precision,

        "risk_recall":
            test_risk_recall,

        "risk_f1":
            test_risk_f1,

        "risk_f2":
            test_risk_f2,

        "high_detected_as_risk":
            test_high_detected_as_risk,

        "congested_detected_as_risk":
            test_congested_detected_as_risk
    },

    "original_four_class_test_distribution":
        {
            key: int(value)
            for key, value
            in test_four_class_distribution.items()
        }
}


with open(
    V8_METRICS,
    "w"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )


print(
    f"Metrics saved:\n{V8_METRICS}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print(" TRAFFICX XGBOOST V8 COMPLETE")
print("========================================")


print("\nMODEL")
print("----------------------------------------")

print(
    "trafficx_xgboost_v8.json"
)

print(
    "(independently trained binary XGBoost)"
)


print("\nRISK DEFINITION")
print("----------------------------------------")

print(
    "NON_RISK = LOW + MEDIUM"
)

print(
    "RISK     = HIGH + CONGESTED"
)


print("\nPREDICTION")
print("----------------------------------------")

print(
    "5-minute future congestion risk"
)


print("\nTEMPORAL SPLIT")
print("----------------------------------------")

print(
    "Train      : steps 0-499"
)

print(
    "Validation : steps 500-599"
)

print(
    "Test       : steps 600-699"
)


print("\nFEATURES")
print("----------------------------------------")

print(
    f"{len(features)} V6-compatible features"
)


print("\nTHRESHOLD")
print("----------------------------------------")

print(
    f"{risk_threshold:.3f}"
)


print("\nTHRESHOLD OPTIMIZATION")
print("----------------------------------------")

print(
    "Validation only"
)

print(
    "F2 objective"
)

print(
    "Beta = 2.0"
)


print("\nFINAL TEST")
print("----------------------------------------")


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
    f"Risk F2             : "
    f"{test_risk_f2:.4f}"
)


print(
    f"Accuracy            : "
    f"{test_accuracy:.4f}"
)


print(
    f"HIGH as Risk        : "
    f"{test_high_detected_as_risk:.4f}"
)


print(
    f"CONGESTED as Risk   : "
    f"{test_congested_detected_as_risk:.4f}"
)


print("\nOUTPUTS")
print("----------------------------------------")


print("Model:")
print(V8_MODEL)


print("\nFeatures:")
print(V8_FEATURES)


print("\nThresholds:")
print(V8_THRESHOLDS)


print("\nMetrics:")
print(V8_METRICS)


print("\nConfusion:")
print(V8_CONFUSION)


print("\nReport:")
print(V8_REPORT)


print("\n========================================")
print(" TRAFFICX V8 TRAINING FINISHED")
print("========================================")