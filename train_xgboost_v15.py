import os
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
    precision_recall_curve,
)

warnings.filterwarnings("ignore")


# ================================================================
# CONFIGURATION
# ================================================================

DATASET = r"D:\TRAFFICX\road_datasets\trafficx_ml_dataset_v2.csv"
MODEL_DIR = r"D:\TRAFFICX\models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_risk_escalation.json"
)

RESULTS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_results.csv"
)

THRESHOLD_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_thresholds.csv"
)

IMPORTANCE_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_feature_importance.csv"
)

SCENARIO_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_scenario_performance.csv"
)

PREDICTIONS_PATH = os.path.join(
    MODEL_DIR,
    "trafficx_xgboost_v15_test_predictions.csv"
)

os.makedirs(MODEL_DIR, exist_ok=True)


# ================================================================
# DISPLAY
# ================================================================

def banner(text):
    print()
    print("=" * 70)
    print(text)
    print("=" * 70)


# ================================================================
# LOAD DATA
# ================================================================

banner("TRAFFICX - XGBOOST V15")
print("RISK ESCALATION / TRAFFIC MOMENTUM")
print("TEMPORAL GENERALIZATION + SHORTCUT REMOVAL")

banner("LOADING V2 DATASET")

print(f"\nDataset:")
print(DATASET)

df = pd.read_csv(DATASET)

print(f"\nRows loaded    : {len(df):,}")
print(f"Columns loaded : {len(df.columns)}")


# ================================================================
# CREATE FUTURE RISK TARGET
# ================================================================

banner("CREATING FUTURE RISK TARGET")

df["future_risk"] = (
    df["future_congestion"].isin(["HIGH", "CONGESTED"])
).astype(np.int8)

print("\nFuture risk distribution:")
print(df["future_risk"].value_counts().sort_index())

print("\nFuture risk percentages:")
print(
    df["future_risk"]
    .value_counts(normalize=True)
    .sort_index()
    .mul(100)
    .round(3)
)


# ================================================================
# TEMPORAL ORDERING
# ================================================================

banner("TEMPORAL ORDERING")

df["step"] = pd.to_numeric(df["step"], errors="coerce")
df["road_id"] = df["road_id"].astype(str)

df = df.sort_values(
    ["scenario", "road_id", "step"]
).reset_index(drop=True)

print(f"\nMinimum step : {df['step'].min()}")
print(f"Maximum step : {df['step'].max()}")

unique_steps = np.sort(df["step"].unique())

print(f"Unique steps : {len(unique_steps)}")


# ================================================================
# CREATE V15 FEATURES
# ================================================================

banner("CREATING V15 RISK ESCALATION FEATURES")


# ----------------------------------------------------------------
# Base V14 features
# ----------------------------------------------------------------

BASE_FEATURES = [
    "vehicle_count",
    "average_speed_kmh",
    "stopped_vehicles",
    "average_waiting_time",
    "density_veh_per_km",
    "queue_length_estimate_m",
    "road_length_m",
    "vehicles_per_100m",
    "queue_ratio",
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
]


# ----------------------------------------------------------------
# V15 temporal lag features
#
# IMPORTANT:
# Shift is performed within scenario + road_id.
# This prevents information leaking between roads/scenarios.
# ----------------------------------------------------------------

GROUP = ["scenario", "road_id"]

g = df.groupby(GROUP, sort=False)


# Previous 2-step state
df["speed_lag2"] = g["average_speed_kmh"].shift(2)
df["vehicle_lag2"] = g["vehicle_count"].shift(2)
df["density_lag2"] = g["density_veh_per_km"].shift(2)
df["queue_lag2"] = g["queue_length_estimate_m"].shift(2)
df["stopped_lag2"] = g["stopped_vehicles"].shift(2)


# Previous 3-step state
df["speed_lag3"] = g["average_speed_kmh"].shift(3)
df["vehicle_lag3"] = g["vehicle_count"].shift(3)
df["density_lag3"] = g["density_veh_per_km"].shift(3)
df["queue_lag3"] = g["queue_length_estimate_m"].shift(3)
df["stopped_lag3"] = g["stopped_vehicles"].shift(3)


# ================================================================
# MULTI-STEP CHANGES
# ================================================================

banner("CREATING MULTI-STEP TRAFFIC MOMENTUM")


# 2-step changes
df["speed_change_2step"] = (
    df["average_speed_kmh"] - df["speed_lag2"]
)

df["vehicle_change_2step"] = (
    df["vehicle_count"] - df["vehicle_lag2"]
)

df["density_change_2step"] = (
    df["density_veh_per_km"] - df["density_lag2"]
)

df["queue_change_2step"] = (
    df["queue_length_estimate_m"] - df["queue_lag2"]
)

df["stopped_change_2step"] = (
    df["stopped_vehicles"] - df["stopped_lag2"]
)


# 3-step changes
df["speed_change_3step"] = (
    df["average_speed_kmh"] - df["speed_lag3"]
)

df["vehicle_change_3step"] = (
    df["vehicle_count"] - df["vehicle_lag3"]
)

df["density_change_3step"] = (
    df["density_veh_per_km"] - df["density_lag3"]
)

df["queue_change_3step"] = (
    df["queue_length_estimate_m"] - df["queue_lag3"]
)

df["stopped_change_3step"] = (
    df["stopped_vehicles"] - df["stopped_lag3"]
)


# ================================================================
# ESCALATION FEATURES
# ================================================================

banner("CREATING RISK ESCALATION FEATURES")


# Speed deterioration
df["speed_reduction_rate"] = (
    -df["speed_change_2step"]
)


# Density growth
df["density_growth_rate"] = (
    df["density_change_2step"]
)


# Queue growth
df["queue_growth_rate"] = (
    df["queue_change_2step"]
)


# Vehicle growth
df["vehicle_growth_rate"] = (
    df["vehicle_change_2step"]
)


# Stopped vehicle growth
df["stopped_growth_rate"] = (
    df["stopped_change_2step"]
)


# ================================================================
# SECOND-ORDER / ACCELERATION FEATURES
# ================================================================

df["speed_acceleration"] = (
    df["speed_change_kmh"]
    - (df["speed_lag2"] - df["speed_lag3"])
)

df["density_acceleration"] = (
    df["density_change"]
    - (df["density_lag2"] - df["density_lag3"])
)

df["queue_acceleration"] = (
    df["queue_change_m"]
    - (df["queue_lag2"] - df["queue_lag3"])
)

df["vehicle_acceleration"] = (
    df["vehicle_change"]
    - (df["vehicle_lag2"] - df["vehicle_lag3"])
)

df["stopped_acceleration"] = (
    (df["stopped_vehicles"] - df["stopped_lag2"])
    - (df["stopped_lag2"] - df["stopped_lag3"])
)


# ================================================================
# TRAFFIC PRESSURE
# ================================================================

df["traffic_pressure"] = (
    df["density_veh_per_km"]
    * (1.0 + df["stopped_vehicle_ratio"]
       if "stopped_vehicle_ratio" in df.columns
       else 1.0)
)


# ================================================================
# QUEUE / DENSITY PRESSURE
# ================================================================

df["queue_density_pressure"] = (
    df["queue_length_estimate_m"]
    * df["density_veh_per_km"]
)


# ================================================================
# SPEED-DENSITY INTERACTION
# ================================================================

df["speed_density_ratio"] = (
    df["density_veh_per_km"]
    / (df["average_speed_kmh"] + 1.0)
)


# ================================================================
# ESCALATION SCORE
# ================================================================

df["escalation_score"] = (
    np.maximum(df["density_growth_rate"], 0)
    + np.maximum(df["queue_growth_rate"], 0)
    + np.maximum(df["stopped_growth_rate"], 0)
    + np.maximum(df["speed_reduction_rate"], 0)
)


# ================================================================
# CLEAN NUMERIC VALUES
# ================================================================

V15_FEATURES = BASE_FEATURES + [

    # Multi-step state
    "speed_lag2",
    "vehicle_lag2",
    "density_lag2",
    "queue_lag2",
    "stopped_lag2",

    "speed_lag3",
    "vehicle_lag3",
    "density_lag3",
    "queue_lag3",
    "stopped_lag3",

    # Multi-step changes
    "speed_change_2step",
    "vehicle_change_2step",
    "density_change_2step",
    "queue_change_2step",
    "stopped_change_2step",

    "speed_change_3step",
    "vehicle_change_3step",
    "density_change_3step",
    "queue_change_3step",
    "stopped_change_3step",

    # Escalation
    "speed_reduction_rate",
    "density_growth_rate",
    "queue_growth_rate",
    "vehicle_growth_rate",
    "stopped_growth_rate",

    # Acceleration
    "speed_acceleration",
    "density_acceleration",
    "queue_acceleration",
    "vehicle_acceleration",
    "stopped_acceleration",

    # Interaction features
    "traffic_pressure",
    "queue_density_pressure",
    "speed_density_ratio",

    # Composite
    "escalation_score",
]


print("\nV15 FEATURES")
print("=" * 70)

for i, feature in enumerate(V15_FEATURES, 1):
    print(f"{i:02d}. {feature}")

print(f"\nTotal features: {len(V15_FEATURES)}")


# ================================================================
# HANDLE INF / NAN
# ================================================================

df[V15_FEATURES] = (
    df[V15_FEATURES]
    .replace([np.inf, -np.inf], np.nan)
    .fillna(0.0)
)


# ================================================================
# TEMPORAL SPLIT
# ================================================================

banner("TEMPORAL TRAIN / VALIDATION / TEST SPLIT")

n_steps = len(unique_steps)

train_end = int(n_steps * 0.70)
val_end = int(n_steps * 0.85)

train_steps = unique_steps[:train_end]
val_steps = unique_steps[train_end:val_end]
test_steps = unique_steps[val_end:]

train_start = train_steps[0]
train_last = train_steps[-1]

val_start = val_steps[0]
val_last = val_steps[-1]

test_start = test_steps[0]
test_last = test_steps[-1]

print("\nTRAIN")
print(f"Steps: {train_start} -> {train_last}")

print("\nVALIDATION")
print(f"Steps: {val_start} -> {val_last}")

print("\nTEST")
print(f"Steps: {test_start} -> {test_last}")


train_mask = df["step"].isin(train_steps)
val_mask = df["step"].isin(val_steps)
test_mask = df["step"].isin(test_steps)

train_df = df.loc[train_mask]
val_df = df.loc[val_mask]
test_df = df.loc[test_mask]

print("\nRows:")
print(f"TRAIN      : {len(train_df):,}")
print(f"VALIDATION : {len(val_df):,}")
print(f"TEST       : {len(test_df):,}")


# ================================================================
# TARGET DISTRIBUTION
# ================================================================

banner("TARGET DISTRIBUTION BY SPLIT")

for name, subset in [
    ("TRAIN", train_df),
    ("VALIDATION", val_df),
    ("TEST", test_df),
]:

    counts = subset["future_risk"].value_counts().sort_index()

    nonrisk = int(counts.get(0, 0))
    risk = int(counts.get(1, 0))
    total = len(subset)

    print(f"\n{name}")
    print(
        f"NON-RISK : {nonrisk:,} "
        f"({nonrisk / total * 100:.3f}%)"
    )
    print(
        f"RISK     : {risk:,} "
        f"({risk / total * 100:.3f}%)"
    )


# ================================================================
# X / Y
# ================================================================

X_train = train_df[V15_FEATURES]
y_train = train_df["future_risk"]

X_val = val_df[V15_FEATURES]
y_val = val_df["future_risk"]

X_test = test_df[V15_FEATURES]
y_test = test_df["future_risk"]


# ================================================================
# CLASS IMBALANCE
# ================================================================

banner("CLASS IMBALANCE")

negative = int((y_train == 0).sum())
positive = int((y_train == 1).sum())

scale_pos_weight = negative / positive

print(f"\nNON-RISK : {negative:,}")
print(f"RISK     : {positive:,}")
print(f"\nscale_pos_weight : {scale_pos_weight:.4f}")


# ================================================================
# TRAIN XGBOOST
# ================================================================

banner("TRAINING XGBOOST V15")

model = xgb.XGBClassifier(
    n_estimators=800,

    max_depth=7,

    learning_rate=0.05,

    min_child_weight=5,

    subsample=0.85,

    colsample_bytree=0.85,

    gamma=0.05,

    reg_alpha=0.05,

    reg_lambda=1.5,

    objective="binary:logistic",

    eval_metric="aucpr",

    scale_pos_weight=scale_pos_weight,

    tree_method="hist",

    random_state=42,

    n_jobs=-1,
)


model.fit(
    X_train,
    y_train,

    eval_set=[
        (X_train, y_train),
        (X_val, y_val),
    ],

    verbose=50,
)


print("\nTraining complete.")


# ================================================================
# VALIDATION PROBABILITIES
# ================================================================

banner("VALIDATION PROBABILITIES")

val_prob = model.predict_proba(X_val)[:, 1]

val_roc = roc_auc_score(
    y_val,
    val_prob
)

val_pr = average_precision_score(
    y_val,
    val_prob
)

print(f"\nValidation ROC-AUC : {val_roc:.4f}")
print(f"Validation PR-AUC  : {val_pr:.4f}")


# ================================================================
# THRESHOLD OPTIMIZATION
# ================================================================

banner("THRESHOLD OPTIMIZATION")

precision, recall, thresholds = precision_recall_curve(
    y_val,
    val_prob
)

threshold_rows = []

best_threshold = 0.89
best_f1 = -1

for threshold in np.arange(0.10, 0.991, 0.01):

    pred = (val_prob >= threshold).astype(int)

    p = precision_score(
        y_val,
        pred,
        zero_division=0
    )

    r = recall_score(
        y_val,
        pred,
        zero_division=0
    )

    f1 = f1_score(
        y_val,
        pred,
        zero_division=0
    )

    cm = confusion_matrix(
        y_val,
        pred,
        labels=[0, 1]
    )

    tn, fp, fn, tp = cm.ravel()

    far = fp / (fp + tn) if (fp + tn) else 0

    threshold_rows.append({
        "threshold": threshold,
        "precision": p,
        "recall": r,
        "f1": f1,
        "false_alarm_rate": far,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    })

    # Prefer F1, but require reasonable precision
    if p >= 0.60 and f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold


threshold_df = pd.DataFrame(threshold_rows)

threshold_df.to_csv(
    THRESHOLD_PATH,
    index=False
)

print(
    f"\nSelected threshold: "
    f"{best_threshold:.2f}"
)

selected = threshold_df[
    threshold_df["threshold"] == best_threshold
].iloc[0]

print(
    f"Validation precision : "
    f"{selected['precision']:.4f}"
)

print(
    f"Validation recall    : "
    f"{selected['recall']:.4f}"
)

print(
    f"Validation F1        : "
    f"{selected['f1']:.4f}"
)

print(
    f"False alarm rate     : "
    f"{selected['false_alarm_rate']:.4f}"
)

print(f"\nThreshold results saved:")
print(THRESHOLD_PATH)


# ================================================================
# FINAL TEST
# ================================================================

banner("FINAL TEST EVALUATION")

test_prob = model.predict_proba(X_test)[:, 1]

test_pred = (
    test_prob >= best_threshold
).astype(int)


# ================================================================
# METRICS
# ================================================================

accuracy = accuracy_score(
    y_test,
    test_pred
)

precision_val = precision_score(
    y_test,
    test_pred,
    zero_division=0
)

recall_val = recall_score(
    y_test,
    test_pred,
    zero_division=0
)

f1_val = f1_score(
    y_test,
    test_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    test_prob
)

pr_auc = average_precision_score(
    y_test,
    test_prob
)


cm = confusion_matrix(
    y_test,
    test_pred,
    labels=[0, 1]
)

tn, fp, fn, tp = cm.ravel()

false_alarm_rate = (
    fp / (fp + tn)
    if (fp + tn) > 0
    else 0
)

miss_rate = (
    fn / (fn + tp)
    if (fn + tp) > 0
    else 0
)


banner("V15 TEST RESULTS")

print(f"\nThreshold         : {best_threshold:.2f}")
print(f"Accuracy          : {accuracy:.4f}")
print(f"Precision         : {precision_val:.4f}")
print(f"Risk Recall       : {recall_val:.4f}")
print(f"F1 Score          : {f1_val:.4f}")
print(f"ROC-AUC           : {roc_auc:.4f}")
print(f"PR-AUC            : {pr_auc:.4f}")
print(f"False Alarm Rate  : {false_alarm_rate:.4f}")
print(f"Miss Rate         : {miss_rate:.4f}")


# ================================================================
# CONFUSION MATRIX
# ================================================================

print("\nConfusion Matrix:")
print()
print("                 Predicted")
print("              NON-RISK   RISK")
print(
    f"Actual NON-RISK {tn:9,} {fp:9,}"
)
print(
    f"Actual RISK     {fn:9,} {tp:9,}"
)


# ================================================================
# CLASSIFICATION REPORT
# ================================================================

banner("CLASSIFICATION REPORT")

print(
    classification_report(
        y_test,
        test_pred,
        target_names=[
            "NON_RISK",
            "RISK"
        ],
        digits=4,
        zero_division=0,
    )
)


# ================================================================
# FEATURE IMPORTANCE
# ================================================================

banner("FEATURE IMPORTANCE")

importance = pd.DataFrame({
    "feature": V15_FEATURES,
    "importance": model.feature_importances_,
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print(
    importance.to_string(
        index=False,
        formatters={
            "importance": "{:.6f}".format
        }
    )
)

importance.to_csv(
    IMPORTANCE_PATH,
    index=False
)


# ================================================================
# SCENARIO-WISE PERFORMANCE
# ================================================================

banner("SCENARIO-WISE PERFORMANCE")

scenario_rows = []

for scenario in sorted(
    test_df["scenario"].unique()
):

    mask = (
        test_df["scenario"].values
        == scenario
    )

    y_s = y_test.values[mask]
    p_s = test_prob[mask]
    pred_s = test_pred[mask]

    if len(np.unique(y_s)) > 1:
        scenario_roc = roc_auc_score(
            y_s,
            p_s
        )

        scenario_pr = average_precision_score(
            y_s,
            p_s
        )
    else:
        scenario_roc = np.nan
        scenario_pr = np.nan

    cm_s = confusion_matrix(
        y_s,
        pred_s,
        labels=[0, 1]
    )

    tn_s, fp_s, fn_s, tp_s = cm_s.ravel()

    far_s = (
        fp_s / (fp_s + tn_s)
        if (fp_s + tn_s) > 0
        else 0
    )

    scenario_rows.append({
        "scenario": scenario,
        "samples": len(y_s),
        "risk_samples": int(y_s.sum()),

        "accuracy": accuracy_score(
            y_s,
            pred_s
        ),

        "precision": precision_score(
            y_s,
            pred_s,
            zero_division=0
        ),

        "recall": recall_score(
            y_s,
            pred_s,
            zero_division=0
        ),

        "f1": f1_score(
            y_s,
            pred_s,
            zero_division=0
        ),

        "roc_auc": scenario_roc,
        "pr_auc": scenario_pr,

        "false_alarm_rate": far_s,

        "true_positive": tp_s,
        "false_positive": fp_s,
        "true_negative": tn_s,
        "false_negative": fn_s,
    })


scenario_df = pd.DataFrame(
    scenario_rows
)

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


# ================================================================
# SAVE TEST PREDICTIONS
# ================================================================

banner("SAVING TEST PREDICTIONS")

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
] = test_prob

prediction_output[
    "predicted_risk"
] = test_pred

prediction_output[
    "threshold"
] = best_threshold

prediction_output.to_csv(
    PREDICTIONS_PATH,
    index=False
)

print(PREDICTIONS_PATH)


# ================================================================
# SAVE MODEL
# ================================================================

banner("SAVING MODEL")

model.save_model(
    MODEL_PATH
)

print(f"\nModel saved:")
print(MODEL_PATH)


# ================================================================
# SAVE RESULTS
# ================================================================

results = pd.DataFrame([
    {
        "model": "TRAFFICX XGBoost V15",
        "threshold": best_threshold,
        "accuracy": accuracy,
        "precision": precision_val,
        "risk_recall": recall_val,
        "f1": f1_val,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "false_alarm_rate": false_alarm_rate,
        "miss_rate": miss_rate,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
        "test_rows": len(test_df),
        "features": len(V15_FEATURES),
    }
])

results.to_csv(
    RESULTS_PATH,
    index=False
)


# ================================================================
# FINAL
# ================================================================

banner("TRAFFICX V15 COMPLETE")

print(f"\nModel:")
print(MODEL_PATH)

print(f"\nResults:")
print(RESULTS_PATH)

print(f"\nThreshold analysis:")
print(THRESHOLD_PATH)

print(f"\nFeature importance:")
print(IMPORTANCE_PATH)

print(f"\nScenario performance:")
print(SCENARIO_PATH)

print(f"\nTest predictions:")
print(PREDICTIONS_PATH)

print("\nFinal metrics:")
print(
    f"  Threshold        : {best_threshold:.2f}"
)
print(
    f"  Precision        : {precision_val:.4f}"
)
print(
    f"  Risk Recall      : {recall_val:.4f}"
)
print(
    f"  F1               : {f1_val:.4f}"
)
print(
    f"  ROC-AUC          : {roc_auc:.4f}"
)
print(
    f"  PR-AUC           : {pr_auc:.4f}"
)
print(
    f"  False Alarm Rate : {false_alarm_rate:.4f}"
)
print(
    f"  Miss Rate        : {miss_rate:.4f}"
)

print()
print("=" * 70)