import glob
import pandas as pd

# List of names to replace with "Salve"
name_replacements = {
    name: "Salve"
    for name in [
        "Ray, Andrew",
        "LaRose, Jack",
        "Houchens, Sam",
        "Turner, Tommy",
        "Kent, Zayden",
        "Morris, Zach",
        "Aikens, Parker",
    ]
}

# Find CSV file for 10/10/2026
file_paths = glob.glob("data/Fall26/20261010*.csv")

for file_path in file_paths:
    df = pd.read_csv(file_path)

    if "Pitcher" in df.columns:
        df["Pitcher"] = df["Pitcher"].replace(name_replacements)

        df.to_csv(file_path, index=False)
