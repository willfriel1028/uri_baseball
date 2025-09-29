import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(layout="wide")

def print_graphs(df, PITCH_ORDER):
    
    col1, col2 = st.columns(2)
    
    with col1:
        pitchbreak(df, PITCH_ORDER)
    with col2:
        releasepoint(df, PITCH_ORDER)
        
def pitchbreak(df, PITCH_ORDER):
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x='HorzBreak', y='InducedVertBreak', hue='TaggedPitchType', hue_order=PITCH_ORDER, clip_on=False, ax=ax)
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
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.)    
    st.pyplot(fig)
    
def releasepoint(df, PITCH_ORDER):
    fig, ax = plt.subplots(figsize=(6,6))
    sns.scatterplot(data=df, x="RelSidei", y="RelHeighti", hue="TaggedPitchType", hue_order=PITCH_ORDER, ax=ax)
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
    ax.legend(new_handles, new_labels, bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.)    
    st.pyplot(fig)

data = pd.read_csv("data/Fall25Scrim(updated).csv")
df = data[data["PitcherTeam"] == "RHO_RAM"]
df["Pitcher"] = df["Pitcher"].replace("Grotyohann, Connor ", "Grotyohann, Connor")
df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12
PITCH_ORDER = list(df["TaggedPitchType"].unique())

df_sorted = df.sort_values("Pitcher")
total = ["TOTAL"]
names = list(df_sorted["Pitcher"].unique())

choices = total + names

col1, col2, col3 = st.columns([1,3,1])
with col2:
    options = st.selectbox("Pitchers", options=choices)

col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col3:
    st.header(options)
    
if options == "TOTAL":
    new_df = df
else:
    new_df = df[df["Pitcher"] == options]
        
print_graphs(new_df, PITCH_ORDER)


        
        
        
        
        
        