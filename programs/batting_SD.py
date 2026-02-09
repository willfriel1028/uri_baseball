import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image

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

def uri_batters_report(df):
    
    names = list(df["Batter"].unique())
    if "Creed, Will" in names:
        names.remove("Creed, Will")
    if "Houchens, Sam" in names:
        names.remove("Houchens, Sam")
    if "Aikens, Parker" in names:
        names.remove("Aikens, Parker")
        
    dfs = []
    
    pitches = list(df["TaggedPitchType"].unique())
    
    for name in names:
        
        dfn = df[df["Batter"] == name]
        df_batter = batters_stats_report(dfn, pitches)
        dfs.append(df_batter)
        
    final_df = pd.DataFrame(dfs).reset_index(drop=True)
    
    final_df = move_column(final_df, "Score", 4)
    final_df = move_column(final_df, "Correct%", 5)
    final_df = move_column(final_df, "SwingVsStrike%", 6)
    final_df = move_column(final_df, "NoSwingVsBall%", 7)
    final_df = move_column(final_df, "Score/PA", 5)
    final_df = final_df.drop("Pitches", axis=1)
        
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
    dfx["Pitches"] = len(df) - len(df[df["PitchCall"] == "HitByPitch"])
    dfx["SwingAtStrike"] = len(df_strikes[(df_strikes["PitchCall"] == "InPlay") | (df_strikes["PitchCall"] == "FoulBallNotFieldable") | (df_strikes["PitchCall"] == "StrikeSwinging")])
    dfx["StrikeTaken"] = len(df_strikes[(df_strikes["PitchCall"] == "StrikeCalled") | (df_strikes["PitchCall"] == "BallCalled")])
    dfx["SwingAtBall"] = len(df_balls[(df_balls["PitchCall"] == "InPlay") | (df_balls["PitchCall"] == "FoulBallNotFieldable") | (df_balls["PitchCall"] == "StrikeSwinging")])
    dfx["BallTaken"] = len(df_balls[(df_balls["PitchCall"] == "BallCalled") | (df_balls["PitchCall"] == "StrikeCalled")])
    dfx["IZMiss"] = len(df_strikes[df_strikes["PitchCall"] == "StrikeSwinging"])
    dfx["2K BIP/Foul"] = len(df[(df["Strikes"] == 2) & ((df["PitchCall"] == "FoulBallNotFieldable") | (df["PitchCall"] == "InPlay"))])
    dfx["Score"] = (dfx["SwingAtStrike"] - dfx["StrikeTaken"] - (2 * dfx["SwingAtBall"]) + dfx["BallTaken"] - (2 * dfx["IZMiss"]) + dfx["2K BIP/Foul"])
    
    dfx["StrikesSeen"] = dfx["StrikeTaken"] + dfx["SwingAtStrike"]
    dfx["BallsSeen"] = dfx["BallTaken"] + dfx["SwingAtBall"]
    
    if dfx["StrikesSeen"] > 0:
        dfx["SwingVsStrike%"] = round(((dfx["SwingAtStrike"] / dfx["StrikesSeen"]) * 100), 1)
    else:
        dfx["SwingVsStrike%"] = 0
    
    if dfx["BallsSeen"] > 0:
        dfx["NoSwingVsBall%"] = round(((dfx["BallTaken"] / dfx["BallsSeen"]) * 100), 1)
    else:
        dfx["NoSwingVsBall%"] = 0
        
    correct_strikes = df_strikes[(df_strikes["PitchCall"] == "InPlay") | (df_strikes["PitchCall"] == "FoulBallNotFieldable") | (df_strikes["PitchCall"] == "StrikeSwinging")]
    correct_balls = df_balls[(df_balls["PitchCall"] == "BallCalled") | (df_balls["PitchCall"] == "StrikeCalled")]
    incorrect_strikes = df_strikes[(df_strikes["PitchCall"] == "StrikeCalled") | (df_strikes["PitchCall"] == "BallCalled")]
    incorrect_balls = df_balls[(df_balls["PitchCall"] == "InPlay") | (df_balls["PitchCall"] == "FoulBallNotFieldable") | (df_balls["PitchCall"] == "StrikeSwinging")]
    
    df_correct = pd.concat([correct_strikes, correct_balls], ignore_index=True)
    df_incorrect = pd.concat([incorrect_strikes, incorrect_balls], ignore_index=True)
    
    dfx["Correct_Decisions"] = dfx["SwingAtStrike"] + dfx["BallTaken"]
    dfx["Incorrect_Decisions"] = dfx["StrikeTaken"] + dfx["SwingAtBall"]
    dfx["Correct%"] = round((dfx["Correct_Decisions"] / dfx["Pitches"]) * 100, 1)
    dfx["Score/PA"] = round(dfx["Score"] / dfx["PA"], 2)
               
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
    st.header("Swing Decision")
    
st.image("images/swing_decision.png")

st.dataframe(dfbs, hide_index=True, height=800)