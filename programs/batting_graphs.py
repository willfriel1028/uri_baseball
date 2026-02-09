import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from matplotlib.lines import Line2D

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="stAppViewContainer"], [class*="main"], [class*="block-container"] {
        height: 100%;
        overflow: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def print_graphs(df):
    
    col1, col2 = st.columns(2)
    
    with col1:
        slug_zones(df)
    with col2:
        correct_zones(df)

def slug_zones(df):
    A1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    B1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    C1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    D1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    E1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)] 
    
    zones = [A1, A2, A3, A4, A5, B1, B2, B3, B4, B5, C1, C2, C3, C4, C5, D1, D2, D3, D4, D5, E1, E2, E3, E4, E5]
    avg = []
    
    for zone in zones:
        AB = len(zone[(zone["PitchCall"] == "InPlay") | (zone["KorBB"] == "Strikeout")])
        B1 = len(zone[zone["PlayResult"] == "Single"])
        B2 = len(zone[zone["PlayResult"] == "Double"])
        B3 = len(zone[zone["PlayResult"] == "Triple"])
        HR = len(zone[zone["PlayResult"] == "HomeRun"])
        H = B1 + B2 + B3 + HR
        TB = B1 + (2 * B2) + (3 * B3) + (4 * HR)
        if AB > 0:
            AVG = round(H / AB, 3)
        else:
            AVG = 0
        
        avg.append(AVG)
    
    avg_array = np.array(avg)
    avg_grid = avg_array.reshape(5, 5)
    
    fig, ax = plt.subplots(figsize=(6,7))
    im = ax.imshow(avg_grid, cmap='coolwarm', origin='upper',
               extent=[-1.25, 1.25, 0.9833, 4.3167],
               vmin=0.1, vmax=0.5)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Batting Average")
    ax.vlines(x=-0.75, ymin=1.65, ymax=3.65, color="black", linewidth=3)
    ax.vlines(x=0.75, ymin=1.65, ymax=3.65, color="black", linewidth=3)
    ax.vlines(x=-0.25, ymin=1.65, ymax=3.65, color="black", linewidth=2)
    ax.vlines(x=0.25, ymin=1.65, ymax=3.65, color="black", linewidth=2)    
    ax.hlines(y=3.65, xmin=-0.75, xmax=0.75, color="black", linewidth=3)
    ax.hlines(y=1.65, xmin=-0.75, xmax=0.75, color="black", linewidth=3)
    ax.hlines(y=2.32, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    ax.hlines(y=2.99, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    x_centers = np.linspace(-1.0, 1.0, 5)   
    y_centers = np.linspace(4.0, 1.3, 5) 
    for i, y in enumerate(y_centers):       
        for j, x in enumerate(x_centers):   
            value = avg_grid[i, j]
            ax.text(x, y, f"{value:.3f}", ha='center', va='center',
                    color='black', fontsize=8, fontweight='bold')
    ax.set_title("AVG")
    ax.set_xlabel("Plate Location")
    ax.set_ylabel("Plate Location")
    st.pyplot(fig)
    
def correct_zones(df):
    A1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    A5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 4.3167) & (df["PlateLocHeight"] > 3.65)]
    B1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    B5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 3.65) & (df["PlateLocHeight"] > 2.9833)]
    C1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    C5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 2.9833) & (df["PlateLocHeight"] > 2.3167)]
    D1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    D5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 2.3167) & (df["PlateLocHeight"] > 1.65)]
    E1 = df[(df["PlateLocSide"] >= -1.25) & (df["PlateLocSide"] < -0.75) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E2 = df[(df["PlateLocSide"] >= -0.75) & (df["PlateLocSide"] < -0.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E3 = df[(df["PlateLocSide"] >= -0.25) & (df["PlateLocSide"] < 0.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E4 = df[(df["PlateLocSide"] >= 0.25) & (df["PlateLocSide"] < 0.75) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)]
    E5 = df[(df["PlateLocSide"] >= 0.75) & (df["PlateLocSide"] <= 1.25) & (df["PlateLocHeight"] <= 1.65) & (df["PlateLocHeight"] >= 0.9833)] 
    
    zones = [A1, A2, A3, A4, A5, B1, B2, B3, B4, B5, C1, C2, C3, C4, C5, D1, D2, D3, D4, D5, E1, E2, E3, E4, E5]
    corr = []
    
    for zone in zones:
        strikes = (
            ((zone["PlateLocHeight"] >= 1.65) & (zone["PlateLocHeight"] <= 3.65)) & 
            ((zone["PlateLocSide"] >= -0.75) & (zone["PlateLocSide"] <= 0.75))
        )

        df_strikes = zone[strikes]
        df_balls = zone[~strikes]
        
        pitches = len(zone) - len(zone[zone["PitchCall"] == "HitByPitch"])
        
        correct_strikes = df_strikes[(df_strikes["PitchCall"] == "InPlay") | (df_strikes["PitchCall"] == "FoulBallNotFieldable") | (df_strikes["PitchCall"] == "StrikeSwinging")]
        correct_balls = df_balls[(df_balls["PitchCall"] == "BallCalled") | (df_balls["PitchCall"] == "StrikeCalled")]

        df_correct = pd.concat([correct_strikes, correct_balls], ignore_index=True)

        correct = len(df_correct)
        if pitches != 0: 
            correct_percent = round((correct / pitches) * 100, 1)
        else:
            correct_percent = 0
        
        corr.append(correct_percent)
    
    corr_array = np.array(corr)
    corr_grid = corr_array.reshape(5, 5)
    
    fig, ax = plt.subplots(figsize=(6,7))
    im = ax.imshow(corr_grid, cmap='coolwarm', origin='upper',
               extent=[-1.25, 1.25, 0.9833, 4.3167],
               vmin=40, vmax=80)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Correct Decisions %")
    ax.vlines(x=-0.75, ymin=1.65, ymax=3.65, color="black", linewidth=3)
    ax.vlines(x=0.75, ymin=1.65, ymax=3.65, color="black", linewidth=3)
    ax.vlines(x=-0.25, ymin=1.65, ymax=3.65, color="black", linewidth=2)
    ax.vlines(x=0.25, ymin=1.65, ymax=3.65, color="black", linewidth=2)    
    ax.hlines(y=3.65, xmin=-0.75, xmax=0.75, color="black", linewidth=3)
    ax.hlines(y=1.65, xmin=-0.75, xmax=0.75, color="black", linewidth=3)
    ax.hlines(y=2.32, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    ax.hlines(y=2.99, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    x_centers = np.linspace(-1.0, 1.0, 5)   
    y_centers = np.linspace(4.0, 1.3, 5) 
    for i, y in enumerate(y_centers):       
        for j, x in enumerate(x_centers):   
            value = corr_grid[i, j]
            ax.text(x, y, f"{value:.1f}", ha='center', va='center',
                    color='black', fontsize=8, fontweight='bold')
    ax.set_title("Correct Decisions %")
    ax.set_xlabel("Plate Location")
    ax.set_ylabel("Plate Location")
    st.pyplot(fig)

fall = pd.read_csv("data/Fall25Scrim(updated).csv")
spring = pd.read_csv("data/Spring26Scrim(updated).csv")

selections = st.pills("Include Data From:", 
                     ["Fall Scrimmages", "Spring Scrimmages"],
                     selection_mode="multi")

if selections == ["Fall Scrimmages"]:
    data = fall
elif selections == ["Spring Scrimmages"]:
    data = spring
else:
    data = pd.concat([fall, spring])

df = data[data["BatterTeam"] == "RHO_RAM"]
PITCH_ORDER = list(df["TaggedPitchType"].unique())

df_sorted = df.sort_values("Batter")
total = ["TOTAL", "All LHB", "All RHB"]
names = list(df_sorted["Batter"].unique())
if "Creed, Will" in names:
    names.remove("Creed, Will")
if "Houchens, Sam" in names:
    names.remove("Houchens, Sam")
if "Aikens, Parker" in names:
    names.remove("Aikens, Parker")

choices = total + names

col1, col2, col3 = st.columns([1,1,1])
with col1:
    options = st.selectbox("Batter", options=choices)
    
not_valid = ["TOTAL", "All LHB", "All RHB"]
    
if  options not in not_valid:
    dfp = df[df["Batter"] == options]
    all1 = ["ALL"]
    pitches = list(dfp["TaggedPitchType"].unique())
    choices = all1 + pitches
    
else:
    all1 = ["ALL"]
    pitches = list(df["TaggedPitchType"].unique())
    choices = all1 + pitches    
    
col1, col2, col3 = st.columns([1,1,1])
with col1:    
    pitch = st.selectbox("Pitch", options=choices)
    
choices = ["ALL", "Right", "Left"]
    
col1, col2, col3 = st.columns([1,1,1])
with col1:
    side = st.selectbox("Pitch Hand", options=choices)
    
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.header(options)
    
#if options == "TOTAL":
    #if pitch == "ALL":
        #new_df = df
    #else:
        #new_df = df[df["TaggedPitchType"] == pitch]
#else:
    #if pitch == "ALL":
        #new_df = df[df["Pitcher"] == options]
    #else:
        #new_df = df[(df["Pitcher"] == options) & (df["TaggedPitchType"] == pitch)]
        
if options == "TOTAL":
    new_df0 = df
elif options == "All LHB":
    new_df0 = df[df["BatterSide"] == "Left"]
elif options == "All RHB":
    new_df0 = df[df["BatterSide"] == "Right"]
else:
    new_df0 = df[df["Batter"] == options]
    
if pitch == "ALL":
    new_df1 = new_df0
else:
    new_df1 = new_df0[new_df0["TaggedPitchType"] == pitch]
    
if side == "ALL":
    new_df2 = new_df1
else:
    new_df2 = new_df1[new_df1["PitcherThrows"] == side]
        
print_graphs(new_df2)