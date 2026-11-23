import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import streamlit as st
import glob

#fall = pd.read_csv("data/Fall25Scrim(updated).csv")
#spring = pd.read_csv("data/Spring26Scrim(updated).csv")
#season = pd.concat([pd.read_csv(f) for f in glob.glob("data/26Season/*.csv")], ignore_index=True)

#selections = st.pills("Include Data From:", 
                     #["Regular Season", "Fall Scrimmages"],
                     #selection_mode="multi")

#if selections == ["Fall Scrimmages"]:
    #df = fall
#elif selections == ["Regular Season"]:
    #df = season
#elif selections == ["Regular Season", "Fall Scrimmages"]:
    #df = pd.concat([fall, season])
#else:
    #df = season

df = pd.concat([pd.read_csv(f) for f in glob.glob("data/Fall26/*.csv")], ignore_index=True)

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
    if dfx["IP"] != 0:
        dfx["RA"] = round((dfx["Runs"] / dfx["IP"]) * 9, 2)
        dfx["BB/9"] = round((dfx["BB"] / dfx["IP"]) * 9, 2)
        dfx["K/9"] = round((dfx["K"] / dfx["IP"]) * 9, 2)
    elif dfx["IP"] == 0:
        dfx["RA"] = np.nan
        dfx["BB/9"] = np.nan
        dfx["K/9"] = np.nan
    dfx["Strikes"] = len(df[(df["PitchCall"] == "StrikeCalled") | (df["PitchCall"] == "StrikeSwinging") | (df["PitchCall"] == "FoulBallNotFieldable") | (df["PitchCall"] == "InPlay")])
    dfx["Strike%"] = round((dfx["Strikes"] / dfx["TotalPitches"]) * 100, 1)
    firstp = df[df["PitchofPA"] == 1]
    dfx["BF"] = len(firstp)
    dfx["HR"] = len(df[df["PlayResult"] == "HomeRun"])
    if dfx["IP"] != 0:
        dfx["WHIP"] = round((dfx["BB"] + dfx["Hits"]) / dfx["IP"], 2)
    elif dfx["IP"] == 0:
        dfx["WHIP"] = np.nan
    dfx["CalledStrikes"] = len(df[df["PitchCall"] == "StrikeCalled"])
    dfx["Whiffs"] = len(df[df["PitchCall"] == "StrikeSwinging"])
    dfx["CSW%"] = round(((dfx["CalledStrikes"] + dfx["Whiffs"]) * 100) / dfx["TotalPitches"], 1)
    
    return dfx

def move_column(df, colname, position):
    cols = list(df.columns)
    cols.insert(position, cols.pop(cols.index(colname)))
    return df[cols]

df_uri = df[df["PitcherTeam"] == "RHO_RAM"].copy()

# Parse dates so they can be filtered
df_uri["GameDate"] = pd.to_datetime(df_uri["Date"], format="mixed", errors="coerce").dt.date
min_date = df_uri["GameDate"].min()
max_date = df_uri["GameDate"].max()

col1, col2 = st.columns([1,1])
with col1:
    st.header("Pitching Statistics")
with col2:
    st.markdown("**Filter by Date**")
    use_range = st.session_state.get("use_range", False)

    if not use_range:
        # Plain one-date picker, so no empty second date is shown
        single = st.date_input(
            "Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
        )
        start_date = end_date = single
    else:
        date_sel = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if len(date_sel) == 2:
            start_date, end_date = date_sel
        elif len(date_sel) == 1:
            # Only the start date picked so far
            start_date = end_date = date_sel[0]
        else:
            start_date, end_date = min_date, max_date

    st.checkbox("Filter by date range", key="use_range")

df_filtered = df_uri[(df_uri["GameDate"] >= start_date) & (df_uri["GameDate"] <= end_date)]

if df_filtered.empty:
    st.warning("No pitching data in the selected date range.")
else:
    dfp = uri_pitchers_report(df_filtered.drop(columns="GameDate"))
    dfps = dfp.sort_values("Pitcher", ascending=True)
    # Size the table to fit its rows (about 35px per row, plus the header row)
    table_height = (len(dfps) + 1) * 35 + 3
    st.dataframe(dfps, hide_index=True, height=table_height)
st.set_page_config(layout="wide")