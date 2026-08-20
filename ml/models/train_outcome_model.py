import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    confusion_matrix,
    classification_report,
    recall_score,
    f1_score
)

# ================================================================
# LOAD STAGE 4 DATASET
# ================================================================

file_path = "data/historical/processed/epl_stage4_features.csv"

df = pd.read_csv(file_path)

df["Date"] = pd.to_datetime(df["Date"])


print("Dataset loaded successfully!")
print("Total matches:", len(df))
print("Total columns:", len(df.columns))


# ================================================================
# CHECK AVAILABLE SEASONS
# ================================================================

print("\nSeasons:")

print(
    df["Season"]
    .value_counts()
    .sort_index()
)


# ================================================================
# CHRONOLOGICAL SPLIT
# ================================================================

train_seasons = [
    "2021/22",
    "2022/23",
    "2023/24"
]

validation_season = "2024/25"

test_season = "2025/26"


train_df = df[
    df["Season"].isin(train_seasons)
].copy()


validation_df = df[
    df["Season"] == validation_season
].copy()


test_df = df[
    df["Season"] == test_season
].copy()


# ================================================================
# SORT EACH SPLIT BY DATE
# ================================================================

train_df = train_df.sort_values(
    "Date"
).reset_index(drop=True)


validation_df = validation_df.sort_values(
    "Date"
).reset_index(drop=True)


test_df = test_df.sort_values(
    "Date"
).reset_index(drop=True)


# ================================================================
# DISPLAY SPLIT INFORMATION
# ================================================================

print("\nChronological split:")

print(
    "Train matches:",
    len(train_df)
)

print(
    "Validation matches:",
    len(validation_df)
)

print(
    "Test matches:",
    len(test_df)
)


print("\nTrain period:")
print(
    train_df["Date"].min(),
    "→",
    train_df["Date"].max()
)


print("\nValidation period:")
print(
    validation_df["Date"].min(),
    "→",
    validation_df["Date"].max()
)


print("\nTest period:")
print(
    test_df["Date"].min(),
    "→",
    test_df["Date"].max()
)

# ================================================================
# BASELINE MODEL
# ================================================================

print("\nBaseline results:")


# ------------------------------------------------
# BASELINE 1: ALWAYS PREDICT HOME WIN
# ------------------------------------------------

home_baseline_predictions = ["H"] * len(validation_df)

home_baseline_accuracy = (
    validation_df["FTR"]
    ==
    home_baseline_predictions
).mean()

print(
    "Always Home Win accuracy:",
    round(home_baseline_accuracy, 4)
)


# ------------------------------------------------
# BASELINE 2: MOST COMMON TRAINING RESULT
# ------------------------------------------------

most_common_result = (
    train_df["FTR"]
    .value_counts()
    .idxmax()
)

print(
    "Most common training result:",
    most_common_result
)


common_baseline_predictions = (
    [most_common_result]
    * len(validation_df)
)

common_baseline_accuracy = (
    validation_df["FTR"]
    ==
    common_baseline_predictions
).mean()

print(
    "Most common result accuracy:",
    round(common_baseline_accuracy, 4)
)

# ================================================================
# SELECT MODEL FEATURES
# ================================================================

feature_columns = [

    # Recent form
    "HomeLast5Points",
    "AwayLast5Points",
    "Last5HomePoints",
    "Last5AwayPoints",

    # League situation
    "LeaguePointsGap",
    "GamesPlayedGap",
    "HomePositionBefore",
    "AwayPositionBefore",

    # Head-to-head
    "HomeH2HLast5Points",
    "AwayH2HLast5Points",
    "H2HMatchesUsed",

    # Season + recent performance
    "HomeSeasonPPG",
    "AwaySeasonPPG",
    "HomeRecentPPG",
    "AwayRecentPPG",

    # Momentum
    "HomeMomentum",
    "AwayMomentum",

    # Upset signal
    "UpsetPotential",
    "UpsetDirection",

    # League pressure
    "HomeTitlePressure",
    "AwayTitlePressure",

    "HomeTop4Pressure",
    "AwayTop4Pressure",

    "HomeRelegationPressure",
    "AwayRelegationPressure"
]


print("\nSelected features:")
print("Total features:", len(feature_columns))


for feature in feature_columns:
    print("-", feature)

# ================================================================
# CHECK MISSING VALUES
# ================================================================

print("\nTraining missing values:")

print(
    train_df[
        feature_columns
    ]
    .isnull()
    .sum()
)

# ================================================================
# CREATE X AND y
# ================================================================

X_train = train_df[feature_columns]
y_train = train_df["FTR"]

X_validation = validation_df[feature_columns]
y_validation = validation_df["FTR"]

X_test = test_df[feature_columns]
y_test = test_df["FTR"]


print("\nML dataset shapes:")

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)

print("X_validation:", X_validation.shape)
print("y_validation:", y_validation.shape)

print("X_test:", X_test.shape)
print("y_test:", y_test.shape)

# ================================================================
# BUILD ML PIPELINE
# ================================================================

model = Pipeline([
    (
        "imputer",
        SimpleImputer(
            strategy="median",
            add_indicator=True
        )
    ),

    (
        "scaler",
        StandardScaler()
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=2000
        )
    )
])


print("\nML pipeline created successfully!")

# ================================================================
# TRAIN MODEL
# ================================================================

print("\nTraining Logistic Regression model...")

model.fit(
    X_train,
    y_train
)

print("Model training completed successfully!")

# ================================================================
# VALIDATION PREDICTIONS
# ================================================================

print("\nEvaluating on validation season...")


# Final predicted class: H / D / A
validation_predictions = model.predict(
    X_validation
)


# Probabilities for H / D / A
validation_probabilities = model.predict_proba(
    X_validation
)


# ================================================================
# VALIDATION ACCURACY
# ================================================================

validation_accuracy = accuracy_score(
    y_validation,
    validation_predictions
)


print(
    "Validation accuracy:",
    round(validation_accuracy, 4)
)


print(
    "Validation accuracy (%):",
    round(validation_accuracy * 100, 2)
)


# ================================================================
# VALIDATION LOG LOSS
# ================================================================

validation_log_loss = log_loss(
    y_validation,
    validation_probabilities,
    labels=model.classes_
)


print(
    "Validation log loss:",
    round(validation_log_loss, 4)
)

# ================================================================
# CLASS-BY-CLASS EVALUATION
# ================================================================

print("\nConfusion Matrix:")

labels = ["H", "D", "A"]

matrix = confusion_matrix(
    y_validation,
    validation_predictions,
    labels=labels
)

confusion_df = pd.DataFrame(
    matrix,
    index=[
        "Actual H",
        "Actual D",
        "Actual A"
    ],
    columns=[
        "Predicted H",
        "Predicted D",
        "Predicted A"
    ]
)

print(confusion_df)


print("\nClassification Report:")

print(
    classification_report(
        y_validation,
        validation_predictions,
        labels=labels,
        target_names=[
            "Home Win",
            "Draw",
            "Away Win"
        ],
        digits=3
    )
)

# ================================================================
# COMPARE WITH BASELINE
# ================================================================

improvement = (
    validation_accuracy
    - home_baseline_accuracy
)


print(
    "\nBaseline accuracy (%):",
    round(home_baseline_accuracy * 100, 2)
)


print(
    "Logistic Regression accuracy (%):",
    round(validation_accuracy * 100, 2)
)


print(
    "Accuracy improvement:",
    round(improvement * 100, 2),
    "percentage points"
)

# ================================================================
# BALANCED LOGISTIC REGRESSION EXPERIMENT
# ================================================================

print("\n" + "=" * 60)
print("BALANCED LOGISTIC REGRESSION")
print("=" * 60)


balanced_model = Pipeline([
    (
        "imputer",
        SimpleImputer(
            strategy="median",
            add_indicator=True
        )
    ),

    (
        "scaler",
        StandardScaler()
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced"
        )
    )
])


# ================================================================
# TRAIN BALANCED MODEL
# ================================================================

balanced_model.fit(
    X_train,
    y_train
)


# ================================================================
# VALIDATION PREDICTIONS
# ================================================================

balanced_predictions = balanced_model.predict(
    X_validation
)


balanced_probabilities = balanced_model.predict_proba(
    X_validation
)


# ================================================================
# ACCURACY
# ================================================================

balanced_accuracy = accuracy_score(
    y_validation,
    balanced_predictions
)


print(
    "\nBalanced validation accuracy (%):",
    round(balanced_accuracy * 100, 2)
)


# ================================================================
# LOG LOSS
# ================================================================

balanced_log_loss = log_loss(
    y_validation,
    balanced_probabilities,
    labels=balanced_model.classes_
)


print(
    "Balanced validation log loss:",
    round(balanced_log_loss, 4)
)


# ================================================================
# CONFUSION MATRIX
# ================================================================

balanced_matrix = confusion_matrix(
    y_validation,
    balanced_predictions,
    labels=["H", "D", "A"]
)


balanced_confusion_df = pd.DataFrame(
    balanced_matrix,
    index=[
        "Actual H",
        "Actual D",
        "Actual A"
    ],
    columns=[
        "Predicted H",
        "Predicted D",
        "Predicted A"
    ]
)


print("\nBalanced Confusion Matrix:")

print(
    balanced_confusion_df
)


# ================================================================
# CLASSIFICATION REPORT
# ================================================================

print("\nBalanced Classification Report:")


print(
    classification_report(
        y_validation,
        balanced_predictions,
        labels=["H", "D", "A"],
        target_names=[
            "Home Win",
            "Draw",
            "Away Win"
        ],
        digits=3
    )
)


# ================================================================
# COMPARE BOTH MODELS
# ================================================================

print("\nModel comparison:")

print(
    "Normal accuracy (%):",
    round(validation_accuracy * 100, 2)
)

print(
    "Balanced accuracy (%):",
    round(balanced_accuracy * 100, 2)
)


print(
    "Normal log loss:",
    round(validation_log_loss, 4)
)

print(
    "Balanced log loss:",
    round(balanced_log_loss, 4)
)

# ================================================================
# DRAW WEIGHT TUNING
# ================================================================

print("\n" + "=" * 60)
print("DRAW WEIGHT TUNING")
print("=" * 60)


draw_weights = [
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0
]


tuning_results = []


for draw_weight in draw_weights:

    tuned_model = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="median",
                add_indicator=True
            )
        ),

        (
            "scaler",
            StandardScaler()
        ),

        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight={
                    "H": 1.0,
                    "D": draw_weight,
                    "A": 1.0
                }
            )
        )
    ])


    # Train using training seasons only
    tuned_model.fit(
        X_train,
        y_train
    )


    # Predict validation season
    tuned_predictions = tuned_model.predict(
        X_validation
    )

    tuned_probabilities = tuned_model.predict_proba(
        X_validation
    )


    # ------------------------------------------------------------
    # ACCURACY
    # ------------------------------------------------------------

    accuracy = accuracy_score(
        y_validation,
        tuned_predictions
    )


    # ------------------------------------------------------------
    # LOG LOSS
    # ------------------------------------------------------------

    loss = log_loss(
        y_validation,
        tuned_probabilities,
        labels=tuned_model.classes_
    )


    # ------------------------------------------------------------
    # DRAW RECALL
    # ------------------------------------------------------------

    recalls = recall_score(
        y_validation,
        tuned_predictions,
        labels=["H", "D", "A"],
        average=None
    )

    draw_recall = recalls[1]


    # ------------------------------------------------------------
    # MACRO F1
    # ------------------------------------------------------------

    macro_f1 = f1_score(
        y_validation,
        tuned_predictions,
        labels=["H", "D", "A"],
        average="macro"
    )


    tuning_results.append({

        "DrawWeight":
            draw_weight,

        "Accuracy":
            accuracy,

        "LogLoss":
            loss,

        "DrawRecall":
            draw_recall,

        "MacroF1":
            macro_f1
    })


# ================================================================
# DISPLAY RESULTS
# ================================================================

tuning_df = pd.DataFrame(
    tuning_results
)


print("\nValidation tuning results:")

print(
    tuning_df.to_string(
        index=False,
        formatters={

            "Accuracy":
                lambda x: f"{x * 100:.2f}%",

            "LogLoss":
                lambda x: f"{x:.4f}",

            "DrawRecall":
                lambda x: f"{x * 100:.2f}%",

            "MacroF1":
                lambda x: f"{x:.3f}"
        }
    )
)


# ================================================================
# BEST MODEL BY VALIDATION LOG LOSS
# ================================================================

best_index = (
    tuning_df["LogLoss"]
    .idxmin()
)


best_result = tuning_df.loc[
    best_index
]


print("\nBest Draw Weight by Log Loss:")

print(
    "Draw weight:",
    best_result["DrawWeight"]
)

print(
    "Accuracy (%):",
    round(
        best_result["Accuracy"] * 100,
        2
    )
)

print(
    "Log Loss:",
    round(
        best_result["LogLoss"],
        4
    )
)

print(
    "Draw Recall (%):",
    round(
        best_result["DrawRecall"] * 100,
        2
    )
)

print(
    "Macro F1:",
    round(
        best_result["MacroF1"],
        3
    )
)

# ================================================================
# PROBABILITY BASELINE
# ================================================================

print("\n" + "=" * 60)
print("PROBABILITY BASELINE")
print("=" * 60)


# Result proportions from TRAINING data only
train_result_probabilities = (
    y_train
    .value_counts(normalize=True)
)


home_probability = train_result_probabilities["H"]
draw_probability = train_result_probabilities["D"]
away_probability = train_result_probabilities["A"]


print("\nTraining result probabilities:")

print(
    "Home Win:",
    round(home_probability * 100, 2),
    "%"
)

print(
    "Draw:",
    round(draw_probability * 100, 2),
    "%"
)

print(
    "Away Win:",
    round(away_probability * 100, 2),
    "%"
)


# Same naive probabilities for every validation match
baseline_probabilities = np.tile(
    [
        away_probability,
        draw_probability,
        home_probability
    ],
    (
        len(y_validation),
        1
    )
)


# model.classes_ is expected to be:
# ['A', 'D', 'H']

probability_baseline_log_loss = log_loss(
    y_validation,
    baseline_probabilities,
    labels=["A", "D", "H"]
)


print(
    "\nProbability baseline log loss:",
    round(
        probability_baseline_log_loss,
        4
    )
)


print(
    "Normal Logistic Regression log loss:",
    round(
        validation_log_loss,
        4
    )
)


print(
    "Draw weight 1.2 log loss:",
    round(
        best_result["LogLoss"],
        4
    )
)