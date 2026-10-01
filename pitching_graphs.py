import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import duckdb
import pickle
import numpy as np
import glob

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

MODELS_CACHE = {}

def load_model(pitch):
    key = pitch
    if key not in MODELS_CACHE:
        with open(f'pitch_modeling/stuff/2026/models/stuff_{pitch}.pkl', 'rb') as f:
            MODELS_CACHE[key] = pickle.load(f)
    return MODELS_CACHE[key]

def compute_stuff_plus(df):
    """Calculates xRV and Stuff+ for dataframes loaded in pitching_graphs."""
    df_calc = df.copy()
    
    # Map to standardized pitch codes for modeling
    pitch_map = {
        "Fastball": "FA", "FourSeamFastBall": "FA", "Slider": "SL",
        "Sweeper": "ST", "Curveball": "CU", "ChangeUp": "CH",
        "Sinker": "SI", "TwoSeamFastBall": "SI", "Cutter": "FC", "Splitter": "FS"
    }
    df_calc["modelPitchType"] = df_calc["TaggedPitchType"].map(pitch_map)
    valid_types = ["FA", "SI", "FC", "CH", "FS", "SL", "ST", "CU"]
    
    # Map feature names
    df_calc = df_calc.rename(columns={
        "RelSpeed": "releaseVelocity",
        "SpinRate": "spinRate",
        "RelHeight": "relZ",
        "RelSide": "relX",
        "Extension": "extension",
        "InducedVertBreak": "inducedVertBreak",
        "HorzBreak": "horzBreak",
    })

    df_calc["pitchBucket"] = None
    df_calc.loc[df_calc["modelPitchType"].isin(["FA", "SI"]), "pitchBucket"] = "FB"
    df_calc.loc[df_calc["modelPitchType"].isin(["FC"]), "pitchBucket"] = "FC"
    df_calc.loc[df_calc["modelPitchType"].isin(["CH", "FS"]), "pitchBucket"] = "OFF"
    df_calc.loc[df_calc["modelPitchType"].isin(["SL", "ST", "CU"]), "pitchBucket"] = "BB"

    df_calc["phand"] = np.where(df_calc["PitcherThrows"] == "Right", 1, 0)
    df_calc["bhand"] = np.where(df_calc["BatterSide"] == "Right", 1, 0)

    fb_velo = (
        df_calc[df_calc["modelPitchType"].isin(["FA", "SI", "FC"])]
        .groupby(["PitcherId"])["releaseVelocity"]
        .mean()
        .reset_index(name="fb_velo")
    )
    orig_idx = df_calc.index
    df_calc = df_calc.merge(fb_velo, on=["PitcherId"], how="left")
    df_calc.index = orig_idx

    fb_features = ["releaseVelocity", "inducedVertBreak", "horzBreak", "spinRate", "relX", "relZ", "extension", "phand", "bhand"]
    non_fb_features = fb_features + ["fb_velo"]

    df_calc["xRV"] = np.nan
    for pitch, group in df_calc.groupby("pitchBucket"):
        if group.empty or pd.isna(pitch):
            continue
        features = fb_features if pitch in ("FB", "FC") else non_fb_features
        if group[features].dropna().empty:
            continue
        model = load_model(pitch)
        preds = model.predict(group[features].fillna(0))
        df_calc.loc[group.index, "xRV"] = preds

    df["Stuff+"] = np.nan
    for ptype in valid_types:
        try:
            result = duckdb.sql(
                "SELECT AVG(xRV) AS pop_mean, STDDEV_POP(xRV) AS pop_std FROM 'pitch_modeling/stuff/2026/stuff_26.parquet' WHERE pitchType = ?",
                params=[ptype]
            ).df()
            pop_mean = result["pop_mean"].iloc[0]
            pop_std = result["pop_std"].iloc[0]
            
            mask = df_calc["modelPitchType"] == ptype
            df.loc[mask, "Stuff+"] = np.round(100 + (-10 * (df_calc.loc[mask, "xRV"] - pop_mean) / pop_std))
        except Exception:
            pass
            
    return df

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

    st.markdown("---")
    st.subheader("Stuff+ on Pitch Break Plot")
    stuff_plus_pitchbreak(df)

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
    st.pyplot(fig)

def stuff_plus_pitchbreak(df):
    """Plotly-based Stuff+ on Pitch Break Plot."""
    pitches = list(df["TaggedPitchType"].unique())
    if not pitches:
        st.info("No pitch data available for Stuff+ plot.")
        return

    col_select, col_plot = st.columns([1, 2])
    
    with col_select:
        selected_pitch = st.selectbox("Select Pitch Type for Stuff+ Plot", options=pitches, key="graph_stuff_pitch")
        df_p = df[df["TaggedPitchType"] == selected_pitch]

    with col_plot:
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=df_p["HorzBreak"],
            y=df_p["InducedVertBreak"],
            mode="markers",
            marker=dict(
                size=9,
                color=df_p["Stuff+"],        
                colorscale="RdYlGn",         
                cmin=70,                     
                cmax=130,                    
                colorbar=dict(title="Stuff+"),
                opacity=1
            ),
            customdata=df_p["Stuff+"].tolist(),
            hovertemplate="Stuff+: %{customdata:.0f}<extra></extra>",
        ))
        
        fig5.update_layout(
            title=f"Stuff+ On Pitch Break Plot ({selected_pitch})",
            xaxis_title="Horizontal Break (in)",
            yaxis_title="Induced Vertical Break (in)",
            width=550,
            height=500,
            autosize=False,
            xaxis=dict(range=[-30, 30], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
            yaxis=dict(range=[-30, 30], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=40, b=20),
            shapes=[
                dict(
                    type="rect",
                    xref="paper", yref="paper",
                    x0=0, y0=0, x1=1, y1=1,
                    line=dict(color="black", width=1)
                )
            ]
        )

        st.plotly_chart(fig5, use_container_width=False, key="stuff_plot_graph_page")

def get_outcome(df):
    outcome_map = {
        "StrikeCalled": "Strike Called",
        "StrikeSwinging": "Strike Swinging",
        "BallCalled": "Ball Called",
        "HitByPitch": "HBP",
        "InPlay": "In Play",
        "FoulBallNotFieldable": "Foul Ball Not Fieldable",
    }
    df["Outcome"] = df["PitchCall"].map(outcome_map).fillna("Other")
    return df

# Data loading
df = pd.concat([pd.read_csv(f) for f in glob.glob("data/Fall26/*.csv")], ignore_index=True)

data = df.reset_index(drop=True)
df = data[data["PitcherTeam"] == "RHO_RAM"].copy()
df["Pitcher"] = df["Pitcher"].replace("Grotyohann, Connor ", "Grotyohann, Connor")
df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12
df["Extensioni"] = df["Extension"] * 12
df.loc[df["Pitcher"] == "Kopetski, Josh", "PitcherThrows"] = "Left"

if "Stuff+" not in df.columns:
    try:
        df = compute_stuff_plus(df)
    except Exception as e:
        st.warning("Could not calculate Stuff+ automatically; please ensure model files exist in pitch_modeling/stuff/2026/.")

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
    
if options not in not_valid:
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
