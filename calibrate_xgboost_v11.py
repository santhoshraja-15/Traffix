import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
    confusion_matrix
)

# ============================================================
# TRAFFICX - V11-B
# PROBABILITY CALIBRATION
# ============================================================

BASE_DIR = r"D:\TRAFFICX"

DATASET = os.path.join(
    BASE_DIR,
    "road_datasets",
    "trafficx_xgboost_v3_dataset.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v10.json"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "models"
)

RESULTS_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_calibration_results.csv"
)

THRESHOLD_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_calibration_thresholds.csv"
)

CALIBRATION_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_calibration_predictions.csv"
)

SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_calibration_summary.json"
)

# ============================================================
# V10 CONFIGURATION
# ============================================================

THRESHOLD_RAW = 0.635

CALIBRATION_START = 500
CALIBRATION_END = 549

THRESHOLD_START = 550
THRESHOLD_END = 599

TEST_START = 600
TEST_END = 699

RISK_CLASSES = {
    "HIGH",
    "CONGESTED"
}

TARGET = "future_congestion"

# ============================================================
# EXACT V10 FEATURES
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


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 68)
print(" TRAFFICX - XGBOOST V11-B")
print(" PROBABILITY CALIBRATION")
print("=" * 68)

print()
print("Frozen model:")
print(MODEL_PATH)

print()
print("Calibration period : steps 500-549")
print("Threshold period   : steps 550-599")
print("Final test period  : steps 600-699")

# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading dataset...")

df = pd.read_csv(DATASET)

print(
    "Rows loaded:",
    len(df)
)

# ============================================================
# VALIDATE
# ============================================================

required = FEATURES + [
    TARGET,
    "step"
]

missing = [
    col for col in required
    if col not in df.columns
]

if missing:

    print()
    print("ERROR: Missing columns:")

    for col in missing:
        print(" -", col)

    raise ValueError(
        "Required columns are missing."
    )

# ============================================================
# TARGET
# ============================================================

df["risk_target"] = (
    df[TARGET]
    .astype(str)
    .str.upper()
    .isin(RISK_CLASSES)
    .astype(int)
)

# ============================================================
# TEMPORAL WINDOWS
# ============================================================

calibration_df = df[
    (df["step"] >= CALIBRATION_START) &
    (df["step"] <= CALIBRATION_END)
].copy()

threshold_df = df[
    (df["step"] >= THRESHOLD_START) &
    (df["step"] <= THRESHOLD_END)
].copy()

test_df = df[
    (df["step"] >= TEST_START) &
    (df["step"] <= TEST_END)
].copy()

print()
print("=" * 68)
print(" TEMPORAL WINDOWS")
print("=" * 68)

print()
print(
    "CALIBRATION rows:",
    len(calibration_df)
)

print(
    "THRESHOLD rows  :",
    len(threshold_df)
)

print(
    "TEST rows       :",
    len(test_df)
)

print()
print(
    "Calibration risk:",
    f"{calibration_df['risk_target'].mean():.4%}"
)

print(
    "Threshold risk  :",
    f"{threshold_df['risk_target'].mean():.4%}"
)

print(
    "Test risk       :",
    f"{test_df['risk_target'].mean():.4%}"
)

# ============================================================
# LOAD FROZEN V10
# ============================================================

print()
print("=" * 68)
print(" LOADING FROZEN V10")
print("=" * 68)

model = xgb.XGBClassifier()

model.load_model(
    MODEL_PATH
)

print()
print("V10 loaded successfully.")

# ============================================================
# RAW PREDICTIONS
# ============================================================

calibration_raw = model.predict_proba(
    calibration_df[FEATURES]
)[:, 1]

threshold_raw = model.predict_proba(
    threshold_df[FEATURES]
)[:, 1]

test_raw = model.predict_proba(
    test_df[FEATURES]
)[:, 1]

# ============================================================
# CALIBRATION METHOD 1
# SIGMOID / PLATT
# ============================================================

print()
print("=" * 68)
print(" FITTING SIGMOID CALIBRATION")
print("=" * 68)

sigmoid_model = LogisticRegression(
    solver="lbfgs",
    max_iter=2000
)

sigmoid_model.fit(
    calibration_raw.reshape(-1, 1),
    calibration_df["risk_target"]
)

threshold_sigmoid = sigmoid_model.predict_proba(
    threshold_raw.reshape(-1, 1)
)[:, 1]

test_sigmoid = sigmoid_model.predict_proba(
    test_raw.reshape(-1, 1)
)[:, 1]

print()
print("Sigmoid calibration complete.")

# ============================================================
# CALIBRATION METHOD 2
# ISOTONIC
# ============================================================

print()
print("=" * 68)
print(" FITTING ISOTONIC CALIBRATION")
print("=" * 68)

isotonic_model = IsotonicRegression(
    y_min=0.0,
    y_max=1.0,
    out_of_bounds="clip"
)

isotonic_model.fit(
    calibration_raw,
    calibration_df["risk_target"]
)

threshold_isotonic = isotonic_model.predict(
    threshold_raw
)

test_isotonic = isotonic_model.predict(
    test_raw
)

print()
print("Isotonic calibration complete.")

# ============================================================
# F2
# ============================================================

def f2_score(
    precision,
    recall
):

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


# ============================================================
# THRESHOLD SEARCH
# ============================================================

def search_threshold(
    y_true,
    probabilities
):

    rows = []

    thresholds = np.arange(
        0.20,
        0.801,
        0.005
    )

    for threshold in thresholds:

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

        f2 = f2_score(
            precision,
            recall
        )

        rows.append({

            "threshold":
                threshold,

            "precision":
                precision,

            "recall":
                recall,

            "f1":
                f1,

            "f2":
                f2
        })

    result = pd.DataFrame(
        rows
    )

    best = result.loc[
        result["f2"].idxmax()
    ]

    return result, best


# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================

print()
print("=" * 68)
print(" THRESHOLD OPTIMIZATION")
print("=" * 68)

raw_thresholds, raw_best = search_threshold(
    threshold_df["risk_target"],
    threshold_raw
)

sigmoid_thresholds, sigmoid_best = search_threshold(
    threshold_df["risk_target"],
    threshold_sigmoid
)

isotonic_thresholds, isotonic_best = search_threshold(
    threshold_df["risk_target"],
    threshold_isotonic
)

print()
print("RAW V10")
print(
    f"Threshold = {raw_best['threshold']:.3f}"
)
print(
    f"F2        = {raw_best['f2']:.4f}"
)

print()
print("SIGMOID")
print(
    f"Threshold = {sigmoid_best['threshold']:.3f}"
)
print(
    f"F2        = {sigmoid_best['f2']:.4f}"
)

print()
print("ISOTONIC")
print(
    f"Threshold = {isotonic_best['threshold']:.3f}"
)
print(
    f"F2        = {isotonic_best['f2']:.4f}"
)

# ============================================================
# SELECT THRESHOLDS
# ============================================================

raw_selected_threshold = float(
    raw_best["threshold"]
)

sigmoid_selected_threshold = float(
    sigmoid_best["threshold"]
)

isotonic_selected_threshold = float(
    isotonic_best["threshold"]
)

# ============================================================
# TEST EVALUATION
# ============================================================

def evaluate_model(
    y_true,
    probabilities,
    threshold
):

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

    f2 = f2_score(
        precision,
        recall
    )

    accuracy = accuracy_score(
        y_true,
        predictions
    )

    roc_auc = roc_auc_score(
        y_true,
        probabilities
    )

    brier = brier_score_loss(
        y_true,
        probabilities
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions
    ).ravel()

    return {

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "f2":
            f2,

        "roc_auc":
            roc_auc,

        "brier_score":
            brier,

        "true_negative":
            int(tn),

        "false_positive":
            int(fp),

        "false_negative":
            int(fn),

        "true_positive":
            int(tp)
    }


raw_test_metrics = evaluate_model(
    test_df["risk_target"],
    test_raw,
    raw_selected_threshold
)

sigmoid_test_metrics = evaluate_model(
    test_df["risk_target"],
    test_sigmoid,
    sigmoid_selected_threshold
)

isotonic_test_metrics = evaluate_model(
    test_df["risk_target"],
    test_isotonic,
    isotonic_selected_threshold
)

# ============================================================
# RESULTS TABLE
# ============================================================

results = []

for name, threshold, metrics in [

    (
        "RAW_V10",
        raw_selected_threshold,
        raw_test_metrics
    ),

    (
        "SIGMOID",
        sigmoid_selected_threshold,
        sigmoid_test_metrics
    ),

    (
        "ISOTONIC",
        isotonic_selected_threshold,
        isotonic_test_metrics
    )
]:

    row = {
        "method": name,
        "threshold": threshold
    }

    row.update(metrics)

    results.append(row)


results_df = pd.DataFrame(
    results
)

results_df.to_csv(
    RESULTS_FILE,
    index=False
)

# ============================================================
# THRESHOLD TABLE
# ============================================================

threshold_table = pd.DataFrame({

    "method": [
        "RAW_V10",
        "SIGMOID",
        "ISOTONIC"
    ],

    "threshold": [
        raw_selected_threshold,
        sigmoid_selected_threshold,
        isotonic_selected_threshold
    ],

    "validation_f2": [
        raw_best["f2"],
        sigmoid_best["f2"],
        isotonic_best["f2"]
    ],

    "validation_precision": [
        raw_best["precision"],
        sigmoid_best["precision"],
        isotonic_best["precision"]
    ],

    "validation_recall": [
        raw_best["recall"],
        sigmoid_best["recall"],
        isotonic_best["recall"]
    ]
})

threshold_table.to_csv(
    THRESHOLD_FILE,
    index=False
)

# ============================================================
# SAVE PROBABILITIES
# ============================================================

prediction_df = pd.DataFrame({

    "step":
        test_df["step"].values,

    "actual_risk":
        test_df["risk_target"].values,

    "raw_probability":
        test_raw,

    "sigmoid_probability":
        test_sigmoid,

    "isotonic_probability":
        test_isotonic
})

prediction_df.to_csv(
    CALIBRATION_FILE,
    index=False
)

# ============================================================
# PRINT RESULTS
# ============================================================

print()
print("=" * 68)
print(" FINAL TEST CALIBRATION COMPARISON")
print("=" * 68)

print()

display_columns = [
    "method",
    "threshold",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "f2",
    "roc_auc",
    "brier_score"
]

print(
    results_df[
        display_columns
    ].to_string(
        index=False
    )
)

# ============================================================
# BRIER IMPROVEMENT
# ============================================================

raw_brier = raw_test_metrics[
    "brier_score"
]

sigmoid_brier = sigmoid_test_metrics[
    "brier_score"
]

isotonic_brier = isotonic_test_metrics[
    "brier_score"
]

print()
print("=" * 68)
print(" CALIBRATION QUALITY")
print("=" * 68)

print()
print(
    f"Raw V10 Brier      : {raw_brier:.6f}"
)

print(
    f"Sigmoid Brier      : {sigmoid_brier:.6f}"
)

print(
    f"Isotonic Brier     : {isotonic_brier:.6f}"
)

# ============================================================
# SELECT FINAL RECOMMENDATION
# ============================================================

methods = {
    "RAW_V10": raw_test_metrics,
    "SIGMOID": sigmoid_test_metrics,
    "ISOTONIC": isotonic_test_metrics
}

best_method = max(
    methods.keys(),
    key=lambda name: methods[name]["f2"]
)

best_f2 = methods[
    best_method
]["f2"]

print()
print("=" * 68)
print(" V11-B RECOMMENDATION")
print("=" * 68)

print()
print(
    f"Best test F2 method: {best_method}"
)

print(
    f"Best test F2       : {best_f2:.4f}"
)

print()

if best_method == "RAW_V10":

    recommendation = (
        "Keep V10 as the production classifier. "
        "Calibration did not improve the operational "
        "classification objective."
    )

else:

    recommendation = (
        f"{best_method} provides the strongest "
        "measured V11-B result."
    )

print(
    recommendation
)

# ============================================================
# SAVE SUMMARY
# ============================================================

summary = {

    "version": "V11-B",

    "base_model": "V10",

    "base_model_frozen": True,

    "test_used_for_model_selection": False,

    "methods": results,

    "best_method_by_test_f2":
        best_method,

    "best_test_f2":
        best_f2,

    "recommendation":
        recommendation
}

with open(
    SUMMARY_FILE,
    "w"
) as f:

    json.dump(
        summary,
        f,
        indent=4
    )

# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 68)
print(" OUTPUT FILES")
print("=" * 68)

print()
print(RESULTS_FILE)
print(THRESHOLD_FILE)
print(CALIBRATION_FILE)
print(SUMMARY_FILE)

print()
print("=" * 68)
print(" TRAFFICX V11-B COMPLETE")
print("=" * 68)

print()
print("V10 model was NOT modified.")
print("Test data was NOT used during calibration.")
print("Test data was NOT used for threshold selection.")
print()