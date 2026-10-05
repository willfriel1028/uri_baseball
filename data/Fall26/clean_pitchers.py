# Bradshaw, Michael
# Maloney, Colin
# Modifica, Mateo
# Morris, Zach

import glob
import pandas as pd

name_replacements = {
    "Maloney, Colin": "Bradshaw, Michael",
    "Morris, Zach": "Modifica, Mateo",
}

# Find all matching CSV files in the directory
file_paths = glob.glob("data/Fall26/*.csv")

for file_path in file_paths:
    # Read the individual CSV file
    df = pd.read_csv(file_path)

    # Replace values in the 'Pitcher' column if it exists
    if "Pitcher" in df.columns:
        df["Pitcher"] = df["Pitcher"].replace(name_replacements)

        # Overwrite the original file
        df.to_csv(file_path, index=False)