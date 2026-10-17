# Imports
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import pickle
import numpy as np
import duckdb
import glob
MODELS_CACHE = {}

# Makes it so app takes up full page
st.set_page_config(layout="wide")

# Allows scrolling on app
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

# Create function to calculate arm angle based on pitcher height and release point
def arm_angle(release_pos_x, release_pos_z, height_in):

    # # Inches -> Feet
    shoulder_z = 0.7 * height_in / 12   
    opp = release_pos_z - shoulder_z

    # h]Handles LHP/RHP sign
    adj = np.abs(release_pos_x)                    
    return np.degrees(np.arctan2(opp, adj))

# Refresh button: reloads the CSVs from the folder, clearing any edits
if st.button("Refresh"):
    st.session_state.pop("data", None)
    st.rerun()

# Load data once per session
if "data" not in st.session_state:

    # Read and filter files
    raw = pd.concat([pd.read_csv(f) for f in glob.glob("data/Fall26/*.csv")], ignore_index=True)
    raw = raw[raw["PitcherTeam"] == "RHO_RAM"].reset_index(drop=True)

    # Assign heights and calculate arm angle
    heights = pd.read_csv("data/pitcher_heights.csv")
    raw["height_in"] = raw["Pitcher"].map(heights.set_index("Pitcher")["height_in"])
    raw["arm_angle"] = arm_angle(raw["RelSide"], raw["RelHeight"], raw["height_in"])

    # Drop pitches missing any required values
    required_cols = ["RelSpeed", "SpinRate", "RelHeight", "RelSide", "Extension",
                     "InducedVertBreak", "HorzBreak", "TaggedPitchType",
                     "PitcherThrows", "BatterSide", "height_in"]
    raw = raw.dropna(subset=required_cols).reset_index(drop=True)

    st.session_state.data = raw

# Assign session data to variable
data = st.session_state.data



### THIS SECTION CALCULATES STUFF+ FOR EACH PITCH

# Remaps pitch type column to match what is used in our modeling, makes sure each pitch we are using falls into these buckets
data["TaggedPitchType"] = data["TaggedPitchType"].replace({
        "Fastball": "FA",
        "FourSeamFastBall": "FA",
        "Slider": "SL",
        "Sweeper": "ST",
        "Curveball": "CU",
        "ChangeUp": "CH",
        "Sinker": "SI",
        "TwoSeamFastBall": "SI",
        "Cutter": "FC",
        "Splitter": "FS"
    })
valid_pitch_types = ["FA", "SI", "FC", "CH", "FS", "SL", "ST", "CU"]
data = data[data["TaggedPitchType"].isin(valid_pitch_types)]

# Renames features to match what is used in Stuff models
data = data.rename(columns={
    "RelSpeed": "releaseVelocity",
    "SpinRate": "spinRate",
    "RelHeight": "relZ",
    "RelSide": "relX",
    "Extension": "extension",
    "InducedVertBreak": "inducedVertBreak",
    "HorzBreak": "horzBreak",
})

# Initializes and populates pitchBucket column, to identify Stuff+ which model will be used for each pitch
data["pitchBucket"] = None
data.loc[data["TaggedPitchType"].isin(["FA", "SI"]), "pitchBucket"] = "FB"
data.loc[data["TaggedPitchType"].isin(["FC"]), "pitchBucket"] = "FC"
data.loc[data["TaggedPitchType"].isin(["CH", "FS"]), "pitchBucket"] = "OFF"
data.loc[data["TaggedPitchType"].isin(["SL", "ST", "CU"]), "pitchBucket"] = "BB"

# Initialize and populate phand column (1 if Right, 0 if Left)
data["phand"] = np.nan
data.loc[data["PitcherThrows"] == "Right", "phand"] = 1
data.loc[data["PitcherThrows"] == "Left", "phand"] = 0

# Initialize and populate bhand column (1 if Right, 0 if Left)
data["bhand"] = np.nan
data.loc[data["BatterSide"] == "Right", "bhand"] = 1
data.loc[data["BatterSide"] == "Left", "bhand"] = 0

# Create fastball velo column, which takes the average velo for a pitcher's FF, SI, and FC - to be used as feature for Breaking Ball and Offspeed models
fb_velo = (
    data[data["TaggedPitchType"].isin(["FA", "SI", "FC"])]
    .groupby(["PitcherId"])["releaseVelocity"]
    .mean()
    .reset_index(name="fb_velo")
)
# Merge fastball velos
orig_index = data.index
data = data.merge(fb_velo, on=["PitcherId"], how="left")
data.index = orig_index

# load_model() function simply chooses and loads which model should be used for each pitch, then adds it to cache
def load_model(pitch):
    key = pitch
    if key not in MODELS_CACHE:
        with open(f'pitch_modeling/stuff/2026/models/stuff_{pitch}.pkl', 'rb') as f:
            MODELS_CACHE[key] = pickle.load(f)
    return MODELS_CACHE[key]

# Define features for fastballs, sinkers, and cutters
fb_features = ["releaseVelocity", "inducedVertBreak", "horzBreak", "spinRate", "relX", "relZ", "extension", "phand", "bhand"]
# Define features for non-fastballs
non_fb_features = fb_features + ["fb_velo"]

# Initialize xRV column
data["xRV"] = np.nan

# Predicting xRV for each pitch in df - one predict() call per pitchBucket 
for pitch, group in data.groupby("pitchBucket"):
    features = fb_features if pitch in ("FB", "FC") else non_fb_features
    model = load_model(pitch)
    preds = model.predict(group[features])
    data.loc[group.index, "xRV"] = preds

# Calculating Stuff+ for each pitch in df - uses population mean and standard deviations of xRV in test sample (see `pitch_modeling/stuff/2026/stuff_2026.ipynb`)
for ptype in ["FA", "SI", "FC", "CH", "FS", "SL", "ST", "CU"]:
    
    # Use SQL to get mean and std of xRV values per pitch type
    result = duckdb.sql(
        "SELECT AVG(xRV) AS pop_mean, STDDEV_POP(xRV) AS pop_std FROM 'pitch_modeling/stuff/2026/stuff_26.parquet' WHERE pitchType = ?",
        params=[ptype]
    ).df()
    pop_mean = result["pop_mean"].iloc[0]
    pop_std = result["pop_std"].iloc[0]

    # Scale df values to Stuff+ standard
    data.loc[data["TaggedPitchType"] == ptype, "Stuff+"] = round(100 + (-10 * (data["xRV"] - pop_mean) / pop_std))

### END OF STUFF+ CALCULAION SECTION









############## INTERACTIVE PITCH PLOTS

# In this section we create and plot both of the interactive pitch charts that appear on the page

x1,x2,x3,x4 = st.columns([4,6,2,4])

# Since we are using x2, we use a column that will print to 2/4, or half of the page
with x2:
    # Create a list of all unique pitchers in dataframe for users to select from
    names = list(data["Pitcher"].unique())

    # Create selectbox where user can select pitcher they want to analyze
    pitcher = st.selectbox("Choose a Pitcher", options=names)

    # Once pitcher is selected, we filter the dataframe so ONLY that pitcher's pitches are included
    df = data[data["Pitcher"] == pitcher].copy()

with x3:
    # Build list for date selections
    alld = ["TOTAL"]
    dates = list(df["Date"].dropna().unique())
    choices = alld + dates

    # User date selection
    date = st.selectbox("Date", options=choices)

    # Create subset of df based on date selected
    if date == "TOTAL":
        df = df
    else:
        df = df[df["Date"] == date]

# Creating column that converts Release Side/Height to inches, to be used for Release Point Chart
df["relXi"] = df["relX"] * 12
df["relZi"] = df["relZ"] * 12

# Maps colors to pitch types, so they are consistent across all plots
colors = {"FA": "red", "SL": "blue", "CU": "green", "CH": "orange",
          "SI": "saddlebrown", "FC": "gray", "FS": "purple", "ST": "lightblue"}

# Creates columns for plots
c0, c1, c2, c3, c4 = st.columns([1,4,1,4,1])





###### RELEASE POINT PLOT

# The first chart will be our Release Point Chart, which will appear in the upper left section of the pitch plots

with c1:

    # Initialize plot
    fig1 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig1.add_trace(go.Scatter(

            # Release Side (inches) on x-axis, Release Height (inches) on y-axis
            x=group["relXi"],
            y=group["relZi"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plot
            marker=dict(size=12, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig1.update_layout(

        # Add titles
        title="Release Point Plot",
        xaxis_title="Release Side (in)",
        yaxis_title="Release Height (in)",

        # Set size to fit embedded app on website - make sure it appears square
        width=800,
        height=650,
        autosize=False,

        # Set axes range
        xaxis=dict(range=[-48, 48], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(range=[0, 96], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
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

    # Show plot with key "rel_plot"
    event1 = st.plotly_chart(fig1, on_select="rerun", key="rel_plot", use_container_width=False)

    # When pitches are selected
    if event1 and event1.selection and event1.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event1.selection.points]

        # Users can only delete pitches on this plot, not reassign their pitch type
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Selected", key="delete_relplot"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()








###### PITCH BREAK PLOT

# The next chart we develop will be our standard Pitch Break Chart, which will appear in the upper middle section of the pitch plots

with c3:

    # Initializes empty plot
    fig2 = go.Figure()

    # Arm side direction: RHP arm side is +HB, LHP arm side is -HB
    arm_side = 1 if df["PitcherThrows"].iloc[0] == "Right" else -1
    L = 30

    # Iterates over each pitch, grouped by pitch type, and performs the following
    for pitch, group in df.groupby("TaggedPitchType"):

        # Get color for this pitch
        color = colors.get(pitch, "black")

        # Average arm angle grouped by pitch type
        theta = np.radians(group["arm_angle"].mean())

        # Mean arm angle line from the origin
        fig2.add_trace(go.Scatter(

            # Plot line at arm angle
            x=[0, arm_side * L * np.cos(theta)],
            y=[0, L * np.sin(theta)],
            mode="lines",

            # Line color correlates with pitch type
            line=dict(color=color, width=5, dash="solid"),
            opacity=0.4,
            
            legendgroup=pitch,      
            showlegend=False,
            hoverinfo="skip",      
        ))

        # Build hover message
        hover_message = (
            pitch
            + "<br>Velo: " + group["releaseVelocity"].round(1).astype(str) + " mph"
            + "<br>Spin: " + group["spinRate"].round(0).astype(int).astype(str) + " rpm"
            + "<br>IVB: " + group["inducedVertBreak"].round(1).astype(str) + " in"
            + "<br>HB: " + group["horzBreak"].round(1).astype(str) + " in"
            + "<br>Stuff+: " + group["Stuff+"].astype(int).astype(str)
        )

        # for each pitch type group, adds a new scatter plot layer to the figure with:
        fig2.add_trace(go.Scatter(

            # Horizontal Break on x-axis, Induced Vertical Break on y-axis
            x=group["horzBreak"],
            y=group["inducedVertBreak"],
            mode="markers",

            # Labels each dot as their respective pitch type
            name=pitch,

            # Styles each dot to size 8, and the color is based on correlating pitch type color that we mapped earlier
            marker=dict(
                size=12,
                color=color,
                opacity=0.8,                            # slight transparency
                line=dict(color="black", width=0.75),   # thin border
            ),

            # Attaches dataframe row indeces to each point, will be helpful for click interactions later on
            customdata=group.index.tolist(),

            # Assign text as hover template, adjust its style
            text=hover_message,
            hovertemplate="%{text}<extra></extra>",
            hoverlabel=dict(
                font=dict(size=14, color="black"),  # text size and font
                bgcolor="white",                                   # background color
                bordercolor="black",                               # border color
                align="left",                                      # text alignment inside the box
            ),
        ))


    fig2.update_layout(

        # Add titles
        title="Pitch Break Plot",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",

        # Set size to fit embedded app on website - make sure it appears square
        width=800,
        height=650,
        autosize=False,

        # Set axes
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

    # Show the plot on app
    # Every plot has to have its own unique key, this one is "plot1"
    event2 = st.plotly_chart(fig2, on_select="rerun", key="plot1", use_container_width=False)

    # For when point(s) on the plot are selected
    if event2 and event2.selection and event2.selection.points:
        # The selected point(s)
        selected_indices = [int(pt["customdata"]) for pt in event2.selection.points]

        # Display number of pitches selected
        st.markdown(f"**{len(selected_indices)} pitches selected**")

        # Present pitch type options for reclassification
        new_type = st.selectbox("Reclassify all selected as:", valid_pitch_types, key="reclass_breakplot")

        # Giving users the option to change the pitch type of selected points, or delete them entirely
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Change", key="apply_breakplot"):
                for idx in selected_indices:
                    # Reassigns selected pitches to selected pitch type
                    st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                # This line essentially refreshes the dataset across the whole app, everything that is affected by this change will be updated
                st.rerun()
        with col2:
            if st.button("Delete Selected", key="delete_breakplot"):
                # Deletes selected pitches
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()








############## STUFF TABLE

# Control the size of the table
g1,g2, g3 = st.columns([1,4,1])

with g2:

    # Table header
    st.text("STUFF TABLE")

    table = df.groupby("TaggedPitchType").agg(
        Count = ("TaggedPitchType", "count"),
        Max_Velo = ("releaseVelocity", "max"),
        Avg_Velo = ("releaseVelocity", "mean"),
        IVB = ("inducedVertBreak", "mean"),
        HB = ("horzBreak", "mean"),
        SpinRate = ("spinRate", "mean"),
        Vert_Rel = ("relZ", "mean"),
        Horz_Rel = ("relX", "mean"),
        Extension = ("extension", "mean"),
        Arm_Angle = ("arm_angle", "mean"),
        xrv = ("xRV", "mean")
    ).reset_index()

    total = table["Count"].sum()

    table.rename(columns={"TaggedPitchType": "PitchType"}, inplace=True)
    table["Pitch %"] = round((table["Count"] / total) * 100, 1)
    table["Max_Velo"] = round(table["Max_Velo"], 1)
    table["Avg_Velo"] = round(table["Avg_Velo"], 1)
    table["IVB"] = round(table["IVB"], 1)
    table["HB"] = round(table["HB"], 1)
    table["SpinRate"] = round(table["SpinRate"])
    table["Horz_Rel"] = round(table["Horz_Rel"], 1)
    table["Vert_Rel"] = round(table["Vert_Rel"], 1)
    table["Extension"] = round(table["Extension"], 1)
    table["Arm_Angle"] = round(table["Arm_Angle"])

    col = table.pop("Pitch %")
    table.insert(2, "Pitch %", col)

    table["Stuff+"] = np.nan

    rows = []
    for index, row in table.iterrows():
        ptype = row["PitchType"]
        if ptype in ["FA", "SI", "FC", "CH", "FS", "SL", "ST", "CU"]:
            result = duckdb.sql(
            "SELECT AVG(xRV) AS pop_mean, STDDEV_POP(xRV) AS pop_std FROM 'pitch_modeling/stuff/2026/stuff_26.parquet' WHERE pitchType = ?",
                params=[ptype]
            ).df()
            pop_mean = result["pop_mean"].iloc[0]
            pop_std = result["pop_std"].iloc[0]
    
            row["Stuff+"] = round(100 + (-10 * (row["xrv"] - pop_mean) / pop_std))
            rows.append(row)

    table = pd.concat(rows, axis=1, ignore_index=True).T

    table.drop(columns=["xrv"], inplace=True)

    table = table.sort_values("Pitch %", ascending=False)
        
    st.dataframe(table, hide_index=True, use_container_width=True, height=(len(table) + 1) * 35 + 3)


    