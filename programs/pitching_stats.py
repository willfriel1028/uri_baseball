import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")

fall = pd.read_csv("data/Fall25Scrim(updated).csv")
spring = pd.read_csv("data/Spring26Scrim(updated).csv")

selections = st.pills("Include Data From:", 
                     ["Fall Scrimmages", "Spring Scrimmages"],
                     selection_mode="multi")

if selections == ["Fall Scrimmages"]:
    df = fall
elif selections == ["Spring Scrimmages"]:
    df = spring
else:
    df = pd.concat([fall, spring])

df["Pitcher"] = df["Pitcher"].replace("Grotyohann, Connor ", "Grotyohann, Connor")

def uri_pitchers_report(df):
    
    names = list(df["Pitcher"].unique())
        
    dfs = []
            
    for name in names:
        
        dfn = df[df["Pitcher"] == name]
        df_pitcher = pitchers_stats_report(dfn)
        dfs.append(df_pitcher)
        
    final_df = pd.DataFrame(dfs).reset_index(drop=True)
            
    #final_df.to_csv(csv + "_pitchers_report.csv")
    
    return final_df

def pitchers_stats_report(df):
    
    dfx = {}
    
    dfx["Pitcher"] = df["Pitcher"].iloc[0]
    dfx["G"] = len(df["Date"].dropna().unique())    
    dfx["IP"] = round((len(df[df["KorBB"] == "Strikeout"]) + sum(df["OutsOnPlay"])) / 3, 2)
    dfx["TotalPitches"] = len(df)
    dfx["Hits"] = len(df[(df["PlayResult"] == "Single") | (df["PlayResult"] == "Double") | (df["PlayResult"] == "Triple") | (df["PlayResult"] == "HomeRun")])
    dfx["Runs"] = sum(df["RunsScored"])
    dfx["BB"] = len(df[df["KorBB"] == "Walk"])
    dfx["K"] = len(df[df["KorBB"] == "Strikeout"])
    dfx["HBP"] = len(df[df["PitchCall"] == "HitByPitch"])
    dfx["RA"] = round((dfx["Runs"] / dfx["IP"]) * 9, 2)
    dfx["BB/9"] = round((dfx["BB"] / dfx["IP"]) * 9, 2)
    dfx["K/9"] = round((dfx["K"] / dfx["IP"]) * 9, 2)
    dfx["Strikes"] = len(df[(df["PitchCall"] == "StrikeCalled") | (df["PitchCall"] == "StrikeSwinging") | (df["PitchCall"] == "FoulBallNotFieldable") | (df["PitchCall"] == "InPlay")])
    dfx["Strike%"] = round((dfx["Strikes"] / dfx["TotalPitches"]) * 100, 1)
    firstp = df[df["PitchofPA"] == 1]
    dfx["BF"] = len(firstp)
    dfx["HR"] = len(df[df["PlayResult"] == "HomeRun"])
    dfx["WHIP"] = round((dfx["BB"] + dfx["Hits"]) / dfx["IP"], 2)
    dfx["CalledStrikes"] = len(df[df["PitchCall"] == "StrikeCalled"])
    dfx["Whiffs"] = len(df[df["PitchCall"] == "StrikeSwinging"])
    dfx["CSW%"] = round(((dfx["CalledStrikes"] + dfx["Whiffs"]) * 100) / dfx["TotalPitches"], 1)
    
    return dfx

def move_column(df, colname, position):
    cols = list(df.columns)
    cols.insert(position, cols.pop(cols.index(colname)))
    return df[cols]

df_uri = df[df["PitcherTeam"] == "RHO_RAM"]

dfp = uri_pitchers_report(df_uri)

dfps = dfp.sort_values("Pitcher", ascending=True)

col1, col2 = st.columns([1,1])
with col1:
    st.header("Pitching Statistics")

st.dataframe(dfps, hide_index=True, height=800)