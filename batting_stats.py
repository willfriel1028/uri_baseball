import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st

df = pd.read_csv("data/Fall25Scrim(updated).csv")

st.set_page_config(layout="wide")

def uri_batters_report(df):
    
    names = list(df["Batter"].unique())
    names.remove("Creed, Will")
    names.remove("Houchens, Sam")
    names.remove("Aikens, Parker")
        
    dfs = []
    
    pitches = list(df["TaggedPitchType"].unique())
    
    for name in names:
        
        dfn = df[df["Batter"] == name]
        df_batter = batters_stats_report(dfn, pitches)
        dfs.append(df_batter)
        
    final_df = pd.DataFrame(dfs).reset_index(drop=True)
    
    final_df = move_column(final_df, "K", 7)
    final_df = move_column(final_df, "SLG", 10)
    final_df = move_column(final_df, "OPS", 11)
    final_df = move_column(final_df, "RBI", 5)
        
    #final_df.to_csv(csv + "_batters_report.csv")
    
    return final_df
        
    
def batters_stats_report(df, pitches):    
        
    dfx = {}
            
    strikes = (
        ((df["PlateLocHeight"] >= 1.65) & (df["PlateLocHeight"] <= 3.65)) & 
        ((df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] <= 0.75))
    )
    
    df_strikes = df[strikes]
    df_balls = df[~strikes]
    
    dfx["Player"] = df["Batter"].iloc[0]
    dfx["PA"] = len(df[(df["PitchCall"] == "HitByPitch") | (df["KorBB"] == "Strikeout") | (df["KorBB"] == "Walk") | (df["PitchCall"] == "InPlay")])
    dfx["AB"] = len(df[(df["PitchCall"] == "InPlay") | (df["KorBB"] == "Strikeout")])
    dfx["Pitches Seen"] = len(df) - len(df[df["PitchCall"] == "HitByPitch"])
    dfx["Hits"] = len(df[(df["PlayResult"] == "Single") | (df["PlayResult"] == "Double") | (df["PlayResult"] == "Triple") | (df["PlayResult"] == "HomeRun")])
    dfx["BB"] = len(df[df["KorBB"] == "Walk"])
    dfx["HBP"] = len(df[df["PitchCall"] == "HitByPitch"])
    dfx["AVG"] = round(dfx["Hits"] / dfx["AB"], 3)
    dfx["OBP"] = round((dfx["Hits"] + dfx["BB"] +  dfx["HBP"]) / dfx["PA"], 3)
    dfx["1B"] = len(df[df["PlayResult"] == "Single"])
    dfx["2B"] = len(df[df["PlayResult"] == "Double"])
    dfx["3B"] = len(df[df["PlayResult"] == "Triple"])
    dfx["HR"] = len(df[df["PlayResult"] == "HomeRun"])
    dfx["TB"] = dfx["1B"] + (2 * dfx["2B"]) + (3 * dfx["3B"]) + (4 * dfx["HR"])
    dfx["SLG"] = round(dfx["TB"] / dfx["AB"], 3)
    dfx["OPS"] = dfx["OBP"] + dfx["SLG"]
    dfx["XBH"] = dfx["2B"] + dfx["3B"] + dfx["HR"]
    dfx["K"] = len(df[df["KorBB"] == "Strikeout"])
    rbi_eligible = df[
        (
            (df["PitchCall"] == "InPlay") &
            (~df["PlayResult"].isin(["Error", "FieldersChoice"]))
        )
        | (df["KorBB"] == "Walk")
        | (df["PitchCall"] == "HitByPitch")
    ]

    dfx["RBI"] = sum(rbi_eligible["RunsScored"])
            
    return dfx

def move_column(df, colname, position):
    cols = list(df.columns)
    cols.insert(position, cols.pop(cols.index(colname)))
    return df[cols]

df_uri = df[df["BatterTeam"] == "RHO_RAM"]

dfb = uri_batters_report(df_uri)

dfbs = dfb.sort_values("Player", ascending=True)

col1, col2 = st.columns([1,1])
with col1:
    st.header("Batting Statistics")

st.dataframe(dfbs, hide_index=True, height=800)
st.set_page_config(layout="wide")