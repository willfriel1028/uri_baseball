import glob
import pandas as pd

file_paths = glob.glob("data/Fall26/*.csv")

for file_path in file_paths:
    df = pd.read_csv(file_path)

    if "Pitcher" in df.columns:
        df_duplicate = df[df["Pitcher"] != "Salve"].copy()

        df_duplicate["Pitcher"] = "URI"

        df_combined = (
            pd.concat([df, df_duplicate])
            .sort_index(kind="merge")
            .reset_index(drop=True)
        )

        df_combined.to_csv(file_path, index=False)
