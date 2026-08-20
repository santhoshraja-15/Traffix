import os
import json
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)

warnings.filterwarnings("ignore")


# ============================================================
# TRAFFICX - XGBOOST V14
# EARLY RISK PREDICTION
# ============================================================

print("=" * 70)
print(" TRAFFICX - XGBOOST V14")
print(" EARLY RISK PREDICTION")
print(" TEMPORAL GENERALIZATION + SHORTCUT REMOVAL")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

DATASET = r"D:\TRAFFICX\road_datasets\trafficx_ml_dataset_v2.csv"

MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_early_risk.json"
)

RESULTS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_results.csv"
)

THRESHOLD_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_thresholds.csv"
)

IMPORTANCE_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_feature_importance.csv"
)

PREDICTIONS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_test_predictions.csv"
)

SCENARIO_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v14_scenario_performance.csv"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42

# Future target
RISK_CLASSES = [
    "HIGH",
    "CONGESTED"
]

# Temporal split
TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15

# Threshold search
THRESHOLD_MIN = 0.10
THRESHOLD_MAX = 0.90
THRESHOLD_STEP = 0.01


# ============================================================
# LOAD DATASET
# ============================================================

print("\n" + "=" * 70)
print(" LOADING V2 DATASET")
print("=" * 70)

print(f"\nDataset:")
print(DATASET)

if not os.path.exists(DATASET):
    raise FileNotFoundError(
        f"\nDataset not found:\n{DATASET}"
    )

df = pd.read_csv(DATASET)

print(f"\nRows loaded    : {len(df):,}")
print(f"Columns loaded : {len(df.columns)}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "scenario",
    "step",
    "road_id",
    "road_length_m",
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",

    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",

    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",

    "speed_change_pct",
    "vehicle_change_pct",

    "vehicles_per_100m",
    "queue_ratio",

    "future_congestion",
]


missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    raise RuntimeError(
        "\nMissing required columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# CREATE BINARY FUTURE RISK TARGET
# ============================================================

print("\n" + "=" * 70)
print(" CREATING FUTURE RISK TARGET")
print("=" * 70)

df["future_risk"] = (
    df["future_congestion"]
    .isin(RISK_CLASSES)
    .astype(np.int8)
)

print("\nFuture risk distribution:")

print(
    df["future_risk"]
    .value_counts()
    .sort_index()
)

print("\nFuture risk percentages:")

print(
    (
        df["future_risk"]
        .value_counts(normalize=True)
        .sort_index()
        * 100
    ).round(3)
)


# ============================================================
# SORT TEMPORALLY
# ============================================================

print("\n" + "=" * 70)
print(" TEMPORAL ORDERING")
print("=" * 70)

df = df.sort_values(
    ["step", "scenario", "road_id"]
).reset_index(drop=True)

print(
    f"\nMinimum step : {df['step'].min()}"
)

print(
    f"Maximum step : {df['step'].max()}"
)


# ============================================================
# TEMPORAL SPLIT
# ============================================================

unique_steps = np.sort(
    df["step"].unique()
)

n_steps = len(unique_steps)

train_end_index = int(
    n_steps * TRAIN_FRACTION
)

validation_end_index = int(
    n_steps *
    (TRAIN_FRACTION + VALIDATION_FRACTION)
)

train_end_step = unique_steps[
    train_end_index - 1
]

validation_end_step = unique_steps[
    validation_end_index - 1
]

print("\n" + "=" * 70)
print(" TEMPORAL TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

print(
    f"\nTotal unique steps : {n_steps}"
)

print(
    f"\nTRAIN")
print(
    f"Steps: {unique_steps[0]} -> {train_end_step}"
)

print(
    f"\nVALIDATION")
print(
    f"Steps: {unique_steps[train_end_index]} "
    f"-> {validation_end_step}"
)

print(
    f"\nTEST")
print(
    f"Steps: {unique_steps[validation_end_index]} "
    f"-> {unique_steps[-1]}"
)


train_df = df[
    df["step"] <= train_end_step
].copy()

validation_df = df[
    (df["step"] > train_end_step)
    &
    (df["step"] <= validation_end_step)
].copy()

test_df = df[
    df["step"] > validation_end_step
].copy()


print("\nRows:")

print(
    f"TRAIN      : {len(train_df):,}"
)

print(
    f"VALIDATION : {len(validation_df):,}"
)

print(
    f"TEST       : {len(test_df):,}"
)


# ============================================================
# TARGET DISTRIBUTION BY SPLIT
# ============================================================

print("\n" + "=" * 70)
print(" TARGET DISTRIBUTION BY SPLIT")
print("=" * 70)


def print_distribution(name, data):

    counts = (
        data["future_risk"]
        .value_counts()
        .sort_index()
    )

    percentages = (
        data["future_risk"]
        .value_counts(normalize=True)
        .sort_index()
        * 100
    )

    print(f"\n{name}")

    print(
        f"NON-RISK : {counts.get(0, 0):,} "
        f"({percentages.get(0, 0):.3f}%)"
    )

    print(
        f"RISK     : {counts.get(1, 0):,} "
        f"({percentages.get(1, 0):.3f}%)"
    )


print_distribution("TRAIN", train_df)
print_distribution("VALIDATION", validation_df)
print_distribution("TEST", test_df)


# ============================================================
# FEATURES
#
# IMPORTANT:
# Remove:
#   has_stopped_vehicles
#   has_vehicles
#   has_queue
#   stopped_vehicle_ratio
#
# This forces the model to learn continuous traffic dynamics.
# ============================================================

FEATURES = [

    # Current traffic state
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",

    # Road characteristics
    "road_length_m",

    # Normalized traffic features
    "vehicles_per_100m",
    "queue_ratio",

    # Previous state
    "previous_speed_kmh",
    "previous_vehicle_count",
    "previous_density",
    "previous_queue_length_m",

    # Temporal changes
    "speed_change_kmh",
    "vehicle_change",
    "density_change",
    "queue_change_m",

    # Percentage changes
    "speed_change_pct",
    "vehicle_change_pct",
]


print("\n" + "=" * 70)
print(" V14 FEATURES")
print("=" * 70)

for i, feature in enumerate(FEATURES):

    print(
        f"{i + 1:02d}. {feature}"
    )

print(
    f"\nTotal features: {len(FEATURES)}"
)


# ============================================================
# CREATE MATRICES
# ============================================================

X_train = train_df[FEATURES]
y_train = train_df["future_risk"]

X_validation = validation_df[FEATURES]
y_validation = validation_df["future_risk"]

X_test = test_df[FEATURES]
y_test = test_df["future_risk"]


# ============================================================
# CLASS IMBALANCE
# ============================================================

negative_count = int(
    (y_train == 0).sum()
)

positive_count = int(
    (y_train == 1).sum()
)

scale_pos_weight = (
    negative_count / positive_count
)

print("\n" + "=" * 70)
print(" CLASS IMBALANCE")
print("=" * 70)

print(
    f"\nNON-RISK : {negative_count:,}"
)

print(
    f"RISK     : {positive_count:,}"
)

print(
    f"\nscale_pos_weight : "
    f"{scale_pos_weight:.4f}"
)


# ============================================================
# XGBOOST MODEL
# ============================================================

print("\n" + "=" * 70)
print(" TRAINING XGBOOST V14")
print("=" * 70)


model = xgb.XGBClassifier(

    objective="binary:logistic",

    n_estimators=700,

    max_depth=7,

    learning_rate=0.05,

    subsample=0.85,

    colsample_bytree=0.85,

    min_child_weight=5,

    gamma=0.05,

    reg_alpha=0.05,

    reg_lambda=1.5,

    scale_pos_weight=scale_pos_weight,

    eval_metric="aucpr",

    tree_method="hist",

    random_state=RANDOM_STATE,

    n_jobs=-1,

)


model.fit(
    X_train,
    y_train,

    eval_set=[
        (X_train, y_train),
        (X_validation, y_validation),
    ],

    verbose=50,
)


print("\nTraining complete.")


# ============================================================
# VALIDATION PROBABILITIES
# ============================================================

print("\n" + "=" * 70)
print(" VALIDATION PROBABILITIES")
print("=" * 70)


validation_probability = (
    model.predict_proba(X_validation)[:, 1]
)


validation_roc_auc = roc_auc_score(
    y_validation,
    validation_probability
)

validation_pr_auc = average_precision_score(
    y_validation,
    validation_probability
)


print(
    f"\nValidation ROC-AUC : "
    f"{validation_roc_auc:.4f}"
)

print(
    f"Validation PR-AUC  : "
    f"{validation_pr_auc:.4f}"
)


# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================

print("\n" + "=" * 70)
print(" THRESHOLD OPTIMIZATION")
print("=" * 70)


threshold_rows = []

thresholds = np.arange(
    THRESHOLD_MIN,
    THRESHOLD_MAX + THRESHOLD_STEP / 2,
    THRESHOLD_STEP
)


for threshold in thresholds:

    prediction = (
        validation_probability >= threshold
    ).astype(int)

    precision = precision_score(
        y_validation,
        prediction,
        zero_division=0
    )

    recall = recall_score(
        y_validation,
        prediction,
        zero_division=0
    )

    f1 = f1_score(
        y_validation,
        prediction,
        zero_division=0
    )

    cm = confusion_matrix(
        y_validation,
        prediction
    )

    tn, fp, fn, tp = cm.ravel()

    false_alarm_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0
    )

    threshold_rows.append({

        "threshold": threshold,

        "precision": precision,

        "recall": recall,

        "f1": f1,

        "false_alarm_rate":
            false_alarm_rate,

        "true_positive": tp,

        "false_positive": fp,

        "true_negative": tn,

        "false_negative": fn,

    })


threshold_df = pd.DataFrame(
    threshold_rows
)


# ============================================================
# OPERATING THRESHOLD
#
# Prefer precision while maintaining
# at least 65% recall.
# ============================================================

minimum_recall = 0.65

eligible = threshold_df[
    threshold_df["recall"] >= minimum_recall
].copy()


if len(eligible) > 0:

    best_row = eligible.sort_values(
        [
            "f1",
            "precision"
        ],
        ascending=False
    ).iloc[0]

else:

    best_row = threshold_df.sort_values(
        "f1",
        ascending=False
    ).iloc[0]


OPERATING_THRESHOLD = float(
    best_row["threshold"]
)


print(
    f"\nSelected threshold: "
    f"{OPERATING_THRESHOLD:.2f}"
)

print(
    f"\nValidation precision : "
    f"{best_row['precision']:.4f}"
)

print(
    f"Validation recall    : "
    f"{best_row['recall']:.4f}"
)

print(
    f"Validation F1        : "
    f"{best_row['f1']:.4f}"
)

print(
    f"False alarm rate     : "
    f"{best_row['false_alarm_rate']:.4f}"
)


threshold_df.to_csv(
    THRESHOLD_PATH,
    index=False
)

print(
    f"\nThreshold results saved:"
    f"\n{THRESHOLD_PATH}"
)


# ============================================================
# FINAL TEST PREDICTION
# ============================================================

print("\n" + "=" * 70)
print(" FINAL TEST EVALUATION")
print("=" * 70)


test_probability = (
    model.predict_proba(X_test)[:, 1]
)


test_prediction = (
    test_probability >= OPERATING_THRESHOLD
).astype(int)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    test_prediction
)

precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0
)

recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0
)

f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    test_probability
)

pr_auc = average_precision_score(
    y_test,
    test_probability
)


cm = confusion_matrix(
    y_test,
    test_prediction
)

tn, fp, fn, tp = cm.ravel()


false_alarm_rate = (
    fp / (fp + tn)
)

miss_rate = (
    fn / (fn + tp)
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 70)
print(" V14 TEST RESULTS")
print("=" * 70)

print(
    f"\nThreshold         : "
    f"{OPERATING_THRESHOLD:.2f}"
)

print(
    f"Accuracy          : "
    f"{accuracy:.4f}"
)

print(
    f"Precision         : "
    f"{precision:.4f}"
)

print(
    f"Risk Recall       : "
    f"{recall:.4f}"
)

print(
    f"F1 Score          : "
    f"{f1:.4f}"
)

print(
    f"ROC-AUC           : "
    f"{roc_auc:.4f}"
)

print(
    f"PR-AUC            : "
    f"{pr_auc:.4f}"
)

print(
    f"False Alarm Rate  : "
    f"{false_alarm_rate:.4f}"
)

print(
    f"Miss Rate         : "
    f"{miss_rate:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\nConfusion Matrix:\n")

print(
    "                 Predicted"
)

print(
    "              NON-RISK   RISK"
)

print(
    f"Actual NON-RISK "
    f"{tn:10,} "
    f"{fp:10,}"
)

print(
    f"Actual RISK     "
    f"{fn:10,} "
    f"{tp:10,}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 70)
print(" CLASSIFICATION REPORT")
print("=" * 70)

print()

print(
    classification_report(
        y_test,
        test_prediction,
        target_names=[
            "NON_RISK",
            "RISK"
        ],
        digits=4,
        zero_division=0
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print(" FEATURE IMPORTANCE")
print("=" * 70)


importance = model.feature_importances_


importance_df = pd.DataFrame({

    "feature": FEATURES,

    "importance": importance

}).sort_values(
    "importance",
    ascending=False
)


for _, row in importance_df.iterrows():

    print(
        f"{row['feature']:<32} "
        f"{row['importance']:.6f}"
    )


importance_df.to_csv(
    IMPORTANCE_PATH,
    index=False
)


# ============================================================
# SCENARIO-WISE PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print(" SCENARIO-WISE PERFORMANCE")
print("=" * 70)


scenario_rows = []


for scenario in sorted(
    test_df["scenario"].unique()
):

    mask = (
        test_df["scenario"] == scenario
    )

    y_true_s = y_test.loc[mask]

    y_pred_s = pd.Series(
        test_prediction,
        index=y_test.index
    ).loc[mask]

    y_prob_s = pd.Series(
        test_probability,
        index=y_test.index
    ).loc[mask]


    scenario_accuracy = accuracy_score(
        y_true_s,
        y_pred_s
    )

    scenario_precision = precision_score(
        y_true_s,
        y_pred_s,
        zero_division=0
    )

    scenario_recall = recall_score(
        y_true_s,
        y_pred_s,
        zero_division=0
    )

    scenario_f1 = f1_score(
        y_true_s,
        y_pred_s,
        zero_division=0
    )


    try:

        scenario_roc_auc = roc_auc_score(
            y_true_s,
            y_prob_s
        )

    except ValueError:

        scenario_roc_auc = np.nan


    try:

        scenario_pr_auc = average_precision_score(
            y_true_s,
            y_prob_s
        )

    except ValueError:

        scenario_pr_auc = np.nan


    scenario_cm = confusion_matrix(
        y_true_s,
        y_pred_s,
        labels=[0, 1]
    )

    s_tn, s_fp, s_fn, s_tp = (
        scenario_cm.ravel()
    )

    scenario_far = (
        s_fp / (s_fp + s_tn)
        if (s_fp + s_tn) > 0
        else 0
    )


    scenario_rows.append({

        "scenario": scenario,

        "samples": len(y_true_s),

        "risk_samples":
            int(y_true_s.sum()),

        "accuracy":
            scenario_accuracy,

        "precision":
            scenario_precision,

        "recall":
            scenario_recall,

        "f1":
            scenario_f1,

        "roc_auc":
            scenario_roc_auc,

        "pr_auc":
            scenario_pr_auc,

        "false_alarm_rate":
            scenario_far,

        "true_positive":
            s_tp,

        "false_positive":
            s_fp,

        "true_negative":
            s_tn,

        "false_negative":
            s_fn,

    })


scenario_df = pd.DataFrame(
    scenario_rows
)


print()

print(
    scenario_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


scenario_df.to_csv(
    SCENARIO_PATH,
    index=False
)


# ============================================================
# SAVE RESULTS
# ============================================================

results = {

    "model": "TRAFFICX XGBoost V14",

    "dataset": DATASET,

    "features": len(FEATURES),

    "train_rows": len(train_df),

    "validation_rows":
        len(validation_df),

    "test_rows": len(test_df),

    "threshold":
        OPERATING_THRESHOLD,

    "accuracy":
        accuracy,

    "precision":
        precision,

    "risk_recall":
        recall,

    "f1":
        f1,

    "roc_auc":
        roc_auc,

    "pr_auc":
        pr_auc,

    "false_alarm_rate":
        false_alarm_rate,

    "miss_rate":
        miss_rate,

    "true_positive":
        tp,

    "false_positive":
        fp,

    "true_negative":
        tn,

    "false_negative":
        fn,

    "validation_roc_auc":
        validation_roc_auc,

    "validation_pr_auc":
        validation_pr_auc,

}


results_df = pd.DataFrame(
    [results]
)


results_df.to_csv(
    RESULTS_PATH,
    index=False
)


# ============================================================
# SAVE TEST PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print(" SAVING TEST PREDICTIONS")
print("=" * 70)


prediction_output = test_df[
    [
        "scenario",
        "step",
        "road_id",
        "future_congestion",
        "future_risk",
    ]
].copy()


prediction_output[
    "risk_probability"
] = test_probability


prediction_output[
    "predicted_risk"
] = test_prediction


prediction_output[
    "operating_threshold"
] = OPERATING_THRESHOLD


prediction_output.to_csv(
    PREDICTIONS_PATH,
    index=False
)


print(
    f"\n{PREDICTIONS_PATH}"
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n" + "=" * 70)
print(" SAVING MODEL")
print("=" * 70)


model.save_model(
    MODEL_PATH
)


print(
    f"\nModel saved:"
    f"\n{MODEL_PATH}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print(" TRAFFICX V14 COMPLETE")
print("=" * 70)

print(
    f"""
    
Model:
{MODEL_PATH}

Results:
{RESULTS_PATH}

Threshold analysis:
{THRESHOLD_PATH}

Feature importance:
{IMPORTANCE_PATH}

Scenario performance:
{SCENARIO_PATH}

Test predictions:
{PREDICTIONS_PATH}

Final metrics:

Threshold        : {OPERATING_THRESHOLD:.2f}
Accuracy         : {accuracy:.4f}
Precision        : {precision:.4f}
Risk Recall      : {recall:.4f}
F1               : {f1:.4f}
ROC-AUC          : {roc_auc:.4f}
PR-AUC           : {pr_auc:.4f}
False Alarm Rate : {false_alarm_rate:.4f}
Miss Rate        : {miss_rate:.4f}

"""
)

print("=" * 70)