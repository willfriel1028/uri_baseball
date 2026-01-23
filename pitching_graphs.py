import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from matplotlib.lines import Line2D

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

st.set_page_config(layout="wide")
#D93434
#FF8800
PITCH_COLORS = {
    "Fastball": "#FF8800",
    "Curveball": "#919090",
    "Slider": "#333DD6",
    "ChangeUp": "#D93434",
    "Cutter": "#28BD4F",
    "Splitter": "#AA00FF",
    "Sinker": "#C8FF00",
    "Knuckleball": "#BB8FCE",
    "Sweeper": "#34CED9",
}

def print_graphs(df, PITCH_ORDER, OUTCOME_ORDER, PITCH_COLORS):
    
    col1, col2 = st.columns(2)
    
    with col1:
        pitchbreak(df, PITCH_ORDER, PITCH_COLORS)
    with col2:
        releasepoint(df, PITCH_ORDER, PITCH_COLORS)
        
    
        
    col1, col2 = st.columns(2)
    
    with col1:
        pitch_outcome(df, OUTCOME_ORDER)
    with col2:
        extension(df, PITCH_ORDER, PITCH_COLORS)
        
def pitchbreak(df, PITCH_ORDER, PITCH_COLORS):
    
    palette = [PITCH_COLORS.get(pitch, "#808080") for pitch in PITCH_ORDER]
    
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x='HorzBreak', y='InducedVertBreak', hue='TaggedPitchType', hue_order=PITCH_ORDER, palette=palette, clip_on=False, ax=ax)
    ax.set_title("Pitch Break Chart")
    ax.set_xlabel("Horizontal Break")
    ax.set_ylabel("Induced Vertical Break")
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.axvline(0, color='black', linestyle='--', linewidth=1)
    ax.grid()
    handles, labels = ax.get_legend_handles_labels()
    unique_pitches = df["TaggedPitchType"].unique()
    new_handles = [h for h, l in zip(handles, labels) if l in unique_pitches]
    new_labels = [l for l in labels if l in unique_pitches]
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0., fontsize=7)    
    #ax.legend().remove()
    st.pyplot(fig)
    
def releasepoint(df, PITCH_ORDER, PITCH_COLORS):
    
    palette = [PITCH_COLORS.get(pitch, "#808080") for pitch in PITCH_ORDER]
    
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x="RelSidei", y="RelHeighti", hue="TaggedPitchType", hue_order=PITCH_ORDER, palette=palette, ax=ax)
    ax.set_title("Release Point Chart")
    ax.set_xlabel("inches")
    ax.set_ylabel("inches")
    ax.set_xlim(-48, 48)
    ax.set_ylim(0, 96)
    ax.axvline(0, color='black', linestyle='--', linewidth=1)
    ax.grid()
    handles, labels = ax.get_legend_handles_labels()
    unique_pitches = df["TaggedPitchType"].unique()
    new_handles = [h for h, l in zip(handles, labels) if l in unique_pitches]
    new_labels = [l for l in labels if l in unique_pitches]
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0., fontsize=7)  
    #ax.legend().remove()
    st.pyplot(fig)
    
def extension(df, PITCH_ORDER, PITCH_COLORS):
    
    palette = [PITCH_COLORS.get(pitch, "#808080") for pitch in PITCH_ORDER]
    
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x="RelSidei", y="Extensioni", hue="TaggedPitchType", hue_order=PITCH_ORDER, palette=palette, ax=ax)
    ax.set_title("Extension Chart")
    ax.set_xlabel("inches")
    ax.set_ylabel("inches")
    ax.set_xlim(-48, 48)
    ax.set_ylim(0, 96)
    ax.axvline(0, color='black', linestyle='--', linewidth=1)
    ax.grid()
    handles, labels = ax.get_legend_handles_labels()
    unique_pitches = df["TaggedPitchType"].unique()
    new_handles = [h for h, l in zip(handles, labels) if l in unique_pitches]
    new_labels = [l for l in labels if l in unique_pitches]
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0., fontsize=7)  
    #ax.legend().remove()
    st.pyplot(fig)
    
def pitch_outcome(df, OUTCOME_ORDER):
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x="PlateLocSide", y="PlateLocHeight", hue="Outcome", hue_order=OUTCOME_ORDER, ax=ax)
    ax.set_title("Pitch Outcomes")
    ax.set_xlabel("Plate Location")
    ax.set_ylabel("Plate Location")
    ax.set_xlim(-3, 3)
    ax.set_ylim(-1, 6)
    ax.vlines(x=-0.75, ymin=1.65, ymax=3.65, color="black", linewidth=2)
    ax.vlines(x=0.75, ymin=1.65, ymax=3.65, color="black", linewidth=2)
    ax.vlines(x=-0.25, ymin=1.65, ymax=3.65, color="black", linewidth=1)
    ax.vlines(x=0.25, ymin=1.65, ymax=3.65, color="black", linewidth=1)    
    ax.hlines(y=3.65, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    ax.hlines(y=1.65, xmin=-0.75, xmax=0.75, color="black", linewidth=2)
    ax.hlines(y=2.32, xmin=-0.75, xmax=0.75, color="black", linewidth=1)
    ax.hlines(y=2.99, xmin=-0.75, xmax=0.75, color="black", linewidth=1)
    handles, labels = ax.get_legend_handles_labels()
    unique_outcomes = df["Outcome"].unique()
    new_handles = [h for h, l in zip(handles, labels) if l in unique_outcomes]
    new_labels = [l for l in labels if l in unique_outcomes]
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0., fontsize=7)    
    #ax.legend(new_handles, new_labels, fontsize = 5)
    st.pyplot(fig)
    
def get_outcome(df):
    
    df["Outcome"] = [0 for _ in range(len(df))]
    
    for i in range(0, len(df)):
        if df["PitchCall"].iloc[i] == "StrikeCalled":
            df["Outcome"].iloc[i] = "Strike Called"
        elif df["PitchCall"].iloc[i] == "StrikeSwinging":
            df["Outcome"].iloc[i] = "Strike Swinging"
        elif df["PitchCall"].iloc[i] == "BallCalled":
            df["Outcome"].iloc[i] = "Ball Called"
        elif df["PitchCall"].iloc[i] == "HitByPitch":
            df["Outcome"].iloc[i] = "HBP"
        elif df["PitchCall"].iloc[i] == "InPlay":
            df["Outcome"].iloc[i] = "In Play"
        elif df["PitchCall"].iloc[i] == "FoulBallNotFieldable":
            df["Outcome"].iloc[i] = "Foul Ball Not Fieldable"
    return df   

fall = pd.read_csv("data/Fall25Scrim(updated).csv")
spring = pd.read_csv("data/Spring26Scrim(updated).csv")

selections = st.pills("Include Data From:", 
                     ["Fall Scrimmages", "Spring Scrimmages"],
                     selection_mode="multi")

if selections == ["Fall Scrimmages"]:
    data = fall.copy()
elif selections == ["Spring Scrimmages"]:
    data = spring.copy()
else:
    data = pd.concat([fall, spring], ignore_index=True)

data = data.reset_index(drop=True)
    
df = data[data["PitcherTeam"] == "RHO_RAM"]
df["Pitcher"] = df["Pitcher"].replace("Grotyohann, Connor ", "Grotyohann, Connor")
df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12
df["Extensioni"] = df["Extension"] * 12
PITCH_ORDER = list(df["TaggedPitchType"].unique())
if "Undefined" in PITCH_ORDER:
    PITCH_ORDER.remove("Undefined")
if "Other" in PITCH_ORDER:
    PITCH_ORDER.remove("Other")
df = get_outcome(df)
OUTCOME_ORDER = list(df["Outcome"].unique())

df_sorted = df.sort_values("Pitcher")
total = ["TOTAL", "All LHP", "All RHP"]
names = list(df_sorted["Pitcher"].unique())

choices = total + names

col1, col2, col3 = st.columns([1,1,1])
with col1:
    options = st.selectbox("Pitcher", options=choices)
    
not_valid = ["TOTAL", "All LHP", "All RHP"]
    
if  options not in not_valid:
    dfp = df[df["Pitcher"] == options]
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
    side = st.selectbox("Batter Side", options=choices)
    
if options not in not_valid:
    dfp = df[df["Pitcher"] == options]
    alld = ["TOTAL"]
    dates = list(dfp["Date"].dropna().unique())
    choices = alld + dates
else:
    alld = ["TOTAL"]
    dates = list(df["Date"].dropna().unique())
    choices = alld + dates

col1, col2, col3 = st.columns([1,1,1])
with col1:
    date = st.selectbox("Date", options=choices)
    
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
elif options == "All LHP":
    new_df0 = df[df["PitcherThrows"] == "Left"]
elif options == "All RHP":
    new_df0 = df[df["PitcherThrows"] == "Right"]
else:
    new_df0 = df[df["Pitcher"] == options]
    
if pitch == "ALL":
    new_df1 = new_df0
else:
    new_df1 = new_df0[new_df0["TaggedPitchType"] == pitch]
    
if side == "ALL":
    new_df2 = new_df1
else:
    new_df2 = new_df1[new_df1["BatterSide"] == side]
    
if date == "TOTAL":
    new_df3 = new_df2
else:
    new_df3 = new_df2[new_df2["Date"] == date]
    
filtered_pitch_order = [p for p in PITCH_ORDER if p in new_df3["TaggedPitchType"].unique()]
filtered_outcome_order = [o for o in OUTCOME_ORDER if o in new_df3["Outcome"].unique()]

print_graphs(new_df3, filtered_pitch_order, filtered_outcome_order, PITCH_COLORS)
        
        
  
        