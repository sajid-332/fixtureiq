import pandas as pd


file_path = "data/historical/processed/epl_features.csv"

df = pd.read_csv(file_path)


feature_columns = [
    "HomeLast5Points",
    "AwayLast5Points",
    "Last5HomePoints",
    "Last5AwayPoints"
]

required_columns = [
    "Date",
    "Season",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR"
]


# Check total matches
assert len(df) == 1900, "Expected 1900 matches"


# Check required columns
for column in required_columns:
    assert column in df.columns, f"Missing column: {column}"


# Check duplicate rows
assert df.duplicated().sum() == 0, "Duplicate rows found"


# Important match data should not be missing
assert df[required_columns].isnull().sum().sum() == 0, \
    "Missing required match data found"


# Only valid match results
assert set(df["FTR"]).issubset({"H", "D", "A"}), \
    "Invalid FTR value found"


# Feature values must be between 0 and 15
for column in feature_columns:

    values = df[column].dropna()

    assert values.between(0, 15).all(), \
        f"Invalid value found in {column}"


print("Feature dataset validation passed!")

print("\nTotal matches:", len(df))

print("\nMissing feature values:")
print(df[feature_columns].isnull().sum())

print("\nFeature ranges:")

for column in feature_columns:

    print(
        f"{column}:",
        "Min =", df[column].min(),
        "Max =", df[column].max()
    )