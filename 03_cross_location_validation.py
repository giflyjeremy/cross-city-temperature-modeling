"""
=====================================================================
CROSS-LOCATION MODEL GENERALIZATION TESTING
Random Forest vs. simple regression, evaluated with leave-one-
location-out cross-validation and a bias/dynamics-decomposed R2
=====================================================================

A reusable pattern for testing whether a spatial prediction model
generalizes to locations it has never seen, rather than only
performing well within the locations used for training. This is a
stricter and more policy-relevant test than a random train/test
split when the eventual use case is applying the model somewhere new.

Includes a diagnostic metric (anomaly-based R2) that separates two
distinct failure modes that standard R2 conflates:
  - the model gets a new location's average level wrong; vs.
  - the model gets the *pattern of change over time* wrong.
This distinction changed the interpretation of the original results
this pipeline was built for, so it is kept here as a reusable
component rather than a one-off calculation.

Adapt INPUT_PATH, FEATURE_SETS, and TARGET_COLUMNS for your own
prediction problem.
=====================================================================
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import pearsonr

INPUT_PATH = "output/merged_lst_ta.csv"
LOCATION_COLUMN = "city"

FEATURE_SETS = {
    "day": ["lst_day_c", "ndvi", "ndbi", "relative_humidity_day", "wind_speed_day", "month"],
    "night": ["lst_night_c", "ndvi", "relative_humidity_night", "wind_speed_night"],
}
BASELINE_FEATURE = {"day": "lst_day_c", "night": "lst_night_c"}
TARGET_COLUMNS = {"day": "ta_day_c", "night": "ta_night_c"}

RF_PARAMS = dict(n_estimators=300, max_depth=6, min_samples_leaf=10,
                  random_state=42, n_jobs=-1)


def leave_one_location_out(df, features, target, model_builder):
    """Train on all locations but one, test on the held-out location,
    repeated for every location. Returns per-location and pooled
    metrics, including the anomaly-based R2 diagnostic."""
    results = []
    for held_out in sorted(df[LOCATION_COLUMN].unique()):
        train = df[df[LOCATION_COLUMN] != held_out]
        test = df[df[LOCATION_COLUMN] == held_out]

        model = model_builder()
        model.fit(train[features], train[target])
        prediction = model.predict(test[features])

        observed = test[target].values
        mae = mean_absolute_error(observed, prediction)
        r2 = r2_score(observed, prediction)
        r, _ = pearsonr(observed, prediction)

        observed_anomaly = observed - observed.mean()
        prediction_anomaly = prediction - prediction.mean()
        r2_anomaly = r2_score(observed_anomaly, prediction_anomaly)
        baseline_bias = prediction.mean() - observed.mean()

        results.append({
            "held_out_location": held_out, "n": len(test),
            "mae": round(mae, 3), "r2": round(r2, 3), "r": round(r, 3),
            "r2_anomaly": round(r2_anomaly, 3),
            "baseline_bias": round(baseline_bias, 3),
        })
    return pd.DataFrame(results)


def compare_model_vs_baseline(df, period_label):
    features = FEATURE_SETS[period_label]
    baseline_feature = [BASELINE_FEATURE[period_label]]
    target = TARGET_COLUMNS[period_label]

    rf_results = leave_one_location_out(
        df, features, target,
        lambda: RandomForestRegressor(**RF_PARAMS)
    )
    baseline_results = leave_one_location_out(
        df, baseline_feature, target,
        lambda: LinearRegression()
    )

    print(f"\n=== {period_label.upper()} MODEL: leave-one-location-out ===")
    print("\nMultivariate model (mean across held-out locations):")
    print(rf_results[["mae", "r2", "r", "r2_anomaly"]].mean().round(3))
    print("\nSingle-feature baseline (mean across held-out locations):")
    print(baseline_results[["mae", "r2", "r"]].mean().round(3))

    return rf_results, baseline_results


if __name__ == "__main__":
    data = pd.read_csv(INPUT_PATH)
    for period in ["day", "night"]:
        compare_model_vs_baseline(data, period)
