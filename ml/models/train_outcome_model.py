import pandas as pd


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