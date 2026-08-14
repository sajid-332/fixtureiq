import pandas as pd

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

# Basic checks
assert len(df) == 1900, "Expected 1900 matches"
assert df.isnull().sum().sum() == 0, "Missing values found"
assert df.duplicated().sum() == 0, "Duplicate rows found"

# Check valid results
valid_results = {"H", "D", "A"}
assert set(df["FTR"]).issubset(valid_results), "Invalid FTR value found"

# Check result matches the goals
for _, row in df.iterrows():

    if row["FTHG"] > row["FTAG"]:
        expected = "H"
    elif row["FTHG"] < row["FTAG"]:
        expected = "A"
    else:
        expected = "D"

    assert row["FTR"] == expected, "Result does not match score"

print("Historical dataset validation passed!")
print("Total matches:", len(df))
print("Seasons:", df["Season"].nunique())
print("Unique teams:", len(set(df["HomeTeam"]) | set(df["AwayTeam"])))