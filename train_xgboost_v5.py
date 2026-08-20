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
    confusion_matrix,
    precision_score,
    recall_score
)


# ============================================================
# TRAFFICX - XGBOOST V5
# RISK-AWARE TEMPORAL CONGESTION PREDICTION
# ============================================================

INPUT_FILE = (
    r"D:\TRAFFICX\road_datasets"
    r"\trafficx_xgboost_v3_dataset.csv"
)

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5.json"
)

FEATURE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5_features.json"
)

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5_metrics.json"
)

REPORT_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5_classification_report.txt"
)

CONFUSION_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5_confusion_matrix.csv"
)

IMPORTANCE_FILE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v5_feature_importance.csv"
)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


print("""
========================================
 TRAFFICX - XGBOOST V5
 RISK-AWARE TEMPORAL PREDICTION
========================================

Prediction:
Current traffic + temporal trends
                ↓
       Future congestion

Prediction horizon:
5 minutes = 300 seconds

Primary optimization metric:
Macro F1

Secondary risk metric:
HIGH + CONGESTED recall
========================================
""")


# ============================================================
# LOAD DATASET
# ============================================================

print("""
========================================
 LOADING DATASET
========================================
""")

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
# CHECK TARGET
# ============================================================

if df["target"].isna().any():

    invalid = df[
        df["target"].isna()
    ]["future_congestion"].unique()

    raise ValueError(
        f"Unknown target labels found: {invalid}"
    )


# ============================================================
# SORT
# ============================================================

print("""
========================================
 SORTING TEMPORAL DATA
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

distribution = (
    train["future_congestion"]
    .value_counts()
    .reindex(
        [
            "LOW",
            "MEDIUM",
            "HIGH",
            "CONGESTED"
        ],
        fill_value=0
    )
)

print(distribution)

print("\nPercentage:")

print(
    (
        distribution /
        len(train) *
        100
    ).round(2)
)


# ============================================================
# RISK-AWARE CLASS WEIGHTS
# ============================================================

print("""
========================================
 RISK-AWARE CLASS WEIGHTS
========================================
""")

# LOW is dominant.
#
# MEDIUM and HIGH receive stronger penalties.
#
# CONGESTED receives a moderate-high penalty.
#
# These weights are intentionally stronger than V4
# for the minority congestion classes.

CLASS_WEIGHTS = {
    0: 1.0,   # LOW
    1: 5.0,   # MEDIUM
    2: 7.0,   # HIGH
    3: 2.5    # CONGESTED
}

print(
    "LOW        :", CLASS_WEIGHTS[0]
)

print(
    "MEDIUM     :", CLASS_WEIGHTS[1]
)

print(
    "HIGH       :", CLASS_WEIGHTS[2]
)

print(
    "CONGESTED  :", CLASS_WEIGHTS[3]
)


# ============================================================
# SAMPLE WEIGHTS
# ============================================================

sample_weights = (
    y_train.map(
        CLASS_WEIGHTS
    ).astype(float)
)

print(
    "\nSample weights generated."
)


# ============================================================
# CREATE MODEL
# ============================================================

print("""
========================================
 CREATING XGBOOST V5 MODEL
========================================
""")

model = XGBClassifier(

    objective="multi:softprob",

    num_class=4,

    n_estimators=1000,

    learning_rate=0.035,

    max_depth=7,

    min_child_weight=4,

    subsample=0.85,

    colsample_bytree=0.85,

    gamma=0.15,

    reg_alpha=0.10,

    reg_lambda=1.5,

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
 TRAINING XGBOOST V5
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


validation_accuracy = accuracy_score(
    y_validation,
    validation_predictions
)

validation_macro_f1 = f1_score(
    y_validation,
    validation_predictions,
    average="macro"
)

validation_weighted_f1 = f1_score(
    y_validation,
    validation_predictions,
    average="weighted"
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

print(report)


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

print(cm_df)


cm_df.to_csv(
    CONFUSION_FILE
)

print(
    f"\nConfusion matrix saved:\n"
    f"{CONFUSION_FILE}"
)


# ============================================================
# RISK METRICS
# ============================================================

print("""
========================================
 RISK-AWARE METRICS
========================================
""")

# HIGH recall
high_recall = recall_score(
    y_test,
    test_predictions,
    labels=[2],
    average=None
)[0]


# CONGESTED recall
congested_recall = recall_score(
    y_test,
    test_predictions,
    labels=[3],
    average=None
)[0]


# HIGH + CONGESTED recall
#
# Actual classes:
# HIGH       = 2
# CONGESTED  = 3
#
# Correct predictions:
# predicted HIGH or CONGESTED

risk_mask = y_test.isin(
    [2, 3]
)

risk_predictions = pd.Series(
    test_predictions,
    index=y_test.index
)

risk_correct = (
    risk_predictions[
        risk_mask
    ].isin([2, 3])
)

high_congested_recall = (
    risk_correct.mean()
)


print(
    f"HIGH recall             : "
    f"{high_recall:.4f}"
)

print(
    f"CONGESTED recall       : "
    f"{congested_recall:.4f}"
)

print(
    f"HIGH + CONGESTED recall: "
    f"{high_congested_recall:.4f}"
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
 SAVING XGBOOST V5 MODEL
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
        "TRAFFICX XGBoost V5",

    "prediction_horizon_seconds":
        300,

    "features":
        len(feature_columns),

    "dataset":
        "trafficx_xgboost_v3_dataset.csv",

    "train_rows":
        len(train),

    "validation_rows":
        len(validation),

    "test_rows":
        len(test),

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

    "high_recall":
        float(high_recall),

    "congested_recall":
        float(congested_recall),

    "high_congested_recall":
        float(high_congested_recall),

    "class_weights":
        {
            "LOW": 1.0,
            "MEDIUM": 5.0,
            "HIGH": 7.0,
            "CONGESTED": 2.5
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
# COMPLETE
# ============================================================

print("""
========================================
 TRAFFICX XGBOOST V5 COMPLETE
========================================

MODEL
----------------------------------------
trafficx_xgboost_v5.json

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

CLASS WEIGHTS
----------------------------------------
LOW        : 1.0
MEDIUM     : 5.0
HIGH       : 7.0
CONGESTED  : 2.5

PRIMARY METRIC
----------------------------------------
Macro F1

RISK METRIC
----------------------------------------
HIGH + CONGESTED recall

OUTPUTS
----------------------------------------
Model:
trafficx_xgboost_v5.json

Features:
trafficx_xgboost_v5_features.json

Metrics:
trafficx_xgboost_v5_metrics.json

Importance:
trafficx_xgboost_v5_feature_importance.csv

Confusion:
trafficx_xgboost_v5_confusion_matrix.csv

Report:
trafficx_xgboost_v5_classification_report.txt

========================================
 FINAL METRICS
========================================

Validation Accuracy    :
Validation Macro F1    :
Validation Weighted F1 :

Test Accuracy          :
Test Macro F1          :
Test Weighted F1       :

HIGH Recall            :
CONGESTED Recall       :
HIGH + CONGESTED Recall:

========================================
 TRAFFICX V5 TRAINING FINISHED
========================================
""")