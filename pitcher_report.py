# Imports
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import pickle
import numpy as np
import duckdb
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

# File upload - allows for multiple csv files to be uploaded at once
files = st.file_uploader("Import Trackman file", type="csv", accept_multiple_files=True)

# If user clicks "Refresh" button, data resets. Essentially, any changes made in file upload will be updated -- File(s) added/removed will now be updated
if st.button("Refresh"):
    del st.session_state.data
    st.session_state.file_key = st.session_state.get("file_key", 0) + 1 
    st.rerun()

# Concatenates all csv files uploaded
if files and "data" not in st.session_state:
    dfs = [pd.read_csv(f) for f in files]
    st.session_state.data = pd.concat(dfs, ignore_index=True)

# Message for if there are no csv files uploaded
if "data" not in st.session_state:
    st.info("Please upload a CSV to get started.")
    st.stop()

# Assigns concatenated csv files to variable
data = st.session_state.data

# Remaps pitch type column to match what is used in our modeling
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





############## INTERACTIVE PITCH PLOTS

# In this section we create and plot all 5 of the interactive pitch charts that appear on the page

# This is an example of creating streamlit columns, which essentially allows us to control the size of everything that is produced relative to the width of the page
# For a column of size x, that column will take up x / sum(cols) percent of the page
# In this instance, we create 3 columns. The sizes (in this case [1,2,1]), creates columns of those proportions, whose sum is the width of the full page.
x1,x2,x3 = st.columns([1,2,1])

# Since we are using x2, we use a column that will print to 2/4, or half of the page
with x2:
    # Create a list of all unique pitchers in dataframe for users to select from
    names = list(data["Pitcher"].unique())

    # Create selectbox where user can select pitcher they want to analyze
    pitcher = st.selectbox("Choose a Pitcher", options=names)

# Once pitcher is selected, we filter the dataframe so ONLY that pitcher's pitches are included
df = data[data["Pitcher"] == pitcher]

# Filter df so it only includes pitches that we have models developed for
pitch_types = ["FA", "SL", "CH", "CU", "FC", "SI", "ST", "FS"]
#df = df[df["TaggedPitchType"].isin(pitch_types)]

# Creating column that converts Release Side/Height to inches, to be used for Release Point Chart
df["relXi"] = df["relX"] * 12
df["relZi"] = df["relZ"] * 12

# Maps colors to pitch types, so they are consistent across all plots
colors = {"FA": "red", "SL": "blue", "CU": "green", "CH": "orange",
          "SI": "brown", "FC": "gray", "FS": "purple", "ST": "lightblue"}

# Creates three equal-sized columns for our top 3 charts
c1, c2, c3 = st.columns([1,1,1])



###### RELEASE POINT PLOT

# The first chart will be our Release Point Chart, which will appear in the upper left section of the pitch plots

with c1:

    # Initialize plot
    fig3 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig3.add_trace(go.Scatter(

            # Release Side (inches) on x-axis, Release Height (inches) on y-axis
            x=group["relXi"],
            y=group["relZi"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plot
            marker=dict(size=8, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig3.update_layout(

        # Add titles
        title="Release Point Plot",
        xaxis_title="Release Side (in)",
        yaxis_title="Release Height (in)",

        # Set size to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
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
    event3 = st.plotly_chart(fig3, on_select="rerun", key="rel_plot", use_container_width=False)

    # When pitches are selected
    if event3 and event3.selection and event3.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event3.selection.points]

        # Users can only delete pitches on this plot, not reassign their pitch type
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Selected", key="delete_relplot"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()



###### PITCH BREAK PLOT

# The next chart we develop will be our standard Pitch Break Chart, which will appear in the upper middle section of the pitch plots

with c2:

    # Initializes empty plot
    fig1 = go.Figure()

    # Iterates over each pitch, grouped by pitch type, and performs the following
    for pitch, group in df.groupby("TaggedPitchType"):

        # for each pitch type group, adds a new scatter plot layer to the figure with:
        fig1.add_trace(go.Scatter(

            # Horizontal Break on x-axis, Induced Vertical Break on y-axis
            x=group["horzBreak"],
            y=group["inducedVertBreak"],
            mode="markers",

            # Labels each dot as their respective pitch type
            name=pitch,

            # Styles each dot to size 8, and the color is based on correlating pitch type color that we mapped earlier
            marker=dict(size=8, color=colors.get(pitch, "black")),

            # Attaches dataframe row indeces to each point, will be helpful for click interactions later on
            customdata=group.index.tolist(),
        ))

    fig1.update_layout(

        # Add titles
        title="Pitch Break Plot",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",

        # Set size to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
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
    event1 = st.plotly_chart(fig1, on_select="rerun", key="plot1", use_container_width=False)

    # For when point(s) on the plot are selected
    if event1 and event1.selection and event1.selection.points:
        # The selected point(s)
        selected_indices = [int(pt["customdata"]) for pt in event1.selection.points]

        # Display number of pitches selected
        st.markdown(f"**{len(selected_indices)} pitches selected**")

        # Present pitch type options for reclassification
        new_type = st.selectbox("Reclassify all selected as:", pitch_types, key="reclass_breakplot")

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


###### PITCH LOCATION Plot

# The next chart will be our Pitch Location Plot, which will appear in the upper right section of the pitch plots
    
with c3:

    # Initialize plot
    fig4 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig4.add_trace(go.Scatter(

            # Plate Location Side (ft) on x-axis, Plate Location Height (feet) on y-axis
            x=group["PlateLocSide"],
            y=group["PlateLocHeight"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plots
            marker=dict(size=10, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig4.update_layout(

        # Add titles
        title="Pitch Location Plot (Catcher's Perspective)",
        xaxis_title="Plate Location Side (ft)",
        yaxis_title="Plate Location Height (ft)",

        # Set size to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
        autosize=False,

        # Set axes
        xaxis=dict(range=[-3, 3], showgrid=False, zeroline=False, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(range=[-1, 6], showgrid=False, zeroline=False, zerolinecolor="black", zerolinewidth=2),
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

    # Add lines to visualize strike zone on the plot
    fig4.add_shape(type="line", x0=-0.75, x1=-0.75, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=0.75, x1=0.75, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.25, x1=-0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=0.25, x1=0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=3.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=1.65, y1=1.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.32, y1=2.32, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.99, y1=2.99, line=dict(color="black", width=1))

    # Display plot with key "loc_plot"
    event4 = st.plotly_chart(fig4, on_select="rerun", key="loc_plot", use_container_width=False)

    # When pitch(es) are selected
    if event4 and event4.selection and event4.selection.points:

        # Give users the option between reassigning pitch types or deleting selected pitches
        
        selected_indices = [int(pt["customdata"]) for pt in event4.selection.points]

        st.markdown(f"**{len(selected_indices)} pitches selected**")

        # Present pitch type options for reclassification
        new_type = st.selectbox("Reclassify all selected as:", pitch_types, key="reclass_locplot")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Change", key="apply_locplot"):
                for idx in selected_indices:
                    st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                st.rerun()
        with col2:
            if st.button("Delete Selected", key="delete_locplot"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()

# Give users option to toggle whether the bottom 2 graphs show or not
show = st.toggle("Show more plots", value=True)

# Align page so our 2 charts will be centered on the screen
co1, co2, co3, co4, co5 = st.columns([1,3,1,3,1])

###### SPEED / SPIN PLOT

# This will be our speed/spin plot, which will be the plot on the bottom left

with co2:

    # Initialize plot
    fig2 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig2.add_trace(go.Scatter(
            # Spin Rate (rpm) on x-axis, Release Speed (mph) on y-axis
            x=group["spinRate"],
            y=group["releaseVelocity"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plots
            marker=dict(size=8, color=colors.get(pitch, "black")),
            customdata=group.index.tolist(),
        ))

    fig2.update_layout(

        # Set titles/labels
        title="Speed / Spin Plot",
        xaxis_title="Spin Rate",
        yaxis_title="Release Speed",

        # Customize height to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
        autosize=False,

        # Set axes, use autorange=True to make it so the plot automatically adjusts to the min/max values on each axis
        xaxis=dict(range=[0, 3000], autorange=True,),
        yaxis=dict(range=[60, 110], autorange=True,),
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

    # Only display plot if "show" is selected
    if show:
        # Show plot with key "pitch_plot"
        event2 = st.plotly_chart(fig2, on_select="rerun", key="pitch_plot", use_container_width=False)

        # When pitch(es) are selected
        if event2 and event2.selection and event2.selection.points:
    
            # Give users the option between reassigning pitch types or deleting selected pitches
            
            selected_indices = [int(pt["customdata"]) for pt in event2.selection.points]
    
            st.markdown(f"**{len(selected_indices)} pitches selected**")
    
            # Present pitch type options for reclassification
            new_type = st.selectbox("Reclassify all selected as:", pitch_types, key="reclass_ssplot")
    
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Apply Change", "apply_ssplot"):
                    for idx in selected_indices:
                        st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                    st.rerun()
            with col2:
                if st.button("Delete Selected", key="delete_ssplot"):
                    st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                    st.rerun()


###### STUFF PLUS PLOT

# This will be our Stuff+ on Pitch Break plot, which will be the plot on the bottom right

# Only display selectbox if "show" is selected
if show:
# Use middle column for pitch type selection
    with co3:
    
        # Give user option to select pitch type to display on Stuff+ plot
        pitches = list(df["TaggedPitchType"].unique())
        pitch = st.selectbox("Choose a Pitch", options=pitches)
        df_p = df[df["TaggedPitchType"] == pitch]

# Set df_p manually if not showing (prevents errors going forward)
else:
    df_p = df[df["TaggedPitchType"] == "FA"]

with co4:

    # Initialize figure
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(

        # Horizontal Break (in) on x-axis, Induced Vertical Break (in) on y-axis
        x=df_p["horzBreak"],
        y=df_p["inducedVertBreak"],
        mode="markers",

        # This dictates the color of each plot, it is based on its Stuff+ value on a red/yellow/green scale. Yellow is average (Stuff+ = 100)
        marker=dict(
            size=8,
            color=df_p["Stuff+"],        
            colorscale="RdYlGn",         
            cmin=70,                     
            cmax=130,                    
            colorbar=dict(title="Stuff+"),
            opacity=1
        ),
        customdata=df_p["Stuff+"].tolist(),

        # Display Stuff+ value of pitch when it is hovered over
        hovertemplate="Stuff+: %{customdata:.0f}<extra></extra>",
    ))
    
    fig5.update_layout(

        # Set titles/labels
        title="Stuff+ On Pitch Break Plot",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",

        # Adjust size to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
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

    # Only display plot if "show" is selected
    if show:
        # Display plot with key "stuff_plot"
        event5 = st.plotly_chart(fig5, on_select="rerun", key="stuff_plot", use_container_width=False)

    # NOTE: This plot does not provide users an option to delete pitches or reassign pitch types




# It is now time to create our tables that appear below all of the plots

############## STUFF TABLE

# We will first create our Stuff table, which displays a variety of metrics for each pitch type that pitcher throws

# Control the size of the table
g1,g2, g3 = st.columns([15,1,13])

with g1:

    # Table header
    st.text("STUFF TABLE")

    table = df.groupby("TaggedPitchType").agg(
        Count = ("TaggedPitchType", "count"),
        Max_Velo = ("releaseVelocity", "max"),
        Avg_Velo = ("releaseVelocity", "mean"),
        IVB = ("inducedVertBreak", "mean"),
        HB = ("horzBreak", "mean"),
        Horz_Rel = ("relX", "mean"),
        Vert_Rel = ("relZ", "mean"),
        SpinRate = ("spinRate", "mean"),
        Extension = ("extension", "mean"),
        xrv = ("xRV", "mean")
    ).reset_index()

    total = table["Count"].sum()

    table.rename(columns={"TaggedPitchType": "PitchType"}, inplace=True)
    table["Pitch %"] = round((table["Count"] / total) * 100, 1)
    table["Max_Velo"] = round(table["Max_Velo"], 1)
    table["Avg_Velo"] = round(table["Avg_Velo"], 1)
    table["IVB"] = round(table["IVB"], 1)
    table["HB"] = round(table["HB"], 1)
    table["Horz_Rel"] = round(table["Horz_Rel"], 1)
    table["Vert_Rel"] = round(table["Vert_Rel"], 1)
    table["SpinRate"] = round(table["SpinRate"])
    table["Extension"] = round(table["Extension"], 1)

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

############## PERFORMANCE TABLE

with g3:
    st.text("PERFORMANCE TABLE")
    pitches = list(df["TaggedPitchType"].unique())
    pitches.append("Total")   
    
    types2 = []
    
    for pitch in pitches:
        dfx = {}
        if pitch != "Total":
            x = df[df["TaggedPitchType"] == pitch]
        else:
            x = df
            
        zone = (
                ((x["PlateLocHeight"] > 1.41) & (x["PlateLocHeight"] < 3.89)) & 
                ((x["PlateLocSide"] > -0.99) & (x["PlateLocSide"] < 0.99))
            )
        swing = (
                (x["PitchCall"] == "InPlay") |
                (x["PitchCall"] == "StrikeSwinging") |
                (x["PitchCall"] == "FoulBallNotFieldable") |
                (x["PitchCall"] == "FoulBallFieldable")
            )
        csw = (
                (x["PitchCall"] == "StrikeSwinging") |
                (x["PitchCall"] == "StrikeCalled")
            )
        xz = x[zone]
        xs = x[swing]
        xcsw = x[csw]
        contact = (
                (x["PitchCall"] == "InPlay") |
                (x["PitchCall"] == "FoulBallNotFieldable") |
                (x["PitchCall"] == "FoulBallFieldable")
            )
        xc = x[contact]
        
        dfx["PitchType"] = pitch
        if pitch != "Total":
            dfx["Pitch %"] = round((len(x) / len(df)) * 100, 1)
        else:
            dfx["Pitch %"] = np.nan
        dfx["Strikes"] = len(x[(x["PitchCall"] == "StrikeCalled") | (x["PitchCall"] == "StrikeSwinging") | (x["PitchCall"] == "FoulBallNotFieldable") | (x["PitchCall"] == "InPlay")])
        if len(x) != 0:
            dfx["Strike %"] = round((dfx["Strikes"] / len(x)) * 100, 1)
            dfx["Zone %"] = round(((len(xz) / len(x)) * 100), 1)
            dfx["Swing %"] = round(((len(xs) / len(x)) * 100), 1)
            if len(xs) != 0:
                dfx["Contact %"] = round(((len(xc) / len(xs)) * 100), 1)
            else:
                dfx["Contact %"] = np.nan
            dfx["CS %"] = round(((len(x[x["PitchCall"] == "StrikeCalled"]) / len(x)) * 100), 1)
            if len(xs) != 0:
                dfx["Whiff %"] = round(((len(xs[xs["PitchCall"] == "StrikeSwinging"]) / len(xs)) * 100), 1)
            else:
                dfx["Whiff %"] = np.nan
            dfx["CSW %"] = dfx["CS %"] + dfx["Whiff %"]
        else:
            dfx["Strike %"] = np.nan
            dfx["Zone %"] = np.nan
            dfx["Swing %"] = np.nan
            dfx["Contact %"] = np.nan
            dfx["CS %"] = np.nan
            dfx["Whiff %"] = np.nan
            dfx["CSW %"] = np.nan
        dfx["Avg EV"] = round(x[x["ExitSpeed"].notna()]["ExitSpeed"].mean(), 1)
    
        dfn = pd.DataFrame([dfx])
        dff = dfn[["PitchType", "Pitch %", "Strike %", "Zone %", "Swing %", "Contact %", "CS %", "Whiff %", "CSW %", "Avg EV"]]
    
        types2.append(dff)
        
    perfs = pd.concat(types2, ignore_index=True)
    perfs = perfs.sort_values("Pitch %", ascending=False)
    
    st.dataframe(perfs, hide_index=True, use_container_width=True, height=(len(perfs) + 1) * 35 + 3)

############## STATISTICS TABLE

st.text("COMPETITION TABLE")

stats = {}

stats["IP"] = round((len(df[df["KorBB"] == "Strikeout"]) + sum(df["OutsOnPlay"])) / 3, 2)
stats["Hits"] = len(df[(df["PlayResult"] == "Single") | (df["PlayResult"] == "Double") | (df["PlayResult"] == "Triple") | (df["PlayResult"] == "HomeRun")])
stats["Runs"] = sum(df["RunsScored"])
stats["K"] = len(df[df["KorBB"] == "Strikeout"])
stats["BB"] = len(df[df["KorBB"] == "Walk"])
stats["HBP"] = len(df[df["PitchCall"] == "HitByPitch"])

oneK = df[(df["Strikes"] == 1) & (df["Balls"] <= 1)]
if len(oneK) > 0:
    stats["0-2 or 1-2"] = len(oneK[(oneK["PitchCall"] == "StrikeCalled") | (oneK["PitchCall"] == "StrikeSwinging") | (oneK["PitchCall"] == "FoulBallNotFieldable")])
else: 
    stats["0-2 or 1-2"] = 0

stats["4PitchesOrLess"] = 0
for d in df["Date"].dropna().unique():
    dfd = df[df["Date"] == d]
    if not dfd.empty:
        for i in range(1, dfd["Inning"].max() + 1):
            dfi = dfd[dfd["Inning"] == i]
            if not dfi.empty:
                for p in range(1, dfi["PAofInning"].max() + 1):
                    dfip = dfi[dfi["PAofInning"] == p]
                    if (len(dfip) <= 4) & (len(dfip) >= 1):
                        stats["4PitchesOrLess"] = stats["4PitchesOrLess"] + 1

stats["IPw/0s"] = 0
for d in df["Date"].dropna().unique():
    dfd = df[df["Date"] == d]
    if not dfd.empty:
        for i in range(1, dfd["Inning"].max() + 1):
            dfi = dfd[dfd["Inning"] == i]
            if not dfi.empty:
                if sum(dfi["RunsScored"]) == 0:
                    stats["IPw/0s"] = stats["IPw/0s"] + 1

leadoff = df[df["PAofInning"] == 1]
stats["LeadoffOut"] = len(leadoff[(leadoff["KorBB"] == "Strikeout") | (leadoff["OutsOnPlay"] > 0)])

stats["123"] = 0
for d in df["Date"].dropna().unique():
    dfd = df[df["Date"] == d]
    if not dfd.empty:
        for i in range(1, dfd["Inning"].max() + 1):
            dfi = dfd[dfd["Inning"] == i]
            if not dfi.empty:
                if sum(dfi["PAofInning"].dropna().unique()) == 6:
                        stats["123"] = stats["123"] + 1

stats["LeadoffOn"] = len(leadoff[(leadoff["KorBB"] == "Walk") | (leadoff["PlayResult"] == "Single") | (leadoff["PlayResult"] == "Double") | (leadoff["PlayResult"] == "Triple") | (leadoff["PlayResult"] == "HomeRun") | (leadoff["PitchCall"] == "HitByPitch")])

stats["CompetitionScore"] = stats["0-2 or 1-2"] + stats["K"] + stats["4PitchesOrLess"] + stats["IPw/0s"] + stats["LeadoffOut"] + (2 * stats["123"]) - stats["BB"] - stats["Runs"] - stats["Hits"] - stats["HBP"] - stats["LeadoffOn"]

if stats["IP"] != 0:
    stats["CompScore/IP"] = round(stats["CompetitionScore"] / stats["IP"], 2)
elif stats["IP"] == 0:
    stats["CompScore/IP"] = np.nan

st.dataframe(pd.DataFrame([stats]), hide_index=True, use_container_width=False, height=(len(pd.DataFrame([stats])) + 1) * 35 + 3)











