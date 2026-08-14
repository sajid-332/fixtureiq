import pandas as pd

file_path = "data/historical/processed/epl_historical.csv"

df = pd.read_csv(file_path)

print("Shape:")
print(df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nLast 5 rows:")
print(df.tail())

print("\nSeason counts:")
print(df["Season"].value_counts().sort_index())

print("\nMissing values:")
print(df.isnull().sum())