import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


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