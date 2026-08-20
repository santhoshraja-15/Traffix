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
# TRAFFICX - XGBOOST V3
# CLEAN TEMPORAL CONGESTION PREDICTION
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_v3_dataset.csv"
)

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3.json"
)

FEATURE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3_features.json"
)

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3_metrics.json"
)

IMPORTANCE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3_feature_importance.csv"
)

CONFUSION_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3_confusion_matrix.csv"
)

REPORT_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v3_classification_report.txt"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

PREDICTION_HORIZON_SECONDS = 300

NUM_CLASSES = 4

RANDOM_STATE = 42


# ============================================================
# HEADER
# ============================================================

print("""
========================================
 TRAFFICX - XGBOOST V3
 CLEAN TEMPORAL CONGESTION PREDICTION
========================================

Prediction:
Current traffic state
        +
Temporal traffic trends
        ↓
Future congestion

Prediction horizon:
5 minutes = 300 simulation steps

V3 improvements:
- Road quality filtering
- Active-road filtering
- Clean temporal features
- 5/15/30/60 second trends
- Rolling traffic averages
- Acceleration features
- Class-balanced training
========================================
""")


# ============================================================
# LOAD DATA
# ============================================================

print("""
========================================
 LOADING V3 DATASET
========================================
""")

print("Loading dataset...")

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Rows loaded: {len(df):,}"
)

print(
    f"Columns loaded: {len(df.columns)}"
)


# ============================================================
# TARGET ENCODING
# ============================================================

print("""
========================================
 TARGET ENCODING
========================================
""")

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
# CHECK TARGET
# ============================================================

if df["target"].isna().any():

    invalid_targets = (
        df.loc[
            df["target"].isna(),
            "future_congestion"
        ]
        .value_counts()
    )

    print(
        "\nWARNING: Invalid target labels found:"
    )

    print(
        invalid_targets
    )

    raise ValueError(
        "Dataset contains invalid future_congestion labels."
    )


df["target"] = (
    df["target"]
    .astype(int)
)


# ============================================================
# TEMPORAL SORT
# ============================================================

print("""
========================================
 SORTING DATA TEMPORALLY
========================================
""")

df = df.sort_values(
    [
        "scenario",
        "road_id",
        "step"
    ]
).reset_index(
    drop=True
)

print(
    "Temporal sorting complete."
)


# ============================================================
# TEMPORAL CONTINUITY CHECK
# ============================================================

print("""
========================================
 TEMPORAL CONTINUITY CHECK
========================================
""")

step_difference = (
    df.groupby(
        ["scenario", "road_id"]
    )["step"]
    .diff()
)

non_consecutive = (
    step_difference
    .dropna()
    .ne(1)
    .sum()
)

print(
    f"Non-consecutive transitions: "
    f"{non_consecutive:,}"
)

if non_consecutive == 0:

    print(
        "Temporal continuity: OK"
    )

else:

    print(
        "WARNING: Non-consecutive "
        "transitions detected."
    )


# ============================================================
# TEMPORAL SPLIT
# ============================================================
#
# IMPORTANT:
#
# Do NOT randomly split this dataset.
#
# We want the model to learn from earlier
# simulation time and predict later time.
#
# TRAIN:
#   steps 0-499
#
# VALIDATION:
#   steps 500-599
#
# TEST:
#   steps 600-699
#
# This prevents temporal leakage.
# ============================================================

print("""
========================================
 TEMPORAL TRAIN / VALIDATION / TEST SPLIT
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
    f"-> {len(train):,} rows"
)

print(
    f"VALIDATION : steps 500-599 "
    f"-> {len(validation):,} rows"
)

print(
    f"TEST       : steps 600-699 "
    f"-> {len(test):,} rows"
)


# ============================================================
# CHECK SPLIT
# ============================================================

if len(train) == 0:
    raise ValueError("Training dataset is empty.")

if len(validation) == 0:
    raise ValueError("Validation dataset is empty.")

if len(test) == 0:
    raise ValueError("Test dataset is empty.")


# ============================================================
# FEATURE COLUMNS
# ============================================================

print("""
========================================
 FEATURE SELECTION
========================================
""")

EXCLUDE_COLUMNS = [

    # Identification
    "scenario",
    "step",
    "road_id",

    # Future information
    "future_congestion",

    # Encoded target
    "target"
]


feature_columns = [

    column
    for column in df.columns

    if column not in EXCLUDE_COLUMNS
]


print(
    f"Number of features: "
    f"{len(feature_columns)}"
)

print()

for i, feature in enumerate(
    feature_columns,
    start=1
):

    print(
        f"{i:02d}. {feature}"
    )


# ============================================================
# EXPECTED V3 FEATURE COUNT
# ============================================================

if len(feature_columns) != 46:

    print(
        "\nWARNING:"
    )

    print(
        f"Expected 46 features, "
        f"but found {len(feature_columns)}."
    )

else:

    print(
        "\nFeature count verified: 46"
    )


# ============================================================
# CHECK FOR FUTURE LEAKAGE
# ============================================================

print("""
========================================
 FUTURE LEAKAGE CHECK
========================================
""")

future_columns = [
    column
    for column in feature_columns
    if column.startswith("future_")
]

if future_columns:

    print(
        "ERROR: Future information detected:"
    )

    for column in future_columns:
        print(
            f"  - {column}"
        )

    raise ValueError(
        "Future information must not be used "
        "as model input."
    )

else:

    print(
        "No future_* features detected."
    )

    print(
        "Leakage check: PASSED"
    )


# ============================================================
# PREPARE X / Y
# ============================================================

print("""
========================================
 PREPARING TRAINING DATA
========================================
""")

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
# CHECK NUMERIC FEATURES
# ============================================================

print("""
========================================
 FEATURE TYPE CHECK
========================================
""")

non_numeric = (
    X_train
    .select_dtypes(
        exclude=[np.number]
    )
    .columns
    .tolist()
)

if non_numeric:

    print(
        "ERROR: Non-numeric features:"
    )

    for column in non_numeric:
        print(
            f"  - {column}"
        )

    raise ValueError(
        "All XGBoost input features must be numeric."
    )

else:

    print(
        "All 46 features are numeric."
    )


# ============================================================
# CHECK NaN / INF
# ============================================================

print("""
========================================
 DATA QUALITY CHECK
========================================
""")

for name, X in [
    ("TRAIN", X_train),
    ("VALIDATION", X_validation),
    ("TEST", X_test)
]:

    nan_count = (
        X.isna()
        .sum()
        .sum()
    )

    inf_count = (
        np.isinf(
            X.to_numpy()
        )
        .sum()
    )

    print(
        f"{name}: "
        f"NaN={nan_count:,}, "
        f"INF={inf_count:,}"
    )

    if nan_count > 0:
        raise ValueError(
            f"{name} contains NaN values."
        )

    if inf_count > 0:
        raise ValueError(
            f"{name} contains infinite values."
        )


print(
    "\nData quality: PASSED"
)


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

print(
    "\nPercentage:"
)

train_percentage = (
    train_distribution
    / len(train)
    * 100
)

print(
    train_percentage.round(2)
)


# ============================================================
# VALIDATION DISTRIBUTION
# ============================================================

print("""
========================================
 VALIDATION CLASS DISTRIBUTION
========================================
""")

validation_distribution = (
    validation["future_congestion"]
    .value_counts()
)

print(
    validation_distribution
)

print(
    "\nPercentage:"
)

print(
    (
        validation_distribution
        / len(validation)
        * 100
    ).round(2)
)


# ============================================================
# TEST DISTRIBUTION
# ============================================================

print("""
========================================
 TEST CLASS DISTRIBUTION
========================================
""")

test_distribution = (
    test["future_congestion"]
    .value_counts()
)

print(
    test_distribution
)

print(
    "\nPercentage:"
)

print(
    (
        test_distribution
        / len(test)
        * 100
    ).round(2)
)


# ============================================================
# CLASS-BALANCED SAMPLE WEIGHTS
# ============================================================

print("""
========================================
 CALCULATING CLASS-BALANCED WEIGHTS
========================================
""")

sample_weights = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)

print(
    "Balanced sample weights calculated."
)

print(
    f"Minimum weight: "
    f"{sample_weights.min():.4f}"
)

print(
    f"Maximum weight: "
    f"{sample_weights.max():.4f}"
)


# ============================================================
# CREATE XGBOOST MODEL
# ============================================================

print("""
========================================
 CREATING XGBOOST V3 MODEL
========================================
""")

model = XGBClassifier(

    # --------------------------------------------------------
    # Multiclass classification
    # --------------------------------------------------------

    objective="multi:softprob",

    num_class=NUM_CLASSES,

    # --------------------------------------------------------
    # Boosting
    # --------------------------------------------------------

    n_estimators=500,

    learning_rate=0.05,

    # --------------------------------------------------------
    # Tree complexity
    # --------------------------------------------------------

    max_depth=8,

    min_child_weight=3,

    # --------------------------------------------------------
    # Sampling
    # --------------------------------------------------------

    subsample=0.85,

    colsample_bytree=0.85,

    # --------------------------------------------------------
    # Regularization
    # --------------------------------------------------------

    gamma=0.1,

    reg_alpha=0.05,

    reg_lambda=1.0,

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    eval_metric="mlogloss",

    # --------------------------------------------------------
    # Performance
    # --------------------------------------------------------

    tree_method="hist",

    n_jobs=-1,

    random_state=RANDOM_STATE
)


print(
    "XGBoost V3 model created."
)


# ============================================================
# TRAIN
# ============================================================

print("""
========================================
 TRAINING XGBOOST V3
========================================
""")

print(
    "Training may take some time..."
)

model.fit(

    X_train,

    y_train,

    sample_weight=sample_weights,

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
# VALIDATION PREDICTIONS
# ============================================================

print("""
========================================
 VALIDATION EVALUATION
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


# ============================================================
# TEST PREDICTIONS
# ============================================================

print("""
========================================
 FINAL TEST EVALUATION
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
 TEST CLASSIFICATION REPORT
========================================
""")

classification_report_text = (
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
        digits=4,
        zero_division=0
    )
)

print(
    classification_report_text
)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "TRAFFICX XGBoost V3\n"
    )

    f.write(
        "===================\n\n"
    )

    f.write(
        classification_report_text
    )

print(
    f"Classification report saved:\n"
    f"{REPORT_FILE}"
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
# SAVE CONFUSION MATRIX
# ============================================================

cm_df.to_csv(
    CONFUSION_FILE
)

print(
    f"\nConfusion matrix saved:\n"
    f"{CONFUSION_FILE}"
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

    "feature":
        feature_columns,

    "importance":
        model.feature_importances_

})

importance = (
    importance
    .sort_values(
        "importance",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE FEATURE IMPORTANCE
# ============================================================

importance.to_csv(
    IMPORTANCE_FILE,
    index=False
)

print(
    f"\nFeature importance saved:\n"
    f"{IMPORTANCE_FILE}"
)


# ============================================================
# TOP FEATURES
# ============================================================

print("""
========================================
 TOP 15 FEATURES
========================================
""")

print(
    importance
    .head(15)
    .to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

print("""
========================================
 SAVING XGBOOST V3 MODEL
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

print("""
========================================
 SAVING METRICS
========================================
""")

metrics = {

    "model":
        "TRAFFICX XGBoost V3",

    "version":
        "V3",

    "prediction_horizon_seconds":
        PREDICTION_HORIZON_SECONDS,

    "prediction_horizon_steps":
        300,

    "features":
        len(feature_columns),

    "train_rows":
        len(train),

    "validation_rows":
        len(validation),

    "test_rows":
        len(test),

    "train_step_range":
        "0-499",

    "validation_step_range":
        "500-599",

    "test_step_range":
        "600-699",

    "road_quality_filter":
        "road_length >= 5 meters",

    "active_road_filter":
        True,

    "temporal_features":
        [
            "5s changes",
            "15s changes",
            "30s changes",
            "60s changes",
            "15s rolling means",
            "30s rolling means",
            "60s rolling means",
            "acceleration/trend"
        ],

    "class_balanced_training":
        True,

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
        float(test_weighted_f1),

    "test_class_distribution":
        {
            str(k): int(v)
            for k, v in test_distribution.items()
        }
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


print(
    f"Metrics saved:\n"
    f"{METRICS_FILE}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("""
========================================
 TRAFFICX XGBOOST V3 COMPLETE
========================================

MODEL
----------------------------------------
trafficx_xgboost_v3.json

DATASET
----------------------------------------
trafficx_xgboost_v3_dataset.csv

FEATURES
----------------------------------------
46 temporal + traffic features

PREDICTION
----------------------------------------
5-minute future congestion

TEMPORAL SPLIT
----------------------------------------
Train      : steps 0-499
Validation : steps 500-599
Test       : steps 600-699

DATA CLEANING
----------------------------------------
Road length >= 5m
Active roads only
Temporal continuity verified
Future leakage checked

CLASS BALANCING
----------------------------------------
Balanced sample weights

EVALUATION
----------------------------------------
Accuracy
Macro F1
Weighted F1
Classification report
Confusion matrix

OUTPUTS
----------------------------------------
Model:
trafficx_xgboost_v3.json

Features:
trafficx_xgboost_v3_features.json

Metrics:
trafficx_xgboost_v3_metrics.json

Importance:
trafficx_xgboost_v3_feature_importance.csv

Confusion:
trafficx_xgboost_v3_confusion_matrix.csv

Report:
trafficx_xgboost_v3_classification_report.txt

========================================
 TRAFFICX V3 TRAINING FINISHED
========================================
""")


# ============================================================
# FINAL METRIC SUMMARY
# ============================================================

print("""
========================================
 FINAL METRICS
========================================
""")

print(
    f"Validation Accuracy    : "
    f"{validation_accuracy:.4f}"
)

print(
    f"Validation Macro F1    : "
    f"{validation_macro_f1:.4f}"
)

print(
    f"Validation Weighted F1 : "
    f"{validation_weighted_f1:.4f}"
)

print()

print(
    f"Test Accuracy          : "
    f"{test_accuracy:.4f}"
)

print(
    f"Test Macro F1          : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Test Weighted F1       : "
    f"{test_weighted_f1:.4f}"
)

print("""
========================================
 READY FOR V1 vs V2 vs V3 COMPARISON
========================================
""")