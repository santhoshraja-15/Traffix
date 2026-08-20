import os
import json
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score
)

# ============================================================
# TRAFFICX - V11
# TEMPORAL ROBUSTNESS & DISTRIBUTION ANALYSIS
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

V10_METRICS = os.path.join(
    BASE_DIR,
    "models",
    "trafficx_xgboost_v10_metrics.json"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "models"
)

DISTRIBUTION_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_temporal_distribution.csv"
)

PERFORMANCE_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_temporal_performance.csv"
)

SCENARIO_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_scenario_performance.csv"
)

QUARTILE_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_risk_probability_analysis.csv"
)

SHIFT_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_distribution_shift.csv"
)

SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "trafficx_v11_summary.json"
)

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

TARGET = "future_congestion"

RISK_CLASSES = {
    "HIGH",
    "CONGESTED"
}

THRESHOLD = 0.635


# ============================================================
# HEADERS
# ============================================================

print()
print("=" * 64)
print(" TRAFFICX - V11")
print(" TEMPORAL ROBUSTNESS & DISTRIBUTION ANALYSIS")
print("=" * 64)

print()
print("Dataset:")
print(DATASET)

print()
print("V10 Model:")
print(MODEL_PATH)


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
# VALIDATION
# ============================================================

required = FEATURES + [
    TARGET,
    "step"
]

missing = [
    col
    for col in required
    if col not in df.columns
]

if missing:

    print()
    print("ERROR: Missing columns:")

    for col in missing:
        print(" -", col)

    raise ValueError(
        "Required columns missing."
    )


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
# TEMPORAL PERIOD
# ============================================================

def assign_period(step):

    if 0 <= step <= 499:
        return "TRAIN"

    if 500 <= step <= 599:
        return "VALIDATION"

    if 600 <= step <= 699:
        return "TEST"

    return "OTHER"


df["period"] = df["step"].apply(
    assign_period
)

df = df[
    df["period"] != "OTHER"
].copy()


# ============================================================
# PERIOD SPLITS
# ============================================================

train_df = df[
    df["period"] == "TRAIN"
].copy()

val_df = df[
    df["period"] == "VALIDATION"
].copy()

test_df = df[
    df["period"] == "TEST"
].copy()


print()
print("=" * 64)
print(" TEMPORAL DATA")
print("=" * 64)

for name, frame in [
    ("TRAIN", train_df),
    ("VALIDATION", val_df),
    ("TEST", test_df)
]:

    print()
    print(name)

    print(
        "Rows:",
        len(frame)
    )

    print(
        "Risk:",
        f"{frame['risk_target'].mean():.4%}"
    )


# ============================================================
# SECTION 1
# FEATURE DISTRIBUTION
# ============================================================

print()
print("=" * 64)
print(" SECTION 1 - FEATURE DISTRIBUTION")
print("=" * 64)

distribution_rows = []

for feature in FEATURES:

    train_mean = train_df[feature].mean()
    val_mean = val_df[feature].mean()
    test_mean = test_df[feature].mean()

    train_std = train_df[feature].std()
    val_std = val_df[feature].std()
    test_std = test_df[feature].std()

    distribution_rows.append({

        "feature": feature,

        "train_mean": train_mean,
        "validation_mean": val_mean,
        "test_mean": test_mean,

        "train_std": train_std,
        "validation_std": val_std,
        "test_std": test_std,

        "validation_mean_change_pct":
            (
                (val_mean - train_mean)
                / (abs(train_mean) + 1e-9)
            ) * 100,

        "test_mean_change_pct":
            (
                (test_mean - train_mean)
                / (abs(train_mean) + 1e-9)
            ) * 100
    })


distribution_df = pd.DataFrame(
    distribution_rows
)

distribution_df.to_csv(
    DISTRIBUTION_FILE,
    index=False
)


# ============================================================
# TOP DISTRIBUTION SHIFTS
# ============================================================

shift_rows = []

for feature in FEATURES:

    train_mean = train_df[feature].mean()
    val_mean = val_df[feature].mean()
    test_mean = test_df[feature].mean()

    train_std = train_df[feature].std()

    val_shift = (
        abs(val_mean - train_mean)
        / (train_std + 1e-9)
    )

    test_shift = (
        abs(test_mean - train_mean)
        / (train_std + 1e-9)
    )

    shift_rows.append({

        "feature": feature,

        "validation_shift_std":
            val_shift,

        "test_shift_std":
            test_shift,

        "train_mean":
            train_mean,

        "validation_mean":
            val_mean,

        "test_mean":
            test_mean
    })


shift_df = pd.DataFrame(
    shift_rows
)

shift_df = shift_df.sort_values(
    "test_shift_std",
    ascending=False
)

shift_df.to_csv(
    SHIFT_FILE,
    index=False
)


print()
print("TOP 15 TEST DISTRIBUTION SHIFTS")
print()

print(
    shift_df.head(15).to_string(
        index=False
    )
)


# ============================================================
# SECTION 2
# LOAD V10 MODEL
# ============================================================

print()
print("=" * 64)
print(" SECTION 2 - LOAD V10")
print("=" * 64)

try:

    import xgboost as xgb

except ImportError:

    raise ImportError(
        "XGBoost is required."
    )


model = xgb.XGBClassifier()

model.load_model(
    MODEL_PATH
)

print()
print("V10 model loaded successfully.")


# ============================================================
# PREDICTIONS
# ============================================================

def predict_frame(frame):

    probabilities = model.predict_proba(
        frame[FEATURES]
    )[:, 1]

    predictions = (
        probabilities >= THRESHOLD
    ).astype(int)

    return probabilities, predictions


train_prob, train_pred = predict_frame(
    train_df
)

val_prob, val_pred = predict_frame(
    val_df
)

test_prob, test_pred = predict_frame(
    test_df
)


# ============================================================
# PERFORMANCE
# ============================================================

def evaluate(
    y_true,
    predictions,
    probabilities
):

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions
    ).ravel()

    return {

        "accuracy":
            accuracy_score(
                y_true,
                predictions
            ),

        "precision":
            precision_score(
                y_true,
                predictions,
                zero_division=0
            ),

        "recall":
            recall_score(
                y_true,
                predictions,
                zero_division=0
            ),

        "f1":
            f1_score(
                y_true,
                predictions,
                zero_division=0
            ),

        "roc_auc":
            roc_auc_score(
                y_true,
                probabilities
            ),

        "true_negative":
            int(tn),

        "false_positive":
            int(fp),

        "false_negative":
            int(fn),

        "true_positive":
            int(tp),

        "risk_rate":
            float(
                y_true.mean()
            ),

        "predicted_risk_rate":
            float(
                predictions.mean()
            ),

        "mean_probability":
            float(
                probabilities.mean()
            )
    }


performance_rows = []

for name, frame, probabilities, predictions in [

    (
        "TRAIN",
        train_df,
        train_prob,
        train_pred
    ),

    (
        "VALIDATION",
        val_df,
        val_prob,
        val_pred
    ),

    (
        "TEST",
        test_df,
        test_prob,
        test_pred
    )
]:

    metrics = evaluate(
        frame["risk_target"],
        predictions,
        probabilities
    )

    metrics["period"] = name

    performance_rows.append(
        metrics
    )


performance_df = pd.DataFrame(
    performance_rows
)

performance_df = performance_df[
    [
        "period",
        "risk_rate",
        "predicted_risk_rate",
        "mean_probability",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive"
    ]
]

performance_df.to_csv(
    PERFORMANCE_FILE,
    index=False
)


print()
print("=" * 64)
print(" V10 TEMPORAL PERFORMANCE")
print("=" * 64)

print()
print(
    performance_df.to_string(
        index=False
    )
)


# ============================================================
# SECTION 3
# SCENARIO ANALYSIS
# ============================================================

print()
print("=" * 64)
print(" SECTION 3 - SCENARIO PERFORMANCE")
print("=" * 64)

scenario_rows = []

for period, frame in [
    ("TRAIN", train_df),
    ("VALIDATION", val_df),
    ("TEST", test_df)
]:

    probabilities, predictions = predict_frame(
        frame
    )

    temp = frame.copy()

    temp["probability"] = probabilities
    temp["prediction"] = predictions

    for scenario in sorted(
        temp["scenario_encoded"].dropna().unique()
    ):

        subset = temp[
            temp["scenario_encoded"] == scenario
        ]

        if len(subset) < 10:
            continue

        y_true = subset["risk_target"]
        y_pred = subset["prediction"]

        scenario_rows.append({

            "period": period,

            "scenario_encoded": scenario,

            "rows": len(subset),

            "risk_rate":
                y_true.mean(),

            "predicted_risk_rate":
                y_pred.mean(),

            "precision":
                precision_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),

            "recall":
                recall_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),

            "f1":
                f1_score(
                    y_true,
                    y_pred,
                    zero_division=0
                ),

            "mean_probability":
                subset["probability"].mean()
        })


scenario_df = pd.DataFrame(
    scenario_rows
)

scenario_df.to_csv(
    SCENARIO_FILE,
    index=False
)

print()

if len(scenario_df) > 0:

    print(
        scenario_df.to_string(
            index=False
        )
    )

else:

    print(
        "No scenario groups available."
    )


# ============================================================
# SECTION 4
# PROBABILITY / RISK ANALYSIS
# ============================================================

print()
print("=" * 64)
print(" SECTION 4 - RISK PROBABILITY ANALYSIS")
print("=" * 64)

probability_rows = []

for period, frame, probabilities in [

    ("TRAIN", train_df, train_prob),
    ("VALIDATION", val_df, val_prob),
    ("TEST", test_df, test_prob)
]:

    temp = frame.copy()

    temp["probability"] = probabilities

    temp["probability_bin"] = pd.cut(
        temp["probability"],
        bins=[
            0.0,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1.0
        ],
        include_lowest=True
    )

    grouped = temp.groupby(
        "probability_bin",
        observed=False
    )

    for probability_bin, subset in grouped:

        if len(subset) == 0:
            continue

        probability_rows.append({

            "period": period,

            "probability_bin":
                str(probability_bin),

            "rows":
                len(subset),

            "actual_risk_rate":
                subset["risk_target"].mean(),

            "mean_probability":
                subset["probability"].mean()
        })


probability_df = pd.DataFrame(
    probability_rows
)

probability_df.to_csv(
    QUARTILE_FILE,
    index=False
)


print()

print(
    probability_df.to_string(
        index=False
    )
)


# ============================================================
# SECTION 5
# TOP FEATURES BY V10 IMPORTANCE
# ============================================================

print()
print("=" * 64)
print(" SECTION 5 - V10 FEATURE IMPORTANCE")
print("=" * 64)

importance_df = pd.DataFrame({

    "feature": FEATURES,

    "importance":
        model.feature_importances_
})

importance_df = importance_df.sort_values(
    "importance",
    ascending=False
)

print()
print(
    importance_df.head(20).to_string(
        index=False
    )
)


# ============================================================
# SECTION 6
# TEMPORAL GENERALIZATION GAP
# ============================================================

train_f2 = None
val_f2 = None
test_f2 = None


def calculate_f2(
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


performance_df["f2"] = performance_df.apply(
    lambda row: calculate_f2(
        row["precision"],
        row["recall"]
    ),
    axis=1
)


train_f2 = float(
    performance_df[
        performance_df["period"] == "TRAIN"
    ]["f2"].iloc[0]
)

val_f2 = float(
    performance_df[
        performance_df["period"] == "VALIDATION"
    ]["f2"].iloc[0]
)

test_f2 = float(
    performance_df[
        performance_df["period"] == "TEST"
    ]["f2"].iloc[0]
)


validation_gap = (
    train_f2 - val_f2
)

test_gap = (
    val_f2 - test_f2
)

total_gap = (
    train_f2 - test_f2
)


print()
print("=" * 64)
print(" TEMPORAL GENERALIZATION")
print("=" * 64)

print()
print(
    f"TRAIN F2      : {train_f2:.4f}"
)

print(
    f"VALIDATION F2 : {val_f2:.4f}"
)

print(
    f"TEST F2       : {test_f2:.4f}"
)

print()
print(
    f"TRAIN → VAL gap : {validation_gap:.4f}"
)

print(
    f"VAL → TEST gap  : {test_gap:.4f}"
)

print(
    f"TRAIN → TEST gap: {total_gap:.4f}"
)


# ============================================================
# SECTION 7
# AUTOMATIC DIAGNOSTIC
# ============================================================

print()
print("=" * 64)
print(" V11 DIAGNOSTIC")
print("=" * 64)

test_shift_top = shift_df.iloc[0]

largest_shift_feature = (
    test_shift_top["feature"]
)

largest_shift_value = (
    test_shift_top["test_shift_std"]
)


risk_train = train_df[
    "risk_target"
].mean()

risk_val = val_df[
    "risk_target"
].mean()

risk_test = test_df[
    "risk_target"
].mean()


print()

print(
    "Largest test distribution shift:"
)

print(
    f"  {largest_shift_feature}"
)

print(
    f"  Shift = {largest_shift_value:.4f} std"
)

print()

print(
    "Risk prevalence:"
)

print(
    f"  Train      = {risk_train:.4%}"
)

print(
    f"  Validation = {risk_val:.4%}"
)

print(
    f"  Test       = {risk_test:.4%}"
)

print()

if test_gap <= 0.03:

    robustness_status = (
        "GOOD - small temporal degradation"
    )

elif test_gap <= 0.06:

    robustness_status = (
        "MODERATE - noticeable temporal degradation"
    )

else:

    robustness_status = (
        "HIGH SHIFT - significant temporal degradation"
    )


print(
    "Robustness status:"
)

print(
    f"  {robustness_status}"
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = {

    "version": "V11",

    "analysis": (
        "Temporal robustness and "
        "distribution analysis"
    ),

    "model": "trafficx_xgboost_v10",

    "threshold": THRESHOLD,

    "risk_prevalence": {

        "train":
            float(risk_train),

        "validation":
            float(risk_val),

        "test":
            float(risk_test)
    },

    "f2": {

        "train":
            train_f2,

        "validation":
            val_f2,

        "test":
            test_f2
    },

    "generalization_gap": {

        "train_to_validation":
            validation_gap,

        "validation_to_test":
            test_gap,

        "train_to_test":
            total_gap
    },

    "largest_test_shift_feature":
        largest_shift_feature,

    "largest_test_shift_std":
        float(largest_shift_value),

    "robustness_status":
        robustness_status
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
# OUTPUT FILES
# ============================================================

print()
print("=" * 64)
print(" OUTPUT FILES")
print("=" * 64)

print()
print(DISTRIBUTION_FILE)

print(
    PERFORMANCE_FILE
)

print(
    SCENARIO_FILE
)

print(
    QUARTILE_FILE
)

print(
    SHIFT_FILE
)

print(
    SUMMARY_FILE
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 64)
print(" TRAFFICX V11 ANALYSIS COMPLETE")
print("=" * 64)

print()
print(
    "V10 remains unchanged."
)

print(
    "No model was retrained."
)

print(
    "No test data was used for model modification."
)

print()
print(
    "Next decision should be based on this diagnostic."
)

print()
print("=" * 64)