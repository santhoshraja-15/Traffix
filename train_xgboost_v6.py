import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ============================================================
# TRAFFICX - XGBOOST V6
# PROBABILITY-BASED RISK-AWARE PREDICTION
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

DATASET = os.path.join(
    BASE_DIR,
    "road_datasets",
    "trafficx_xgboost_v3_dataset.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6.json"
)

FEATURE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_features.json"
)

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_metrics.json"
)

THRESHOLD_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_thresholds.json"
)

IMPORTANCE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_feature_importance.csv"
)

CONFUSION_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_confusion_matrix.csv"
)

REPORT_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v6_classification_report.txt"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

TARGET = "future_congestion"

TRAIN_MAX_STEP = 499
VAL_MIN_STEP = 500
VAL_MAX_STEP = 599
TEST_MIN_STEP = 600
TEST_MAX_STEP = 699

# Class order
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


# ============================================================
# MODERATE CLASS WEIGHTS
# ============================================================
#
# V5:
#
# LOW        1.0
# MEDIUM     5.0
# HIGH       7.0
# CONGESTED  2.5
#
# V6 deliberately uses moderate weights.
#
# The final risk sensitivity is handled by the probability
# decision layer instead of aggressively distorting training.
# ============================================================

CLASS_WEIGHTS = {
    "LOW": 1.0,
    "MEDIUM": 3.0,
    "HIGH": 4.0,
    "CONGESTED": 2.0
}


# ============================================================
# PRINT HEADER
# ============================================================

print("""
========================================
 TRAFFICX - XGBOOST V6
 PROBABILITY-BASED RISK-AWARE MODEL
========================================
""")

print("Dataset:")
print(DATASET)

print("""
Prediction horizon:
5 minutes = 300 simulation steps
""")

print("""
Temporal split:
Train      : steps 0-499
Validation : steps 500-599
Test       : steps 600-699
""")

print("""
V6 strategy:
1. Train multiclass XGBoost
2. Generate validation probabilities
3. Optimize risk-aware decision thresholds
4. Freeze thresholds
5. Evaluate final test set
""")

print("""
Class weights:
LOW        : 1.0
MEDIUM     : 3.0
HIGH       : 4.0
CONGESTED  : 2.0
""")


# ============================================================
# LOAD DATASET
# ============================================================

print("""
========================================
 LOADING DATASET
========================================
""")

df = pd.read_csv(DATASET)

print(f"Rows loaded: {len(df):,}")
print(f"Columns    : {len(df.columns)}")


# ============================================================
# BASIC VALIDATION
# ============================================================

required_columns = [
    "scenario",
    "step",
    "road_id",
    TARGET
]

for col in required_columns:

    if col not in df.columns:

        raise ValueError(
            f"Required column missing: {col}"
        )


print("""
========================================
 DATASET VALIDATION
========================================
""")

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
# TARGET ENCODING
# ============================================================

print("""
========================================
 TARGET ENCODING
========================================
""")

unknown_targets = set(
    df[TARGET].dropna().unique()
) - set(CLASS_TO_ID.keys())

if unknown_targets:

    raise ValueError(
        f"Unknown target classes: {unknown_targets}"
    )

df["target_encoded"] = (
    df[TARGET]
    .map(CLASS_TO_ID)
    .astype(int)
)

print(
    df[TARGET]
    .value_counts()
)


# ============================================================
# FEATURE LIST
# ============================================================
#
# Automatically use all numeric model features except:
#
# scenario
# step
# road_id
# target
# target_encoded
#
# This keeps the exact V3 46-feature dataset structure.
# ============================================================

EXCLUDED_COLUMNS = [
    "scenario",
    "step",
    "road_id",
    TARGET,
    "target_encoded"
]

feature_columns = [
    col
    for col in df.columns
    if col not in EXCLUDED_COLUMNS
]

# Only numeric columns
feature_columns = [
    col
    for col in feature_columns
    if pd.api.types.is_numeric_dtype(
        df[col]
    )
]

print("""
========================================
 FEATURE CONFIGURATION
========================================
""")

print(
    f"Number of features: "
    f"{len(feature_columns)}"
)

for i, feature in enumerate(
    feature_columns,
    start=1
):

    print(
        f"{i:02d}. {feature}"
    )


if len(feature_columns) != 46:

    print("""
WARNING:
Expected 46 V3 features.
The dataset currently contains:
""")

    print(
        len(feature_columns)
    )


# ============================================================
# REMOVE INVALID FEATURE VALUES
# ============================================================

print("""
========================================
 FEATURE CLEANING
========================================
""")

X_all = df[feature_columns].copy()

X_all = X_all.replace(
    [np.inf, -np.inf],
    np.nan
)

invalid_rows = X_all.isna().any(axis=1).sum()

print(
    f"Rows containing NaN/Inf: "
    f"{invalid_rows:,}"
)

if invalid_rows > 0:

    valid_mask = ~X_all.isna().any(axis=1)

    df = df.loc[
        valid_mask
    ].copy()

    X_all = X_all.loc[
        valid_mask
    ].copy()

    print(
        f"Rows after cleaning: "
        f"{len(df):,}"
    )


# ============================================================
# TEMPORAL SPLIT
# ============================================================

print("""
========================================
 TEMPORAL SPLIT
========================================
""")

train_mask = (
    df["step"] <= TRAIN_MAX_STEP
)

val_mask = (
    (df["step"] >= VAL_MIN_STEP) &
    (df["step"] <= VAL_MAX_STEP)
)

test_mask = (
    (df["step"] >= TEST_MIN_STEP) &
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


# ============================================================
# VERIFY TEMPORAL SPLIT
# ============================================================

if len(X_train) == 0:
    raise ValueError("Training set is empty.")

if len(X_val) == 0:
    raise ValueError("Validation set is empty.")

if len(X_test) == 0:
    raise ValueError("Test set is empty.")


print("""
Train step range:
""")

print(
    df.loc[
        train_mask,
        "step"
    ].min(),
    "-",
    df.loc[
        train_mask,
        "step"
    ].max()
)

print("""
Validation step range:
""")

print(
    df.loc[
        val_mask,
        "step"
    ].min(),
    "-",
    df.loc[
        val_mask,
        "step"
    ].max()
)

print("""
Test step range:
""")

print(
    df.loc[
        test_mask,
        "step"
    ].min(),
    "-",
    df.loc[
        test_mask,
        "step"
    ].max()
)


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("""
========================================
 TRAIN TARGET DISTRIBUTION
========================================
""")

train_distribution = (
    y_train
    .map(ID_TO_CLASS)
    .value_counts()
)

print(
    train_distribution
)

print("""
========================================
 VALIDATION TARGET DISTRIBUTION
========================================
""")

print(
    y_val
    .map(ID_TO_CLASS)
    .value_counts()
)

print("""
========================================
 TEST TARGET DISTRIBUTION
========================================
""")

print(
    y_test
    .map(ID_TO_CLASS)
    .value_counts()
)


# ============================================================
# SAMPLE WEIGHTS
# ============================================================

print("""
========================================
 BUILDING SAMPLE WEIGHTS
========================================
""")

sample_weights = np.array([
    CLASS_WEIGHTS[
        ID_TO_CLASS[int(label)]
    ]
    for label in y_train
])

print(
    pd.Series(sample_weights)
    .value_counts()
    .sort_index()
)


# ============================================================
# XGBOOST MODEL
# ============================================================

print("""
========================================
 BUILDING XGBOOST V6
========================================
""")

model = xgb.XGBClassifier(

    objective="multi:softprob",

    num_class=4,

    n_estimators=700,

    max_depth=7,

    learning_rate=0.045,

    min_child_weight=4,

    subsample=0.85,

    colsample_bytree=0.85,

    gamma=0.05,

    reg_alpha=0.15,

    reg_lambda=2.0,

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
 TRAINING XGBOOST V6
========================================
""")

print("Training...")
print("This may take some time.")

model.fit(
    X_train,
    y_train,
    sample_weight=sample_weights,

    eval_set=[
        (X_train, y_train),
        (X_val, y_val)
    ],

    verbose=50
)

print("""
========================================
 TRAINING COMPLETE
========================================
""")


# ============================================================
# STANDARD VALIDATION PROBABILITIES
# ============================================================

print("""
========================================
 VALIDATION PROBABILITIES
========================================
""")

val_probabilities = model.predict_proba(
    X_val
)

print(
    "Validation probability matrix:"
)

print(
    val_probabilities.shape
)


# ============================================================
# STANDARD ARGMAX VALIDATION
# ============================================================

val_pred_standard = np.argmax(
    val_probabilities,
    axis=1
)

standard_val_accuracy = accuracy_score(
    y_val,
    val_pred_standard
)

standard_val_macro_f1 = f1_score(
    y_val,
    val_pred_standard,
    average="macro"
)

standard_val_weighted_f1 = f1_score(
    y_val,
    val_pred_standard,
    average="weighted"
)

print("""
========================================
 STANDARD VALIDATION RESULT
========================================
""")

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
# RISK-AWARE DECISION FUNCTION
# ============================================================
#
# The model outputs:
#
# LOW probability
# MEDIUM probability
# HIGH probability
# CONGESTED probability
#
# We introduce decision thresholds.
#
# HIGH and CONGESTED can override LOW/MEDIUM when their
# probabilities are sufficiently strong.
#
# The thresholds are learned ONLY from validation data.
# ============================================================

def risk_aware_predict(
    probabilities,
    high_threshold,
    congested_threshold,
    medium_threshold
):

    predictions = []

    for prob in probabilities:

        low_p = prob[0]
        medium_p = prob[1]
        high_p = prob[2]
        congested_p = prob[3]

        # ----------------------------------------------------
        # Highest-risk class first
        # ----------------------------------------------------

        if congested_p >= congested_threshold:

            prediction = 3

        elif high_p >= high_threshold:

            prediction = 2

        elif medium_p >= medium_threshold:

            prediction = 1

        else:

            prediction = int(
                np.argmax(prob)
            )

        predictions.append(
            prediction
        )

    return np.array(
        predictions,
        dtype=int
    )


# ============================================================
# THRESHOLD SEARCH
# ============================================================
#
# IMPORTANT:
# This search uses VALIDATION only.
#
# Test data is not touched here.
# ============================================================

print("""
========================================
 OPTIMIZING RISK THRESHOLDS
========================================
""")

print("""
Searching validation thresholds...
""")

# Candidate threshold ranges
high_thresholds = np.arange(
    0.10,
    0.61,
    0.025
)

congested_thresholds = np.arange(
    0.15,
    0.71,
    0.025
)

medium_thresholds = np.arange(
    0.15,
    0.71,
    0.025
)


# ============================================================
# OBJECTIVE
# ============================================================
#
# We don't want a model that simply predicts HIGH everywhere.
#
# Therefore we optimize a combination of:
#
# Macro F1
# HIGH recall
# CONGESTED recall
#
# Macro F1 remains the primary objective.
# ============================================================

best_result = None

search_count = 0

for high_threshold in high_thresholds:

    for congested_threshold in congested_thresholds:

        for medium_threshold in medium_thresholds:

            search_count += 1

            pred = risk_aware_predict(

                val_probabilities,

                high_threshold=
                    high_threshold,

                congested_threshold=
                    congested_threshold,

                medium_threshold=
                    medium_threshold
            )

            macro_f1 = f1_score(
                y_val,
                pred,
                average="macro"
            )

            weighted_f1 = f1_score(
                y_val,
                pred,
                average="weighted"
            )

            accuracy = accuracy_score(
                y_val,
                pred
            )

            # Per-class recall
            report = classification_report(
                y_val,
                pred,
                labels=[0, 1, 2, 3],
                output_dict=True,
                zero_division=0
            )

            high_recall = report[
                "2"
            ]["recall"]

            congested_recall = report[
                "3"
            ]["recall"]

            risk_recall = (
                (
                    (y_val == 2) |
                    (y_val == 3)
                )
            )

            risk_pred = (
                (pred == 2) |
                (pred == 3)
            )

            risk_tp = (
                risk_recall &
                risk_pred
            ).sum()

            risk_total = (
                risk_recall
            ).sum()

            risk_recall_value = (
                risk_tp / risk_total
                if risk_total > 0
                else 0
            )

            # ------------------------------------------------
            # PRIMARY OBJECTIVE
            #
            # Macro F1 first.
            # Risk recall acts as secondary objective.
            # ------------------------------------------------

            score = (
                macro_f1
                + 0.10 * risk_recall_value
                + 0.03 * high_recall
            )

            result = {

                "score": score,

                "macro_f1": macro_f1,

                "weighted_f1":
                    weighted_f1,

                "accuracy":
                    accuracy,

                "high_recall":
                    high_recall,

                "congested_recall":
                    congested_recall,

                "risk_recall":
                    risk_recall_value,

                "high_threshold":
                    float(high_threshold),

                "congested_threshold":
                    float(congested_threshold),

                "medium_threshold":
                    float(medium_threshold)
            }

            if (
                best_result is None
                or result["score"]
                > best_result["score"]
            ):

                best_result = result


print("""
========================================
 THRESHOLD SEARCH COMPLETE
========================================
""")

print(
    f"Configurations tested: "
    f"{search_count:,}"
)


# ============================================================
# BEST THRESHOLDS
# ============================================================

best_high_threshold = (
    best_result[
        "high_threshold"
    ]
)

best_congested_threshold = (
    best_result[
        "congested_threshold"
    ]
)

best_medium_threshold = (
    best_result[
        "medium_threshold"
    ]
)

print("""
========================================
 BEST VALIDATION THRESHOLDS
========================================
""")

print(
    f"HIGH threshold       : "
    f"{best_high_threshold:.3f}"
)

print(
    f"CONGESTED threshold  : "
    f"{best_congested_threshold:.3f}"
)

print(
    f"MEDIUM threshold     : "
    f"{best_medium_threshold:.3f}"
)

print("""
Validation optimized metrics:
""")

print(
    f"Accuracy             : "
    f"{best_result['accuracy']:.4f}"
)

print(
    f"Macro F1             : "
    f"{best_result['macro_f1']:.4f}"
)

print(
    f"Weighted F1          : "
    f"{best_result['weighted_f1']:.4f}"
)

print(
    f"HIGH recall          : "
    f"{best_result['high_recall']:.4f}"
)

print(
    f"CONGESTED recall     : "
    f"{best_result['congested_recall']:.4f}"
)

print(
    f"HIGH + CONGESTED     : "
    f"{best_result['risk_recall']:.4f}"
)


# ============================================================
# FINAL VALIDATION PREDICTIONS
# ============================================================

val_pred = risk_aware_predict(

    val_probabilities,

    high_threshold=
        best_high_threshold,

    congested_threshold=
        best_congested_threshold,

    medium_threshold=
        best_medium_threshold
)


# ============================================================
# FINAL VALIDATION METRICS
# ============================================================

validation_accuracy = accuracy_score(
    y_val,
    val_pred
)

validation_macro_f1 = f1_score(
    y_val,
    val_pred,
    average="macro"
)

validation_weighted_f1 = f1_score(
    y_val,
    val_pred,
    average="weighted"
)

validation_report = classification_report(
    y_val,
    val_pred,

    labels=[0, 1, 2, 3],

    target_names=CLASS_NAMES,

    digits=4,

    zero_division=0
)


# ============================================================
# FINAL TEST PREDICTION
# ============================================================
#
# IMPORTANT:
#
# The thresholds were selected using validation only.
#
# Now they are frozen.
#
# The test set is evaluated exactly once using those thresholds.
# ============================================================

print("""
========================================
 FINAL TEST EVALUATION
========================================
""")

test_probabilities = model.predict_proba(
    X_test
)

test_pred = risk_aware_predict(

    test_probabilities,

    high_threshold=
        best_high_threshold,

    congested_threshold=
        best_congested_threshold,

    medium_threshold=
        best_medium_threshold
)


# ============================================================
# TEST METRICS
# ============================================================

test_accuracy = accuracy_score(
    y_test,
    test_pred
)

test_macro_f1 = f1_score(
    y_test,
    test_pred,
    average="macro"
)

test_weighted_f1 = f1_score(
    y_test,
    test_pred,
    average="weighted"
)

test_report_dict = classification_report(
    y_test,
    test_pred,

    labels=[0, 1, 2, 3],

    target_names=CLASS_NAMES,

    output_dict=True,

    zero_division=0
)

test_report = classification_report(
    y_test,
    test_pred,

    labels=[0, 1, 2, 3],

    target_names=CLASS_NAMES,

    digits=4,

    zero_division=0
)


# ============================================================
# RISK METRICS
# ============================================================

high_recall = test_report_dict[
    "HIGH"
]["recall"]

congested_recall = test_report_dict[
    "CONGESTED"
]["recall"]

risk_actual = (
    (y_test == CLASS_TO_ID["HIGH"]) |
    (y_test == CLASS_TO_ID["CONGESTED"])
)

risk_predicted = (
    (test_pred == CLASS_TO_ID["HIGH"]) |
    (test_pred == CLASS_TO_ID["CONGESTED"])
)

risk_tp = (
    risk_actual &
    risk_predicted
).sum()

risk_total = risk_actual.sum()

risk_recall = (
    risk_tp / risk_total
    if risk_total > 0
    else 0
)


# ============================================================
# PRINT FINAL RESULTS
# ============================================================

print("""
========================================
 VALIDATION EVALUATION
========================================
""")

print(
    f"Validation Accuracy     : "
    f"{validation_accuracy:.4f}"
)

print(
    f"Validation Macro F1     : "
    f"{validation_macro_f1:.4f}"
)

print(
    f"Validation Weighted F1  : "
    f"{validation_weighted_f1:.4f}"
)


print("""
========================================
 FINAL TEST EVALUATION
========================================
""")

print(
    f"Test Accuracy           : "
    f"{test_accuracy:.4f}"
)

print(
    f"Test Macro F1           : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Test Weighted F1        : "
    f"{test_weighted_f1:.4f}"
)


print("""
========================================
 TEST CLASSIFICATION REPORT
========================================
""")

print(
    test_report
)

print("""
========================================
 RISK-AWARE METRICS
========================================
""")

print(
    f"HIGH recall             : "
    f"{high_recall:.4f}"
)

print(
    f"CONGESTED recall        : "
    f"{congested_recall:.4f}"
)

print(
    f"HIGH + CONGESTED recall: "
    f"{risk_recall:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("""
========================================
 TEST CONFUSION MATRIX
========================================
""")

cm = confusion_matrix(
    y_test,
    test_pred,
    labels=[0, 1, 2, 3]
)

cm_df = pd.DataFrame(
    cm,

    index=CLASS_NAMES,

    columns=CLASS_NAMES
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

importance_df = pd.DataFrame({

    "feature":
        feature_columns,

    "importance":
        model.feature_importances_

})

importance_df = (
    importance_df
    .sort_values(
        "importance",
        ascending=False
    )
    .reset_index(drop=True)
)

print(
    importance_df.to_string(
        index=False
    )
)


print("""
========================================
 TOP 15 FEATURES
========================================
""")

print(
    importance_df
    .head(15)
    .to_string(index=False)
)


# ============================================================
# SAVE MODEL
# ============================================================

print("""
========================================
 SAVING XGBOOST V6 MODEL
========================================
""")

model.save_model(
    MODEL_FILE
)

print(
    f"Model saved:\n{MODEL_FILE}"
)


# ============================================================
# SAVE FEATURE LIST
# ============================================================

with open(
    FEATURE_FILE,
    "w"
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
# SAVE THRESHOLDS
# ============================================================

threshold_data = {

    "model_version":
        "trafficx_xgboost_v6",

    "thresholds": {

        "HIGH":
            best_high_threshold,

        "CONGESTED":
            best_congested_threshold,

        "MEDIUM":
            best_medium_threshold
    },

    "optimization_dataset":
        "validation",

    "test_used_for_optimization":
        False,

    "objective":
        "macro_f1 + risk-aware recall",

    "class_weights":
        CLASS_WEIGHTS
}

with open(
    THRESHOLD_FILE,
    "w"
) as f:

    json.dump(
        threshold_data,
        f,
        indent=4
    )

print(
    f"Thresholds saved:\n"
    f"{THRESHOLD_FILE}"
)


# ============================================================
# SAVE FEATURE IMPORTANCE
# ============================================================

importance_df.to_csv(
    IMPORTANCE_FILE,
    index=False
)

print(
    f"Feature importance saved:\n"
    f"{IMPORTANCE_FILE}"
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

cm_df.to_csv(
    CONFUSION_FILE
)

print(
    f"Confusion matrix saved:\n"
    f"{CONFUSION_FILE}"
)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

with open(
    REPORT_FILE,
    "w"
) as f:

    f.write(
        "TRAFFICX XGBOOST V6\n"
    )

    f.write(
        "===================\n\n"
    )

    f.write(
        "Validation Metrics\n"
    )

    f.write(
        f"Accuracy    : "
        f"{validation_accuracy:.4f}\n"
    )

    f.write(
        f"Macro F1    : "
        f"{validation_macro_f1:.4f}\n"
    )

    f.write(
        f"Weighted F1 : "
        f"{validation_weighted_f1:.4f}\n\n"
    )

    f.write(
        "Optimized Thresholds\n"
    )

    f.write(
        f"HIGH       : "
        f"{best_high_threshold:.4f}\n"
    )

    f.write(
        f"MEDIUM     : "
        f"{best_medium_threshold:.4f}\n"
    )

    f.write(
        f"CONGESTED  : "
        f"{best_congested_threshold:.4f}\n\n"
    )

    f.write(
        "Test Metrics\n"
    )

    f.write(
        f"Accuracy    : "
        f"{test_accuracy:.4f}\n"
    )

    f.write(
        f"Macro F1    : "
        f"{test_macro_f1:.4f}\n"
    )

    f.write(
        f"Weighted F1 : "
        f"{test_weighted_f1:.4f}\n"
    )

    f.write(
        f"HIGH Recall : "
        f"{high_recall:.4f}\n"
    )

    f.write(
        f"CONGESTED Recall : "
        f"{congested_recall:.4f}\n"
    )

    f.write(
        f"Risk Recall : "
        f"{risk_recall:.4f}\n\n"
    )

    f.write(
        "Classification Report\n"
    )

    f.write(
        "=====================\n\n"
    )

    f.write(
        test_report
    )

print(
    f"Classification report saved:\n"
    f"{REPORT_FILE}"
)


# ============================================================
# SAVE METRICS JSON
# ============================================================

metrics = {

    "model":
        "trafficx_xgboost_v6",

    "dataset":
        "trafficx_xgboost_v3_dataset.csv",

    "prediction_horizon_steps":
        300,

    "prediction_horizon_minutes":
        5,

    "feature_count":
        len(feature_columns),

    "train_steps":
        "0-499",

    "validation_steps":
        "500-599",

    "test_steps":
        "600-699",

    "class_weights":
        CLASS_WEIGHTS,

    "thresholds":
        {

            "HIGH":
                best_high_threshold,

            "MEDIUM":
                best_medium_threshold,

            "CONGESTED":
                best_congested_threshold
        },

    "validation":
        {

            "accuracy":
                validation_accuracy,

            "macro_f1":
                validation_macro_f1,

            "weighted_f1":
                validation_weighted_f1
        },

    "test":
        {

            "accuracy":
                test_accuracy,

            "macro_f1":
                test_macro_f1,

            "weighted_f1":
                test_weighted_f1,

            "high_recall":
                high_recall,

            "congested_recall":
                congested_recall,

            "high_congested_recall":
                risk_recall
        }
}

with open(
    METRICS_FILE,
    "w"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )

print(
    f"Metrics saved:\n"
    f"{METRICS_FILE}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("""
========================================
 TRAFFICX XGBOOST V6 COMPLETE
========================================
""")

print("""
MODEL
----------------------------------------
trafficx_xgboost_v6.json
""")

print("""
DATASET
----------------------------------------
trafficx_xgboost_v3_dataset.csv
""")

print("""
FEATURES
----------------------------------------
46 temporal + traffic features
""")

print("""
PREDICTION
----------------------------------------
5-minute future congestion
""")

print("""
TEMPORAL SPLIT
----------------------------------------
Train      : steps 0-499
Validation : steps 500-599
Test       : steps 600-699
""")

print("""
CLASS WEIGHTS
----------------------------------------
LOW        : 1.0
MEDIUM     : 3.0
HIGH       : 4.0
CONGESTED  : 2.0
""")

print("""
RISK-AWARE THRESHOLDS
----------------------------------------
HIGH       : %.3f
MEDIUM     : %.3f
CONGESTED  : %.3f
""" % (
    best_high_threshold,
    best_medium_threshold,
    best_congested_threshold
))

print("""
FINAL METRICS
----------------------------------------
Validation Accuracy    : %.4f
Validation Macro F1    : %.4f
Validation Weighted F1 : %.4f

Test Accuracy          : %.4f
Test Macro F1          : %.4f
Test Weighted F1       : %.4f

HIGH Recall            : %.4f
CONGESTED Recall       : %.4f
HIGH + CONGESTED Recall: %.4f
""" % (

    validation_accuracy,

    validation_macro_f1,

    validation_weighted_f1,

    test_accuracy,

    test_macro_f1,

    test_weighted_f1,

    high_recall,

    congested_recall,

    risk_recall
))

print("""
OUTPUTS
----------------------------------------
Model:
trafficx_xgboost_v6.json

Features:
trafficx_xgboost_v6_features.json

Metrics:
trafficx_xgboost_v6_metrics.json

Thresholds:
trafficx_xgboost_v6_thresholds.json

Importance:
trafficx_xgboost_v6_feature_importance.csv

Confusion:
trafficx_xgboost_v6_confusion_matrix.csv

Report:
trafficx_xgboost_v6_classification_report.txt
""")

print("""
========================================
 TRAFFICX V6 TRAINING FINISHED
========================================
""")