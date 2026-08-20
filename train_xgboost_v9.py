import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report
)

# ============================================================
# TRAFFICX - XGBOOST V9
# RISK-AWARE FEATURE ENGINEERING + BINARY XGBOOST
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

V9_MODEL = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9.json"
)

V9_FEATURES = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9_features.json"
)

V9_THRESHOLDS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9_thresholds.json"
)

V9_METRICS = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9_metrics.json"
)

V9_CONFUSION = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9_confusion_matrix.csv"
)

V9_REPORT = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v9_classification_report.txt"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_MAX_STEP = 499
VAL_MIN_STEP = 500
VAL_MAX_STEP = 599
TEST_MIN_STEP = 600
TEST_MAX_STEP = 699

CLASS_TO_ID = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CONGESTED": 3
}

RISK_CLASSES = {
    "HIGH",
    "CONGESTED"
}

BASE_FEATURES = [
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

# Remove accidental duplicate while preserving order.
BASE_FEATURES = list(dict.fromkeys(BASE_FEATURES))


# ============================================================
# HEADER
# ============================================================

print("\n========================================")
print(" TRAFFICX - XGBOOST V9")
print(" RISK-AWARE FEATURE ENGINEERING")
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

df = pd.read_csv(DATASET)

print(f"Rows loaded: {len(df):,}")
print(f"Columns    : {len(df.columns)}")


# ============================================================
# TARGET VALIDATION
# ============================================================

print("\n========================================")
print(" TARGET VALIDATION")
print("========================================")

if "future_congestion" not in df.columns:
    raise ValueError(
        "future_congestion column not found."
    )

print("Original target distribution:")
print(
    df["future_congestion"]
    .value_counts()
)


unknown_classes = set(
    df["future_congestion"].dropna().unique()
) - set(CLASS_TO_ID.keys())

if unknown_classes:
    raise ValueError(
        f"Unknown target classes: {unknown_classes}"
    )


# ============================================================
# BINARY TARGET
# ============================================================

df["risk_target"] = (
    df["future_congestion"]
    .isin(RISK_CLASSES)
    .astype(int)
)

print("\nBinary target distribution:")

print(
    df["risk_target"]
    .map({
        0: "NON_RISK",
        1: "RISK"
    })
    .value_counts()
)


# ============================================================
# BASE FEATURE VALIDATION
# ============================================================

print("\n========================================")
print(" BASE FEATURE VALIDATION")
print("========================================")

missing_features = [
    feature
    for feature in BASE_FEATURES
    if feature not in df.columns
]

if missing_features:

    print("\nMissing features:")

    for feature in missing_features:
        print(feature)

    raise ValueError(
        "Dataset does not contain all required base features."
    )

print(
    f"Base features available: "
    f"{len(BASE_FEATURES)}"
)


# ============================================================
# RISK-AWARE FEATURE ENGINEERING
# ============================================================

print("\n========================================")
print(" RISK-AWARE FEATURE ENGINEERING")
print("========================================")

EPS = 1e-6

# ------------------------------------------------------------
# 1. STOPPED VEHICLE RATIO
# ------------------------------------------------------------

df["stopped_vehicle_ratio"] = (
    df["stopped_vehicles"]
    /
    (df["vehicle_count"] + EPS)
)

# ------------------------------------------------------------
# 2. SPEED DEGRADATION
# ------------------------------------------------------------

df["speed_degradation_15s"] = (
    1.0
    -
    (
        df["average_speed_kmh"]
        /
        (df["speed_mean_15s"] + EPS)
    )
)

df["speed_degradation_30s"] = (
    1.0
    -
    (
        df["average_speed_kmh"]
        /
        (df["speed_mean_30s"] + EPS)
    )
)

df["speed_degradation_60s"] = (
    1.0
    -
    (
        df["average_speed_kmh"]
        /
        (df["speed_mean_60s"] + EPS)
    )
)

# ------------------------------------------------------------
# 3. DENSITY GROWTH RATIOS
# ------------------------------------------------------------

df["density_growth_15s"] = (
    df["density_change_15s"]
    /
    (df["density_mean_15s"] + EPS)
)

df["density_growth_30s"] = (
    df["density_change_30s"]
    /
    (df["density_mean_30s"] + EPS)
)

df["density_growth_60s"] = (
    df["density_change_60s"]
    /
    (df["density_mean_60s"] + EPS)
)

# ------------------------------------------------------------
# 4. QUEUE GROWTH RATIOS
# ------------------------------------------------------------

df["queue_growth_15s"] = (
    df["queue_change_15s"]
    /
    (df["queue_mean_15s"] + EPS)
)

df["queue_growth_30s"] = (
    df["queue_change_30s"]
    /
    (df["queue_mean_30s"] + EPS)
)

df["queue_growth_60s"] = (
    df["queue_change_60s"]
    /
    (df["queue_mean_60s"] + EPS)
)

# ------------------------------------------------------------
# 5. WAITING-TIME GROWTH RATIOS
# ------------------------------------------------------------

df["waiting_growth_15s"] = (
    df["waiting_change_15s"]
    /
    (df["waiting_mean_15s"] + EPS)
)

df["waiting_growth_30s"] = (
    df["waiting_change_30s"]
    /
    (df["waiting_mean_30s"] + EPS)
)

df["waiting_growth_60s"] = (
    df["waiting_change_60s"]
    /
    (df["waiting_mean_60s"] + EPS)
)

# ------------------------------------------------------------
# 6. SPEED-DENSITY INTERACTION
# ------------------------------------------------------------

df["speed_density_interaction"] = (
    df["average_speed_kmh"]
    *
    df["density_veh_per_km"]
)

# ------------------------------------------------------------
# 7. DENSITY-QUEUE INTERACTION
# ------------------------------------------------------------

df["density_queue_interaction"] = (
    df["density_veh_per_km"]
    *
    df["queue_length_estimate_m"]
)

# ------------------------------------------------------------
# 8. QUEUE-WAITING INTERACTION
# ------------------------------------------------------------

df["queue_waiting_interaction"] = (
    df["queue_length_estimate_m"]
    *
    df["average_waiting_time"]
)

# ------------------------------------------------------------
# 9. VEHICLE DENSITY NORMALIZATION
# ------------------------------------------------------------

df["vehicles_per_road_meter"] = (
    df["vehicle_count"]
    /
    (df["road_length_m"] + EPS)
)

# ------------------------------------------------------------
# 10. QUEUE PER VEHICLE
# ------------------------------------------------------------

df["queue_per_vehicle"] = (
    df["queue_length_estimate_m"]
    /
    (df["vehicle_count"] + EPS)
)

# ------------------------------------------------------------
# 11. WAITING PER VEHICLE
# ------------------------------------------------------------

df["waiting_per_vehicle"] = (
    df["average_waiting_time"]
    /
    (df["vehicle_count"] + EPS)
)

# ------------------------------------------------------------
# 12. CONGESTION MOMENTUM
# ------------------------------------------------------------

df["congestion_momentum"] = (
    (-df["speed_change_60s"])
    +
    df["density_change_60s"]
    +
    df["queue_change_60s"]
    +
    df["waiting_change_60s"]
)

# ------------------------------------------------------------
# 13. RISK PRESSURE
# ------------------------------------------------------------

df["risk_pressure"] = (
    df["stopped_vehicle_ratio"]
    +
    df["density_growth_60s"]
    +
    df["queue_growth_60s"]
    +
    df["waiting_growth_60s"]
    +
    df["speed_degradation_60s"]
)

# ------------------------------------------------------------
# 14. TEMPORAL ACCELERATION COMBINATIONS
# ------------------------------------------------------------

df["risk_acceleration"] = (
    df["density_acceleration"]
    +
    df["queue_acceleration"]
    -
    df["speed_acceleration"]
)

# ------------------------------------------------------------
# 15. QUEUE VELOCITY
# ------------------------------------------------------------

df["queue_velocity"] = (
    df["queue_change_60s"]
    /
    60.0
)

# ------------------------------------------------------------
# 16. DENSITY VELOCITY
# ------------------------------------------------------------

df["density_velocity"] = (
    df["density_change_60s"]
    /
    60.0
)

# ------------------------------------------------------------
# 17. WAITING VELOCITY
# ------------------------------------------------------------

df["waiting_velocity"] = (
    df["waiting_change_60s"]
    /
    60.0
)


ENGINEERED_FEATURES = [
    "stopped_vehicle_ratio",

    "speed_degradation_15s",
    "speed_degradation_30s",
    "speed_degradation_60s",

    "density_growth_15s",
    "density_growth_30s",
    "density_growth_60s",

    "queue_growth_15s",
    "queue_growth_30s",
    "queue_growth_60s",

    "waiting_growth_15s",
    "waiting_growth_30s",
    "waiting_growth_60s",

    "speed_density_interaction",
    "density_queue_interaction",
    "queue_waiting_interaction",

    "vehicles_per_road_meter",
    "queue_per_vehicle",
    "waiting_per_vehicle",

    "congestion_momentum",
    "risk_pressure",
    "risk_acceleration",

    "queue_velocity",
    "density_velocity",
    "waiting_velocity"
]

FEATURES = BASE_FEATURES + ENGINEERED_FEATURES

FEATURES = list(
    dict.fromkeys(FEATURES)
)

print(
    f"Base features      : {len(BASE_FEATURES)}"
)

print(
    f"Engineered features: {len(ENGINEERED_FEATURES)}"
)

print(
    f"Total V9 features  : {len(FEATURES)}"
)

print("\nEngineered features:")

for i, feature in enumerate(
    ENGINEERED_FEATURES,
    1
):

    print(
        f"{i:02d}. {feature}"
    )


# ============================================================
# FEATURE CLEANING
# ============================================================

print("\n========================================")
print(" FEATURE CLEANING")
print("========================================")

X_all = df[FEATURES].copy()

X_all = X_all.replace(
    [np.inf, -np.inf],
    np.nan
)

nan_rows = X_all.isna().any(axis=1).sum()

print(
    f"Rows containing NaN/Inf: "
    f"{nan_rows:,}"
)

if nan_rows > 0:

    valid_mask = (
        ~X_all.isna().any(axis=1)
    )

    df = df.loc[
        valid_mask
    ].copy()

    X_all = X_all.loc[
        valid_mask
    ].copy()


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
# SPLIT CLASS DISTRIBUTION
# ============================================================

print("\n========================================")
print(" SPLIT CLASS DISTRIBUTION")
print("========================================")

for name, y in [
    ("TRAIN", y_train),
    ("VALIDATION", y_val),
    ("TEST", y_test)
]:

    print(f"\n{name}:")

    print(
        y.map({
            0: "NON_RISK",
            1: "RISK"
        })
        .value_counts()
    )


# ============================================================
# CLASS BALANCE
# ============================================================

negative_count = int(
    (y_train == 0).sum()
)

positive_count = int(
    (y_train == 1).sum()
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
# V9 MODEL
# ============================================================

print("\n========================================")
print(" TRAINING V9")
print("========================================")

model = xgb.XGBClassifier(

    objective="binary:logistic",

    n_estimators=1500,

    learning_rate=0.035,

    max_depth=7,

    min_child_weight=5,

    subsample=0.85,

    colsample_bytree=0.85,

    gamma=0.05,

    reg_alpha=0.05,

    reg_lambda=1.5,

    scale_pos_weight=scale_pos_weight,

    eval_metric="logloss",

    tree_method="hist",

    random_state=42,

    n_jobs=-1
)


model.fit(
    X_train,
    y_train,

    eval_set=[
        (X_val, y_val)
    ],

    verbose=100
)


print("\nV9 training completed.")

print(
    f"Best iteration: "
    f"{getattr(model, 'best_iteration', 'N/A')}"
)


# ============================================================
# VALIDATION PROBABILITY
# ============================================================

print("\n========================================")
print(" VALIDATION RISK PROBABILITY")
print("========================================")

val_probability = model.predict_proba(
    X_val
)[:, 1]

print(
    pd.Series(
        val_probability
    ).describe()
)


# ============================================================
# F2 FUNCTION
# ============================================================

def calculate_f2(
    precision,
    recall,
    beta=2.0
):

    denominator = (
        beta ** 2 * precision
    ) + recall

    if denominator == 0:
        return 0.0

    return (
        (1 + beta ** 2)
        * precision
        * recall
    ) / denominator


# ============================================================
# BASELINE VALIDATION
# ============================================================

print("\n========================================")
print(" BASELINE VALIDATION RESULT")
print("========================================")

baseline_threshold = 0.50

val_baseline_pred = (
    val_probability
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

baseline_f2 = calculate_f2(
    baseline_precision,
    baseline_recall
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

print("\n========================================")
print(" OPTIMIZING V9 RISK THRESHOLD")
print("========================================")

thresholds = np.arange(
    0.10,
    0.801,
    0.005
)

best_threshold = None
best_f2 = -1.0
best_threshold_metrics = {}


for threshold in thresholds:

    pred = (
        val_probability
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

    f2 = calculate_f2(
        precision,
        recall
    )

    if f2 > best_f2:

        best_f2 = f2

        best_threshold = float(
            threshold
        )

        best_threshold_metrics = {
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
print(" BEST V9 RISK THRESHOLD")
print("========================================")

print(
    f"Configurations tested: "
    f"{len(thresholds):,}"
)

print(
    f"\nRisk threshold : "
    f"{best_threshold:.3f}"
)

print("\nValidation metrics:")

print(
    f"Precision : "
    f"{best_threshold_metrics['precision']:.4f}"
)

print(
    f"Recall    : "
    f"{best_threshold_metrics['recall']:.4f}"
)

print(
    f"F1        : "
    f"{best_threshold_metrics['f1']:.4f}"
)

print(
    f"F2        : "
    f"{best_threshold_metrics['f2']:.4f}"
)


# ============================================================
# FREEZE THRESHOLD
# ============================================================

risk_threshold = best_threshold


# ============================================================
# FINAL VALIDATION PREDICTION
# ============================================================

val_pred = (
    val_probability
    >= risk_threshold
).astype(int)


# ============================================================
# TEST PROBABILITY
# ============================================================

print("\n========================================")
print(" TEST RISK PROBABILITY")
print("========================================")

test_probability = model.predict_proba(
    X_test
)[:, 1]

print(
    pd.Series(
        test_probability
    ).describe()
)


# ============================================================
# FINAL TEST PREDICTION
# ============================================================

test_pred = (
    test_probability
    >= risk_threshold
).astype(int)


# ============================================================
# VALIDATION METRICS
# ============================================================

val_precision = precision_score(
    y_val,
    val_pred,
    zero_division=0
)

val_recall = recall_score(
    y_val,
    val_pred,
    zero_division=0
)

val_f1 = f1_score(
    y_val,
    val_pred,
    zero_division=0
)

val_f2 = calculate_f2(
    val_precision,
    val_recall
)


# ============================================================
# TEST METRICS
# ============================================================

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

test_f2 = calculate_f2(
    test_precision,
    test_recall
)

test_accuracy = accuracy_score(
    y_test,
    test_pred
)


# ============================================================
# ORIGINAL CLASS ANALYSIS
# ============================================================

original_test_target = (
    df.loc[
        test_mask,
        "future_congestion"
    ]
    .to_numpy()
)


def class_risk_recall(
    class_name
):

    mask = (
        original_test_target
        ==
        class_name
    )

    if mask.sum() == 0:
        return 0.0

    return float(
        test_pred[mask].mean()
    )


test_high_recall = class_risk_recall(
    "HIGH"
)

test_congested_recall = class_risk_recall(
    "CONGESTED"
)

val_original_target = (
    df.loc[
        val_mask,
        "future_congestion"
    ]
    .to_numpy()
)

val_high_recall = float(
    val_pred[
        val_original_target == "HIGH"
    ].mean()
)

val_congested_recall = float(
    val_pred[
        val_original_target == "CONGESTED"
    ].mean()
)


# ============================================================
# TEST CONFUSION MATRIX
# ============================================================

print("\n========================================")
print(" V9 BINARY RISK PERFORMANCE")
print("========================================")

print(
    f"Risk Precision : "
    f"{test_precision:.4f}"
)

print(
    f"Risk Recall    : "
    f"{test_recall:.4f}"
)

print(
    f"Risk F1        : "
    f"{test_f1:.4f}"
)

print(
    f"Risk F2        : "
    f"{test_f2:.4f}"
)

print(
    f"Accuracy       : "
    f"{test_accuracy:.4f}"
)

print("\nHIGH / CONGESTED detection:")

print(
    f"HIGH detected as RISK      : "
    f"{test_high_recall:.4f}"
)

print(
    f"CONGESTED detected as RISK : "
    f"{test_congested_recall:.4f}"
)


cm = confusion_matrix(
    y_test,
    test_pred
)

cm_df = pd.DataFrame(
    cm,
    index=[
        "NON_RISK",
        "RISK"
    ],
    columns=[
        "PRED_NON_RISK",
        "PRED_RISK"
    ]
)

print("\nRisk confusion matrix:")

print(
    cm_df.to_string()
)


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
    digits=4,
    zero_division=0
)

print("\nClassification report:")

print(report)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n========================================")
print(" SAVING V9 MODEL")
print("========================================")

model.save_model(
    V9_MODEL
)

print(
    f"Model saved:\n{V9_MODEL}"
)


# ============================================================
# SAVE FEATURES
# ============================================================

with open(
    V9_FEATURES,
    "w"
) as f:

    json.dump(
        {
            "model_version": "v9",
            "base_features": BASE_FEATURES,
            "engineered_features": ENGINEERED_FEATURES,
            "all_features": FEATURES
        },
        f,
        indent=4
    )

print(
    f"Feature list saved:\n{V9_FEATURES}"
)


# ============================================================
# SAVE THRESHOLD
# ============================================================

threshold_data = {

    "model_version": "v9",

    "model_type":
        "independent_binary_xgboost",

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

    "prediction_horizon_steps": 300,

    "prediction_horizon_minutes": 5,

    "threshold": risk_threshold,

    "optimization": {
        "method": "validation_only",
        "objective": "F2",
        "beta": 2.0
    },

    "validation_metrics": {
        "precision": val_precision,
        "recall": val_recall,
        "f1": val_f1,
        "f2": val_f2,
        "high_detected_as_risk":
            val_high_recall,
        "congested_detected_as_risk":
            val_congested_recall
    },

    "test_metrics": {
        "precision": test_precision,
        "recall": test_recall,
        "f1": test_f1,
        "f2": test_f2,
        "high_detected_as_risk":
            test_high_recall,
        "congested_detected_as_risk":
            test_congested_recall
    }
}


with open(
    V9_THRESHOLDS,
    "w"
) as f:

    json.dump(
        threshold_data,
        f,
        indent=4
    )

print(
    f"Threshold data saved:\n{V9_THRESHOLDS}"
)


# ============================================================
# SAVE CONFUSION MATRIX
# ============================================================

cm_df.to_csv(
    V9_CONFUSION
)

print(
    f"Confusion matrix saved:\n{V9_CONFUSION}"
)


# ============================================================
# SAVE CLASSIFICATION REPORT
# ============================================================

with open(
    V9_REPORT,
    "w"
) as f:

    f.write(report)

    f.write(
        "\n\n========================================\n"
        "V9 RISK METRICS\n"
        "========================================\n\n"
    )

    f.write(
        f"Risk threshold: "
        f"{risk_threshold:.4f}\n"
    )

    f.write(
        f"Risk precision: "
        f"{test_precision:.4f}\n"
    )

    f.write(
        f"Risk recall: "
        f"{test_recall:.4f}\n"
    )

    f.write(
        f"Risk F1: "
        f"{test_f1:.4f}\n"
    )

    f.write(
        f"Risk F2: "
        f"{test_f2:.4f}\n"
    )

    f.write(
        f"HIGH detected as risk: "
        f"{test_high_recall:.4f}\n"
    )

    f.write(
        f"CONGESTED detected as risk: "
        f"{test_congested_recall:.4f}\n"
    )

print(
    f"Classification report saved:\n{V9_REPORT}"
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics = {

    "model":
        "trafficx_xgboost_v9",

    "model_type":
        "independent_binary_xgboost",

    "dataset":
        "trafficx_xgboost_v3_dataset.csv",

    "prediction_horizon_steps":
        300,

    "prediction_horizon_minutes":
        5,

    "base_features":
        len(BASE_FEATURES),

    "engineered_features":
        len(ENGINEERED_FEATURES),

    "total_features":
        len(FEATURES),

    "split": {
        "train": "0-499",
        "validation": "500-599",
        "test": "600-699"
    },

    "training": {

        "n_estimators":
            1500,

        "learning_rate":
            0.035,

        "max_depth":
            7,

        "min_child_weight":
            5,

        "subsample":
            0.85,

        "colsample_bytree":
            0.85,

        "gamma":
            0.05,

        "reg_alpha":
            0.05,

        "reg_lambda":
            1.5,

        "scale_pos_weight":
            float(scale_pos_weight)
    },

    "threshold": {

        "value":
            risk_threshold,

        "optimization":
            "validation_only_F2"
    },

    "validation": {

        "precision":
            val_precision,

        "recall":
            val_recall,

        "f1":
            val_f1,

        "f2":
            val_f2,

        "high_detected_as_risk":
            val_high_recall,

        "congested_detected_as_risk":
            val_congested_recall
    },

    "test": {

        "precision":
            test_precision,

        "recall":
            test_recall,

        "f1":
            test_f1,

        "f2":
            test_f2,

        "accuracy":
            test_accuracy,

        "high_detected_as_risk":
            test_high_recall,

        "congested_detected_as_risk":
            test_congested_recall
    }
}


with open(
    V9_METRICS,
    "w"
) as f:

    json.dump(
        metrics,
        f,
        indent=4
    )

print(
    f"Metrics saved:\n{V9_METRICS}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print(" TRAFFICX XGBOOST V9 COMPLETE")
print("========================================")

print("\nMODEL")
print("----------------------------------------")
print("trafficx_xgboost_v9.json")
print("Independent binary risk classifier")

print("\nRISK DEFINITION")
print("----------------------------------------")
print("NON_RISK = LOW + MEDIUM")
print("RISK     = HIGH + CONGESTED")

print("\nFEATURES")
print("----------------------------------------")
print(
    f"Base      : {len(BASE_FEATURES)}"
)

print(
    f"Engineered: {len(ENGINEERED_FEATURES)}"
)

print(
    f"Total     : {len(FEATURES)}"
)

print("\nTHRESHOLD")
print("----------------------------------------")
print(
    f"{risk_threshold:.3f}"
)

print("\nOPTIMIZATION")
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
    f"Risk Precision : "
    f"{test_precision:.4f}"
)

print(
    f"Risk Recall    : "
    f"{test_recall:.4f}"
)

print(
    f"Risk F1        : "
    f"{test_f1:.4f}"
)

print(
    f"Risk F2        : "
    f"{test_f2:.4f}"
)

print(
    f"Accuracy       : "
    f"{test_accuracy:.4f}"
)

print(
    f"HIGH as Risk   : "
    f"{test_high_recall:.4f}"
)

print(
    f"CONGESTED      : "
    f"{test_congested_recall:.4f}"
)

print("\nOUTPUTS")
print("----------------------------------------")

print(V9_MODEL)
print(V9_FEATURES)
print(V9_THRESHOLDS)
print(V9_METRICS)
print(V9_CONFUSION)
print(V9_REPORT)

print("\n========================================")
print(" TRAFFICX V9 TRAINING FINISHED")
print("========================================")