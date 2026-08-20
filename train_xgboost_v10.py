import os
import json
import itertools
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# TRAFFICX - XGBOOST V10
# CONTROLLED RISK-SENSITIVE MODEL OPTIMIZATION
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

V10_MODEL = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10.json"
)

V10_FEATURES = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_features.json"
)

V10_METRICS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_metrics.json"
)

V10_EXPERIMENTS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_experiments.csv"
)

V10_THRESHOLD_TABLE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_thresholds.csv"
)

V10_CONFUSION = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_confusion_matrix.csv"
)

V10_CLASSIFICATION = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_classification_report.csv"
)

V10_FEATURE_IMPORTANCE = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v10_feature_importance.csv"
)


# ============================================================
# EXACT 46 FEATURES FROM TRAFFICX V3/V8
# ============================================================

FEATURES = [
    "road_length_m",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",
    "current_congestion_encoded",
    "scenario_encoded",

    "speed_change",
    "vehicle_change",
    "stopped_change",
    "waiting_change",
    "density_change",
    "queue_change",

    "speed_change_5s",
    "speed_change_15s",
    "speed_change_30s",
    "speed_change_60s",

    "density_change_5s",
    "density_change_15s",
    "density_change_30s",
    "density_change_60s",

    "queue_change_5s",
    "queue_change_15s",
    "queue_change_30s",
    "queue_change_60s",

    "waiting_change_5s",
    "waiting_change_15s",
    "waiting_change_30s",
    "waiting_change_60s",

    "speed_mean_15s",
    "speed_mean_30s",
    "speed_mean_60s",

    "density_mean_15s",
    "density_mean_30s",
    "density_mean_60s",

    "queue_mean_15s",
    "queue_mean_30s",
    "queue_mean_60s",

    "waiting_mean_15s",
    "waiting_mean_30s",
    "waiting_mean_60s",

    "speed_acceleration",
    "density_acceleration",
    "queue_acceleration"
]

TARGET = "future_congestion"

RISK_CLASSES = {"HIGH", "CONGESTED"}


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_STEPS = (0, 499)
VAL_STEPS = (500, 599)
TEST_STEPS = (600, 699)

RISK_WEIGHT_VALUES = [
    3.0,
    4.0,
    5.0,
    6.0,
    6.761,
    8.0,
    10.0
]

DEPTH_VALUES = [4, 6, 8]
MIN_CHILD_VALUES = [1, 3]

LEARNING_RATE_VALUES = [0.05, 0.10]
SUBSAMPLE_VALUES = [0.8, 1.0]
COLSAMPLE_VALUES = [0.8, 1.0]

THRESHOLDS = np.arange(
    0.200,
    0.801,
    0.005
)

RANDOM_STATE = 42

# Keep the search controlled.
# Early stopping prevents unnecessary trees.
N_ESTIMATORS = 700
EARLY_STOPPING_ROUNDS = 50


# ============================================================
# METRIC HELPERS
# ============================================================

def f2_score_binary(y_true, y_pred):
    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    beta = 2.0

    denominator = (
        beta ** 2 * precision
        + recall
    )

    if denominator == 0:
        return 0.0

    return (
        (1 + beta ** 2)
        * precision
        * recall
        / denominator
    )


def evaluate_thresholds(
    y_true,
    probabilities
):

    rows = []

    best = None

    for threshold in THRESHOLDS:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_true,
            predictions,
            zero_division=0
        )

        recall = recall_score(
            y_true,
            predictions,
            zero_division=0
        )

        f1 = f1_score(
            y_true,
            predictions,
            zero_division=0
        )

        f2 = f2_score_binary(
            y_true,
            predictions
        )

        accuracy = accuracy_score(
            y_true,
            predictions
        )

        rows.append({
            "threshold": round(float(threshold), 3),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "f2": f2,
            "accuracy": accuracy
        })

        if (
            best is None
            or f2 > best["f2"]
        ):
            best = {
                "threshold": float(threshold),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "f2": f2,
                "accuracy": accuracy
            }

    return best, pd.DataFrame(rows)


# ============================================================
# MODEL BUILDER
# ============================================================

def build_model(
    scale_pos_weight,
    max_depth,
    min_child_weight,
    learning_rate,
    subsample,
    colsample_bytree
):

    return xgb.XGBClassifier(

        objective="binary:logistic",

        n_estimators=N_ESTIMATORS,

        max_depth=max_depth,

        min_child_weight=min_child_weight,

        learning_rate=learning_rate,

        subsample=subsample,

        colsample_bytree=colsample_bytree,

        scale_pos_weight=scale_pos_weight,

        reg_alpha=0.0,
        reg_lambda=1.0,

        gamma=0.0,

        random_state=RANDOM_STATE,

        tree_method="hist",

        eval_metric="logloss",

        n_jobs=-1,

        verbosity=0
    )


# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 60)
print(" TRAFFICX - XGBOOST V10")
print(" CONTROLLED RISK-SENSITIVE OPTIMIZATION")
print("=" * 60)

print()
print("Dataset:")
print(DATASET)

print()
print("Loading dataset...")

df = pd.read_csv(DATASET)

print("Rows loaded:", len(df))


# ============================================================
# DATA VALIDATION
# ============================================================

print()
print("=" * 60)
print(" DATA VALIDATION")
print("=" * 60)

required_columns = FEATURES + [
    TARGET,
    "step"
]

missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    print()
    print("ERROR: Missing columns:")
    for c in missing:
        print("  -", c)

    raise ValueError(
        "Required columns are missing."
    )

print()
print("Required columns: OK")
print("Feature count:", len(FEATURES))

if len(FEATURES) != 46:
    raise ValueError(
        f"Expected 46 features, found {len(FEATURES)}"
    )


# ============================================================
# SORT TEMPORALLY
# ============================================================

df = df.sort_values(
    by=["step"]
).reset_index(drop=True)


# ============================================================
# RISK TARGET
# ============================================================

df["risk_target"] = (
    df[TARGET]
    .astype(str)
    .str.upper()
    .isin(RISK_CLASSES)
    .astype(int)
)


# ============================================================
# SPLIT
# ============================================================

train_df = df[
    (df["step"] >= TRAIN_STEPS[0])
    & (df["step"] <= TRAIN_STEPS[1])
].copy()

val_df = df[
    (df["step"] >= VAL_STEPS[0])
    & (df["step"] <= VAL_STEPS[1])
].copy()

test_df = df[
    (df["step"] >= TEST_STEPS[0])
    & (df["step"] <= TEST_STEPS[1])
].copy()


print()
print("=" * 60)
print(" TEMPORAL SPLIT")
print("=" * 60)

print(
    f"TRAIN      : steps {TRAIN_STEPS[0]}-{TRAIN_STEPS[1]}"
)
print(
    f"VALIDATION : steps {VAL_STEPS[0]}-{VAL_STEPS[1]}"
)
print(
    f"TEST       : steps {TEST_STEPS[0]}-{TEST_STEPS[1]}"
)

print()
print("TRAIN rows      :", len(train_df))
print("VALIDATION rows :", len(val_df))
print("TEST rows       :", len(test_df))


# ============================================================
# RISK DISTRIBUTION
# ============================================================

def risk_rate(frame):

    return frame["risk_target"].mean()


print()
print("=" * 60)
print(" RISK DISTRIBUTION")
print("=" * 60)

print(
    f"TRAIN      risk : {risk_rate(train_df):.4%}"
)

print(
    f"VALIDATION risk : {risk_rate(val_df):.4%}"
)

print(
    f"TEST       risk : {risk_rate(test_df):.4%}"
)


# ============================================================
# DATA MATRICES
# ============================================================

X_train = train_df[FEATURES]
y_train = train_df["risk_target"]

X_val = val_df[FEATURES]
y_val = val_df["risk_target"]

X_test = test_df[FEATURES]
y_test = test_df["risk_target"]


# ============================================================
# STAGE 1
# CLASS WEIGHT SEARCH
# ============================================================

print()
print("=" * 60)
print(" STAGE 1 - CLASS WEIGHT SEARCH")
print("=" * 60)

stage1_results = []

for weight in RISK_WEIGHT_VALUES:

    print()
    print(
        f"Testing scale_pos_weight = {weight}"
    )

    model = build_model(
        scale_pos_weight=weight,
        max_depth=6,
        min_child_weight=1,
        learning_rate=0.10,
        subsample=0.8,
        colsample_bytree=0.8
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[
            (X_val, y_val)
        ],
        verbose=False
    )

    val_prob = model.predict_proba(
        X_val
    )[:, 1]

    best, _ = evaluate_thresholds(
        y_val,
        val_prob
    )

    result = {
        "stage": "class_weight",
        "scale_pos_weight": weight,
        "max_depth": 6,
        "min_child_weight": 1,
        "learning_rate": 0.10,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "validation_threshold": best["threshold"],
        "validation_precision": best["precision"],
        "validation_recall": best["recall"],
        "validation_f1": best["f1"],
        "validation_f2": best["f2"],
        "validation_accuracy": best["accuracy"]
    }

    stage1_results.append(result)

    print(
        f"  Threshold : {best['threshold']:.3f}"
    )
    print(
        f"  Precision : {best['precision']:.4f}"
    )
    print(
        f"  Recall    : {best['recall']:.4f}"
    )
    print(
        f"  F1        : {best['f1']:.4f}"
    )
    print(
        f"  F2        : {best['f2']:.4f}"
    )


stage1_df = pd.DataFrame(stage1_results)

stage1_df = stage1_df.sort_values(
    by="validation_f2",
    ascending=False
)

best_weight = float(
    stage1_df.iloc[0]["scale_pos_weight"]
)

print()
print("BEST CLASS WEIGHT:")
print(best_weight)


# ============================================================
# STAGE 2
# MODEL COMPLEXITY SEARCH
# ============================================================

print()
print("=" * 60)
print(" STAGE 2 - MODEL COMPLEXITY SEARCH")
print("=" * 60)

stage2_results = []

for depth in DEPTH_VALUES:

    for min_child in MIN_CHILD_VALUES:

        print()
        print(
            f"Testing depth={depth}, "
            f"min_child_weight={min_child}"
        )

        model = build_model(
            scale_pos_weight=best_weight,
            max_depth=depth,
            min_child_weight=min_child,
            learning_rate=0.10,
            subsample=0.8,
            colsample_bytree=0.8
        )

        model.fit(
            X_train,
            y_train,
            eval_set=[
                (X_val, y_val)
            ],
            verbose=False
        )

        val_prob = model.predict_proba(
            X_val
        )[:, 1]

        best, _ = evaluate_thresholds(
            y_val,
            val_prob
        )

        result = {
            "stage": "complexity",
            "scale_pos_weight": best_weight,
            "max_depth": depth,
            "min_child_weight": min_child,
            "learning_rate": 0.10,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "validation_threshold": best["threshold"],
            "validation_precision": best["precision"],
            "validation_recall": best["recall"],
            "validation_f1": best["f1"],
            "validation_f2": best["f2"],
            "validation_accuracy": best["accuracy"]
        }

        stage2_results.append(result)

        print(
            f"  F2 = {best['f2']:.4f}"
        )


stage2_df = pd.DataFrame(stage2_results)

stage2_df = stage2_df.sort_values(
    by="validation_f2",
    ascending=False
)

best_depth = int(
    stage2_df.iloc[0]["max_depth"]
)

best_min_child = int(
    stage2_df.iloc[0]["min_child_weight"]
)

print()
print("BEST COMPLEXITY:")
print(
    "max_depth =", best_depth
)
print(
    "min_child_weight =", best_min_child
)


# ============================================================
# STAGE 3
# GENERALIZATION SEARCH
# ============================================================

print()
print("=" * 60)
print(" STAGE 3 - GENERALIZATION SEARCH")
print("=" * 60)

stage3_results = []

generalization_configs = list(
    itertools.product(
        LEARNING_RATE_VALUES,
        SUBSAMPLE_VALUES,
        COLSAMPLE_VALUES
    )
)

for (
    learning_rate,
    subsample,
    colsample
) in generalization_configs:

    print()
    print(
        "Testing:",
        f"lr={learning_rate}",
        f"subsample={subsample}",
        f"colsample={colsample}"
    )

    model = build_model(
        scale_pos_weight=best_weight,
        max_depth=best_depth,
        min_child_weight=best_min_child,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[
            (X_val, y_val)
        ],
        verbose=False
    )

    val_prob = model.predict_proba(
        X_val
    )[:, 1]

    best, _ = evaluate_thresholds(
        y_val,
        val_prob
    )

    result = {
        "stage": "generalization",
        "scale_pos_weight": best_weight,
        "max_depth": best_depth,
        "min_child_weight": best_min_child,
        "learning_rate": learning_rate,
        "subsample": subsample,
        "colsample_bytree": colsample,
        "validation_threshold": best["threshold"],
        "validation_precision": best["precision"],
        "validation_recall": best["recall"],
        "validation_f1": best["f1"],
        "validation_f2": best["f2"],
        "validation_accuracy": best["accuracy"]
    }

    stage3_results.append(result)

    print(
        f"  Threshold = {best['threshold']:.3f}"
    )
    print(
        f"  F2 = {best['f2']:.4f}"
    )


stage3_df = pd.DataFrame(stage3_results)

stage3_df = stage3_df.sort_values(
    by="validation_f2",
    ascending=False
)


# ============================================================
# COMBINE ALL EXPERIMENTS
# ============================================================

experiments = pd.concat(
    [
        stage1_df,
        stage2_df,
        stage3_df
    ],
    ignore_index=True
)

experiments = experiments.sort_values(
    by="validation_f2",
    ascending=False
).reset_index(drop=True)

experiments.insert(
    0,
    "experiment_rank",
    np.arange(1, len(experiments) + 1)
)

experiments.to_csv(
    V10_EXPERIMENTS,
    index=False
)


# ============================================================
# FINAL WINNER
# ============================================================

winner = stage3_df.iloc[0]

BEST_WEIGHT = float(
    winner["scale_pos_weight"]
)

BEST_DEPTH = int(
    winner["max_depth"]
)

BEST_MIN_CHILD = int(
    winner["min_child_weight"]
)

BEST_LR = float(
    winner["learning_rate"]
)

BEST_SUBSAMPLE = float(
    winner["subsample"]
)

BEST_COLSAMPLE = float(
    winner["colsample_bytree"]
)

BEST_THRESHOLD = float(
    winner["validation_threshold"]
)


print()
print("=" * 60)
print(" V10 WINNING CONFIGURATION")
print("=" * 60)

print(
    "scale_pos_weight  :",
    BEST_WEIGHT
)

print(
    "max_depth         :",
    BEST_DEPTH
)

print(
    "min_child_weight  :",
    BEST_MIN_CHILD
)

print(
    "learning_rate     :",
    BEST_LR
)

print(
    "subsample         :",
    BEST_SUBSAMPLE
)

print(
    "colsample_bytree  :",
    BEST_COLSAMPLE
)

print(
    "threshold         :",
    BEST_THRESHOLD
)

print()
print(
    "Validation F2     :",
    f"{winner['validation_f2']:.4f}"
)


# ============================================================
# TRAIN FINAL FROZEN MODEL
#
# IMPORTANT:
# TEST DATA IS NOT USED HERE.
# ============================================================

print()
print("=" * 60)
print(" TRAINING FINAL FROZEN V10 MODEL")
print("=" * 60)

final_model = build_model(
    scale_pos_weight=BEST_WEIGHT,
    max_depth=BEST_DEPTH,
    min_child_weight=BEST_MIN_CHILD,
    learning_rate=BEST_LR,
    subsample=BEST_SUBSAMPLE,
    colsample_bytree=BEST_COLSAMPLE
)

final_model.fit(
    X_train,
    y_train,
    eval_set=[
        (X_val, y_val)
    ],
    verbose=False
)


# ============================================================
# FINAL VALIDATION THRESHOLD TABLE
# ============================================================

val_prob_final = final_model.predict_proba(
    X_val
)[:, 1]

best_val, threshold_table = evaluate_thresholds(
    y_val,
    val_prob_final
)

threshold_table.to_csv(
    V10_THRESHOLD_TABLE,
    index=False
)


# ============================================================
# UNTOUCHED TEST EVALUATION
# ============================================================

print()
print("=" * 60)
print(" FINAL TEST EVALUATION")
print("=" * 60)

print()
print("TEST HAS NOT BEEN USED FOR MODEL SELECTION.")


test_prob = final_model.predict_proba(
    X_test
)[:, 1]

test_pred = (
    test_prob >= BEST_THRESHOLD
).astype(int)


# ============================================================
# TEST METRICS
# ============================================================

test_accuracy = accuracy_score(
    y_test,
    test_pred
)

test_precision = precision_score(
    y_test,
    test_pred,
    zero_division=0
)

test_recall = recall_score(
    y_test,
    test_pred,
    zero_division=0
)

test_f1 = f1_score(
    y_test,
    test_pred,
    zero_division=0
)

test_f2 = f2_score_binary(
    y_test,
    test_pred
)


print()
print("Threshold :", f"{BEST_THRESHOLD:.3f}")

print(
    "Accuracy  :",
    f"{test_accuracy:.4f}"
)

print(
    "Precision :",
    f"{test_precision:.4f}"
)

print(
    "Recall    :",
    f"{test_recall:.4f}"
)

print(
    "F1        :",
    f"{test_f1:.4f}"
)

print(
    "F2        :",
    f"{test_f2:.4f}"
)


# ============================================================
# TEST CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    test_pred
)

cm_df = pd.DataFrame(
    cm,
    index=[
        "ACTUAL_NON_RISK",
        "ACTUAL_RISK"
    ],
    columns=[
        "PRED_NON_RISK",
        "PRED_RISK"
    ]
)

cm_df.to_csv(
    V10_CONFUSION
)


print()
print("Confusion Matrix:")
print(cm_df)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    y_test,
    test_pred,
    target_names=[
        "NON_RISK",
        "RISK"
    ],
    output_dict=True,
    zero_division=0
)

report_df = pd.DataFrame(
    report
).transpose()

report_df.to_csv(
    V10_CLASSIFICATION
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance_df = pd.DataFrame({
    "feature": FEATURES,
    "importance": final_model.feature_importances_
})

importance_df = importance_df.sort_values(
    by="importance",
    ascending=False
)

importance_df.to_csv(
    V10_FEATURE_IMPORTANCE,
    index=False
)


# ============================================================
# SAVE MODEL
# ============================================================

final_model.save_model(
    V10_MODEL
)


# ============================================================
# SAVE FEATURES
# ============================================================

with open(
    V10_FEATURES,
    "w"
) as f:

    json.dump(
        FEATURES,
        f,
        indent=4
    )


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {

    "version": "V10",

    "model_type": (
        "Independent binary XGBoost "
        "risk classifier"
    ),

    "dataset": DATASET,

    "target_source": TARGET,

    "risk_definition": {
        "NON_RISK": [
            "LOW",
            "MEDIUM"
        ],
        "RISK": [
            "HIGH",
            "CONGESTED"
        ]
    },

    "feature_count": len(FEATURES),

    "features": FEATURES,

    "temporal_split": {
        "train": "0-499",
        "validation": "500-599",
        "test": "600-699"
    },

    "risk_distribution": {
        "train": float(
            risk_rate(train_df)
        ),
        "validation": float(
            risk_rate(val_df)
        ),
        "test": float(
            risk_rate(test_df)
        )
    },

    "best_parameters": {

        "scale_pos_weight":
            BEST_WEIGHT,

        "max_depth":
            BEST_DEPTH,

        "min_child_weight":
            BEST_MIN_CHILD,

        "learning_rate":
            BEST_LR,

        "subsample":
            BEST_SUBSAMPLE,

        "colsample_bytree":
            BEST_COLSAMPLE
    },

    "validation": {

        "threshold":
            BEST_THRESHOLD,

        "precision":
            float(
                best_val["precision"]
            ),

        "recall":
            float(
                best_val["recall"]
            ),

        "f1":
            float(
                best_val["f1"]
            ),

        "f2":
            float(
                best_val["f2"]
            ),

        "accuracy":
            float(
                best_val["accuracy"]
            )
    },

    "test": {

        "threshold":
            BEST_THRESHOLD,

        "accuracy":
            float(
                test_accuracy
            ),

        "precision":
            float(
                test_precision
            ),

        "recall":
            float(
                test_recall
            ),

        "f1":
            float(
                test_f1
            ),

        "f2":
            float(
                test_f2
            )
    }
}


with open(
    V10_METRICS,
    "w"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )


# ============================================================
# TOP FEATURES
# ============================================================

print()
print("=" * 60)
print(" TOP 15 V10 FEATURES")
print("=" * 60)

print(
    importance_df.head(15).to_string(
        index=False
    )
)


# ============================================================
# OUTPUT SUMMARY
# ============================================================

print()
print("=" * 60)
print(" OUTPUT FILES")
print("=" * 60)

print()
print("Model:")
print(V10_MODEL)

print()
print("Features:")
print(V10_FEATURES)

print()
print("Metrics:")
print(V10_METRICS)

print()
print("Experiment table:")
print(V10_EXPERIMENTS)

print()
print("Threshold table:")
print(V10_THRESHOLD_TABLE)

print()
print("Confusion matrix:")
print(V10_CONFUSION)

print()
print("Classification report:")
print(V10_CLASSIFICATION)

print()
print("Feature importance:")
print(V10_FEATURE_IMPORTANCE)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 60)
print(" TRAFFICX XGBOOST V10 COMPLETE")
print("=" * 60)

print()
print("FINAL V10 TEST RESULTS")
print("----------------------")

print(
    f"Accuracy  : {test_accuracy:.4f}"
)

print(
    f"Precision : {test_precision:.4f}"
)

print(
    f"Recall    : {test_recall:.4f}"
)

print(
    f"F1        : {test_f1:.4f}"
)

print(
    f"F2        : {test_f2:.4f}"
)

print()
print("V10 model is frozen.")
print("Test data was not used for model selection.")