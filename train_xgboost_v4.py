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


# ============================================================
# TRAFFICX - XGBOOST V4
# CLASS-BALANCED TEMPORAL CONGESTION PREDICTION
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_v3_dataset.csv"
)

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4.json"
)

FEATURE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4_features.json"
)

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4_metrics.json"
)

IMPORTANCE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4_feature_importance.csv"
)

CONFUSION_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4_confusion_matrix.csv"
)

REPORT_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v4_classification_report.txt"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print("""
========================================
 TRAFFICX - XGBOOST V4
 CLASS-BALANCED TEMPORAL PREDICTION
========================================

Prediction:
Current traffic + temporal trends
                ↓
        Future congestion

Prediction horizon:
5 minutes = 300 simulation steps

Dataset:
Clean V3 dataset

Improvements:
- Custom minority-class weighting
- Tuned XGBoost parameters
- Temporal split preserved
- No future feature leakage
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

df = pd.read_csv(INPUT_FILE)

print(
    f"Rows loaded: {len(df):,}"
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

print(
    df["future_congestion"]
    .value_counts()
)


# ============================================================
# SORT TEMPORALLY
# ============================================================

print("""
========================================
 TEMPORAL SORT
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


# ============================================================
# TEMPORAL SPLIT
# ============================================================

print("""
========================================
 TEMPORAL SPLIT
========================================

Train:
steps 0-499

Validation:
steps 500-599

Test:
steps 600-699
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
    f"TRAIN      : {len(train):,} rows"
)

print(
    f"VALIDATION : {len(validation):,} rows"
)

print(
    f"TEST       : {len(test):,} rows"
)


# ============================================================
# FEATURES
# ============================================================

print("""
========================================
 FEATURE SELECTION
========================================
""")

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

class_counts = (
    y_train.value_counts()
    .sort_index()
)

print(
    class_counts
)

print("\nPercentages:")

print(
    (
        class_counts /
        len(y_train) *
        100
    ).round(2)
)


# ============================================================
# CUSTOM CLASS WEIGHTS
# ============================================================

print("""
========================================
 CUSTOM CLASS WEIGHTS
========================================
""")

# LOW        = 1.0
# MEDIUM     = 3.0
# HIGH       = 4.0
# CONGESTED  = 1.5

class_weights = {
    0: 1.0,
    1: 3.0,
    2: 4.0,
    3: 1.5
}

print(
    "LOW        : 1.0"
)

print(
    "MEDIUM     : 3.0"
)

print(
    "HIGH       : 4.0"
)

print(
    "CONGESTED  : 1.5"
)

sample_weights = (
    y_train.map(class_weights)
    .astype(float)
)


print(
    "\nCustom sample weights created."
)


# ============================================================
# CREATE MODEL
# ============================================================

print("""
========================================
 CREATING XGBOOST V4
========================================
""")

model = XGBClassifier(

    objective="multi:softprob",

    num_class=4,

    n_estimators=700,

    learning_rate=0.035,

    max_depth=7,

    min_child_weight=2,

    subsample=0.85,

    colsample_bytree=0.90,

    gamma=0.05,

    reg_alpha=0.10,

    reg_lambda=1.50,

    eval_metric="mlogloss",

    tree_method="hist",

    random_state=42,

    n_jobs=-1
)


print("""
Model parameters:

n_estimators      = 700
learning_rate     = 0.035
max_depth         = 7
min_child_weight  = 2
subsample         = 0.85
colsample_bytree  = 0.90
gamma             = 0.05
reg_alpha         = 0.10
reg_lambda        = 1.50
""")


# ============================================================
# TRAIN
# ============================================================

print("""
========================================
 TRAINING XGBOOST V4
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
# VALIDATION PREDICTION
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
# FINAL TEST
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

report = classification_report(
    y_test,
    test_predictions,
    labels=[
        0,
        1,
        2,
        3
    ],
    target_names=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CONGESTED"
    ],
    digits=4
)

print(
    report
)


with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(report)


print(
    f"\nClassification report saved:\n"
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
    labels=[
        0,
        1,
        2,
        3
    ]
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
)


print(
    importance.to_string(
        index=False
    )
)


importance.to_csv(
    IMPORTANCE_FILE,
    index=False
)

print(
    f"\nFeature importance saved:\n"
    f"{IMPORTANCE_FILE}"
)


# ============================================================
# TOP 15 FEATURES
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
 SAVING XGBOOST V4 MODEL
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
        "TRAFFICX XGBoost V4",

    "version":
        "V4",

    "prediction_horizon_seconds":
        300,

    "features":
        len(feature_columns),

    "train_rows":
        len(train),

    "validation_rows":
        len(validation),

    "test_rows":
        len(test),

    "class_weights": {
        "LOW": 1.0,
        "MEDIUM": 3.0,
        "HIGH": 4.0,
        "CONGESTED": 1.5
    },

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


print(
    f"Metrics saved:\n"
    f"{METRICS_FILE}"
)


# ============================================================
# COMPLETE
# ============================================================

print("""
========================================
 TRAFFICX XGBOOST V4 COMPLETE
========================================

MODEL
----------------------------------------
trafficx_xgboost_v4.json

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

CLASS BALANCING
----------------------------------------
LOW        : 1.0
MEDIUM     : 3.0
HIGH       : 4.0
CONGESTED  : 1.5

OUTPUTS
----------------------------------------
Model:
trafficx_xgboost_v4.json

Features:
trafficx_xgboost_v4_features.json

Metrics:
trafficx_xgboost_v4_metrics.json

Importance:
trafficx_xgboost_v4_feature_importance.csv

Confusion:
trafficx_xgboost_v4_confusion_matrix.csv

Report:
trafficx_xgboost_v4_classification_report.txt

========================================
 FINAL METRICS
========================================

Validation Accuracy    :
Validation Macro F1    :
Validation Weighted F1 :

Test Accuracy          :
Test Macro F1          :
Test Weighted F1       :

========================================
 V4 TRAINING FINISHED
========================================
""")