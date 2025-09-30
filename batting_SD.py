import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st

df = pd.read_csv("data/Fall25Scrim(updated).csv")

def uri_batters_report(df):
    
    names = list(df["Batter"].unique())
        
    dfs = []
    
    pitches = list(df["TaggedPitchType"].unique())
    
    for name in names:
        
        dfn = df[df["Batter"] == name]
        df_batter = batters_stats_report(dfn, pitches)
        dfs.append(df_batter)
        
    final_df = pd.DataFrame(dfs).reset_index(drop=True)
    
    final_df = move_column(final_df, "TotalScore", 2)
    final_df = move_column(final_df, "Correct%", 3)
    final_df = move_column(final_df, "Swing%vsStrike", 4)
    final_df = move_column(final_df, "Hold%vsBall", 5)
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
    dfx["Pitches"] = len(df) - len(df[df["PitchCall"] == "HitByPitch"])
    dfx["SwingAtStrike"] = len(df_strikes[(df_strikes["PitchCall"] == "InPlay") | (df_strikes["PitchCall"] == "FoulBallNotFieldable") | (df_strikes["PitchCall"] == "StrikeSwinging")])
    dfx["StrikeTaken"] = len(df_strikes[(df_strikes["PitchCall"] == "StrikeCalled")])
    dfx["SwingAtBall"] = len(df_balls[(df_balls["PitchCall"] == "InPlay") | (df_balls["PitchCall"] == "FoulBallNotFieldable") | (df_balls["PitchCall"] == "StrikeSwinging")])
    dfx["BallTaken"] = len(df_balls[df_balls["PitchCall"] == "BallCalled"])
    dfx["IZMiss"] = len(df_strikes[df_strikes["PitchCall"] == "StrikeSwinging"])
    dfx["2K BIP/Foul"] = len(df[(df["Strikes"] == 2) & ((df["PitchCall"] == "FoulBallNotFieldable") | (df["PitchCall"] == "InPlay"))])
    dfx["TotalScore"] = (dfx["SwingAtStrike"] - dfx["StrikeTaken"] - (2 * dfx["SwingAtBall"]) + dfx["BallTaken"] - (2 * dfx["IZMiss"]) + dfx["2K BIP/Foul"])
    
    for i in range(len(df_strikes)):
        if df_strikes["PitchCall"].iloc[i] == "BallCalled":
            dfx["BallTaken"] = dfx["BallTaken"] + 1
    for i in range(len(df_balls)):
        if df_balls["PitchCall"].iloc[i] == "StrikeCalled":
            dfx["StrikeTaken"] = dfx["StrikeTaken"] + 1
    
    dfx["StrikesSeen"] = dfx["StrikeTaken"] + dfx["SwingAtStrike"]
    dfx["BallsSeen"] = dfx["BallTaken"] + dfx["SwingAtBall"]
    
    if dfx["StrikesSeen"] > 0:
        dfx["Swing%vsStrike"] = round(((dfx["SwingAtStrike"] / dfx["StrikesSeen"]) * 100), 1)
    else:
        dfx["Swing%vsStrike"] = 0
    
    if dfx["BallsSeen"] > 0:
        dfx["Hold%vsBall"] = round(((dfx["BallTaken"] / dfx["BallsSeen"]) * 100), 1)
    else:
        dfx["Hold%vsBalll"] = 0
        
    correct_strikes = df_strikes[(df_strikes["PitchCall"] == "InPlay") | (df_strikes["PitchCall"] == "FoulBallNotFieldable") | (df_strikes["PitchCall"] == "StrikeSwinging") | (df_strikes["PitchCall"] == "BallCalled")]
    correct_balls = df_balls[df_balls["PitchCall"] == "BallCalled"]
    incorrect_strikes = df_strikes[df_strikes["PitchCall"] == "StrikeCalled"]
    incorrect_balls = df_balls[(df_balls["PitchCall"] == "InPlay") | (df_balls["PitchCall"] == "FoulBallNotFieldable") | (df_balls["PitchCall"] == "StrikeSwinging") | (df_balls["PitchCall"] == "StrikeCalled")]
    
    df_correct = pd.concat([correct_strikes, correct_balls], ignore_index=True)
    df_incorrect = pd.concat([incorrect_strikes, incorrect_balls], ignore_index=True)
    
    dfx["Correct_Decisions"] = len(df_correct)
    dfx["Incorrect_Decisions"] = len(df_incorrect)
    dfx["Correct%"] = round((dfx["Correct_Decisions"] / dfx["Pitches"]) * 100, 1)
               
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

st.dataframe(dfbs, hide_index=True, height=800)
st.set_page_config(layout="wide")