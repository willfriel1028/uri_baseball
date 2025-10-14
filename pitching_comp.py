import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st

df = pd.read_csv("data/Fall25Scrim(updated).csv")

df["Pitcher"] = df["Pitcher"].replace("Grotyohann, Connor ", "Grotyohann, Connor")

def uri_pitchers_report(df):
    
    names = list(df["Pitcher"].unique())
        
    dfs = []
            
    for name in names:
        
        dfn = df[df["Pitcher"] == name]
        df_pitcher = pitchers_stats_report(dfn)
        dfs.append(df_pitcher)
        
    final_df = pd.DataFrame(dfs).reset_index(drop=True)
    
    drop = ["HBP", "K", "BB/9", "K/9", "Strikes", "Strike%", "TotalPitches", "BF", "HR", "WHIP", "CalledStrikes", "Whiffs"]
    final_df = final_df.drop(drop, axis=1)
    
    mean_score = final_df["CompetitionScore/IP"].mean()
    std_score = final_df["CompetitionScore/IP"].std()
    
    final_df["DominantScore"] = round((final_df["CompetitionScore/IP"] - mean_score) / std_score, 2)
    
    final_df = move_column(final_df, "CompetitionScore", 1)
    final_df = move_column(final_df, "CompetitionScore/IP", 2)
    final_df = move_column(final_df, "DominantScore", 3)
    final_df = move_column(final_df, "BB", 16)
    final_df = move_column(final_df, "Runs", 16)
    final_df = move_column(final_df, "Hits", 16)
    final_df = move_column(final_df, "IP", 1)
    final_df = move_column(final_df, "G", 1)
        
    #final_df.to_csv(csv + "_pitchers_report.csv")
    
    return final_df

def pitchers_stats_report(df):
    
    dfx = {}
    
    dfx["Pitcher"] = df["Pitcher"].iloc[0]
    dfx["IP"] = round((len(df[df["KorBB"] == "Strikeout"]) + sum(df["OutsOnPlay"])) / 3, 2)
    dfx["HBP"] = len(df[df["PitchCall"] == "HitByPitch"])
    dfx["BB"] = len(df[df["KorBB"] == "Walk"])
    dfx["K"] = len(df[df["KorBB"] == "Strikeout"])
    dfx["BB/9"] = round((dfx["BB"] / dfx["IP"]) * 9, 2)
    dfx["K/9"] = round((dfx["K"] / dfx["IP"]) * 9, 2)
    dfx["Strikes"] = len(df[(df["PitchCall"] == "StrikeCalled") | (df["PitchCall"] == "StrikeSwinging") | (df["PitchCall"] == "FoulBallNotFieldable") | (df["PitchCall"] == "InPlay")])
    dfx["TotalPitches"] = len(df)
    dfx["Strike%"] = round((dfx["Strikes"] / dfx["TotalPitches"]) * 100, 1)
    firstp = df[df["PitchofPA"] == 1]
    dfx["1pK"] = len(firstp[(firstp["PitchCall"] == "StrikeCalled") | (firstp["PitchCall"] == "StrikeSwinging") | (firstp["PitchCall"] == "FoulBallNotFieldable") | (firstp["PitchCall"] == "InPlay")])
    dfx["BF"] = len(firstp)
    dfx["1pK%"] = round((dfx["1pK"] / dfx["BF"]) * 100, 1)
    oneone = df[(df["Balls"] == 1) & (df["Strikes"] == 1)]
    if len(oneone) > 0:
        dfx["1-1K%"] = round((len(oneone[(oneone["PitchCall"] == "StrikeCalled") | (oneone["PitchCall"] == "StrikeSwinging") | (oneone["PitchCall"] == "FoulBallNotFieldable") | (oneone["PitchCall"] == "InPlay")]) / len(oneone)) * 100, 1)
    else:
        dfx["1-1K%"] = 0
    dfx["Hits"] = len(df[(df["PlayResult"] == "Single") | (df["PlayResult"] == "Double") | (df["PlayResult"] == "Triple") | (df["PlayResult"] == "HomeRun")])
    dfx["HR"] = len(df[df["PlayResult"] == "HomeRun"])
    dfx["Runs"] = sum(df["RunsScored"])
    dfx["WHIP"] = round((dfx["BB"] + dfx["Hits"]) / dfx["IP"], 2)
    dfx["CalledStrikes"] = len(df[df["PitchCall"] == "StrikeCalled"])
    dfx["Whiffs"] = len(df[df["PitchCall"] == "StrikeSwinging"])
    oneK = df[(df["Strikes"] == 1) & (df["Balls"] <= 1)]
    if len(oneK) > 0:
        dfx["0-2 or 1-2"] = len(oneK[(oneK["PitchCall"] == "StrikeCalled") | (oneK["PitchCall"] == "StrikeSwinging") | (oneK["PitchCall"] == "FoulBallNotFieldable")])
    else: 
        dfx["0-2 or 1-2"] = 0
    
    dfx["4PitchesOrLess"] = 0
    for d in df["Date"].dropna().unique():
        dfd = df[df["Date"] == d]
        if not dfd.empty:
            for i in range(1, dfd["Inning"].max() + 1):
                dfi = dfd[dfd["Inning"] == i]
                if not dfi.empty:
                    for p in range(1, dfi["PAofInning"].max() + 1):
                        dfip = dfi[dfi["PAofInning"] == p]
                        if (len(dfip) <= 4) & (len(dfip) >= 1):
                            dfx["4PitchesOrLess"] = dfx["4PitchesOrLess"] + 1
                
    dfx["IPw/0s"] = 0
    for d in df["Date"].dropna().unique():
        dfd = df[df["Date"] == d]
        if not dfd.empty:
            for i in range(1, dfd["Inning"].max() + 1):
                dfi = dfd[dfd["Inning"] == i]
                if not dfi.empty:
                    if sum(dfi["RunsScored"]) == 0:
                        dfx["IPw/0s"] = dfx["IPw/0s"] + 1
            
    leadoff = df[df["PAofInning"] == 1]
    dfx["LeadoffOut"] = len(leadoff[(leadoff["KorBB"] == "Strikeout") | (leadoff["OutsOnPlay"] > 0)])
    
    dfx["123"] = 0
    for d in df["Date"].dropna().unique():
        dfd = df[df["Date"] == d]
        if not dfd.empty:
            for i in range(1, dfd["Inning"].max() + 1):
                dfi = dfd[dfd["Inning"] == i]
                if not dfi.empty:
                    if sum(dfi["PAofInning"].dropna().unique()) == 6:
                        dfx["123"] = dfx["123"] + 1
            
    dfx["Total+"] = dfx["0-2 or 1-2"] + dfx["K"] + dfx["4PitchesOrLess"] + dfx["IPw/0s"] + dfx["LeadoffOut"] + dfx["123"]
    dfx["HBP on Offspeed"] = len(df[((df["TaggedPitchType"] == "Slider") | (df["TaggedPitchType"] == "Curveball") | (df["TaggedPitchType"] == "ChangeUp")) & (df["PitchCall"] == "HitByPitch")])
    dfx["LeadoffOn"] = len(leadoff[(leadoff["KorBB"] == "Walk") | (leadoff["PlayResult"] == "Single") | (leadoff["PlayResult"] == "Double") | (leadoff["PlayResult"] == "Triple") | (leadoff["PlayResult"] == "HomeRun") | (leadoff["PitchCall"] == "HitByPitch")])
    dfx["Total-"] = dfx["BB"] + dfx["Runs"] + dfx["Hits"] + dfx["HBP on Offspeed"] + dfx["LeadoffOn"]
    
    dfx["CompetitionScore"] = dfx["0-2 or 1-2"] + dfx["K"] + dfx["4PitchesOrLess"] + dfx["IPw/0s"] + dfx["LeadoffOut"] + (2 * dfx["123"]) - dfx["BB"] - dfx["Runs"] - dfx["Hits"] - dfx["HBP on Offspeed"] - dfx["LeadoffOn"]
    dfx["CompetitionScore/IP"] = round(dfx["CompetitionScore"] / dfx["IP"], 2)
    dfx["G"] = len(df["Date"].unique())
    
    return dfx

def move_column(df, colname, position):
    cols = list(df.columns)
    cols.insert(position, cols.pop(cols.index(colname)))
    return df[cols]

df_uri = df[df["PitcherTeam"] == "RHO_RAM"]

dfp = uri_pitchers_report(df_uri)

dfps = dfp.sort_values("Pitcher", ascending=True)

#def highlight_domscore(val):
    #return "background-color: lightblue"  # or "color: red" for text

#styled = dfps.style.applymap(highlight_domscore, subset=["DominantScore"])

col1, col2 = st.columns([1,1])
with col1:
    st.header("Competition Score")

st.dataframe(dfps, hide_index=True, height=800, width=800, use_container_width=True)
st.set_page_config(layout="wide")