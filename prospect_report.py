# Imports
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import numpy as np

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

x1,x2,x3 = st.columns([1,2,1])

with x2:
    # Create a list of all unique pitchers in dataframe for users to select from
    names = list(data["Pitcher"].unique())

    # Create selectbox where user can select pitcher they want to analyze
    pitcher = st.selectbox("Choose a Pitcher", options=names)


# Allow users to input name/date
pitcher_display = st.text_input("Prospect Report for", value=pitcher)
st.markdown(f"<div style='margin-top: {200}px;'></div>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center;'>Prospect Report for {pitcher_display}</h2>", unsafe_allow_html=True)

# Once pitcher is selected, we filter the dataframe so ONLY that pitcher's pitches are included
df = data[data["Pitcher"] == pitcher]

# Creating column that converts Release Side/Height to inches, to be used for Release Point Chart
df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12

# Creates three equal-sized columns for our top 3 charts
c1, c2, c3 = st.columns([1,1,1])

# Maps colors to pitch types, so they are consistent across all plots
colors = {"Fastball": "red", "Slider": "blue", "Curveball": "green", "ChangeUp": "orange",
          "Sinker": "brown", "Cutter": "gray", "Splitter": "purple"}

pitch_types = ["Fastball", "Slider", "ChangeUp", "Curveball", "Cutter", "Sinker", "Splitter"]

############## INTERACTIVE PITCH CHARTS

###### RELEASE POINT CHART

with c1:

    # Initialize plot
    fig3 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig3.add_trace(go.Scatter(

            # Release Side (inches) on x-axis, Release Height (inches) on y-axis
            x=group["RelSidei"],
            y=group["RelHeighti"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plot
            marker=dict(size=8, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig3.update_layout(

        # Add titles
        title="Release Point Chart",
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
            if st.button("Delete Selected"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()


###### PITCH BREAK CHART

with c2:

    # Initializes empty plot
    fig1 = go.Figure()

    # Iterates over each pitch, grouped by pitch type, and performs the following
    for pitch, group in df.groupby("TaggedPitchType"):

        # for each pitch type group, adds a new scatter plot layer to the figure with:
        fig1.add_trace(go.Scatter(

            # Horizontal Break on x-axis, Induced Vertical Break on y-axis
            x=group["HorzBreak"],
            y=group["InducedVertBreak"],
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
        title="Pitch Break Chart",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",

        # Set size to fit embedded app on website - make sure it appears square
        width=550,
        height=500,
        autosize=False,

        # Set axes
        xaxis=dict(range=[-25, 25], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(range=[-25, 25], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
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
        new_type = st.selectbox("Reclassify all selected as:", pitch_types)

        # Giving users the option to change the pitch type of selected points, or delete them entirely
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Change"):
                for idx in selected_indices:\
                    # Reassigns selected pitches to selected pitch type
                    st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                # This line essentially refreshes the dataset across the whole app, everything that is affected by this change will be updated
                st.rerun()
        with col2:
            if st.button("Delete Selected"):
                # Deletes selected pitches
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()


###### PITCH LOCATION CHART

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
            marker=dict(size=8, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig4.update_layout(

        # Add titles
        title="Pitch Location Chart",
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
    fig4.add_shape(type="line", x0=-0.75, x1=-0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=0.75, x1=0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=-0.25, x1=-0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=0.25, x1=0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=3.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=1.65, y1=1.65, line=dict(color="black", width=2))
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
        new_type = st.selectbox("Reclassify all selected as:", pitch_types)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Change"):
                for idx in selected_indices:
                    st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                st.rerun()
        with col2:
            if st.button("Delete Selected"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()


############## STUFF TABLE

# Control the size of the table
g1,g2, g3 = st.columns([15,1,13])

with g1:

    # Table header
    st.text("STUFF TABLE")

    table = df.groupby("TaggedPitchType").agg(
        Count = ("TaggedPitchType", "count"),
        Max_Velo = ("RelSpeed", "max"),
        Avg_Velo = ("RelSpeed", "mean"),
        IVB = ("InducedVertBreak", "mean"),
        HB = ("HorzBreak", "mean"),
        SpinRate = ("SpinRate", "mean"),
        VAA = ("VertApprAngle", "mean"),
        HAA = ("HorzApprAngle", "mean"),
        Horz_Rel = ("RelSide", "mean"),
        Vert_Rel = ("RelHeight", "mean"),
        Extension = ("Extension", "mean"),
    ).reset_index()

    total = table["Count"].sum()

    table.rename(columns={"TaggedPitchType": "Pitch Type"}, inplace=True)
    table["# Thrown"] = table["Count"]
    table["Max Velo"] = round(table["Max_Velo"], 1)
    table["Avg Velo"] = round(table["Avg_Velo"], 1)
    table["IVB"] = round(table["IVB"], 1)
    table["HB"] = round(table["HB"], 1)
    table["Spin Rate"] = round(table["SpinRate"])
    table["VAA"] = round(table["VAA"], 1)
    table["HAA"] = round(table["HAA"], 1)
    table["Vert Rel"] = round(table["Vert_Rel"], 1)
    table["Horz Rel"] = round(table["Horz_Rel"], 1)
    table["Extension"] = round(table["Extension"], 1)

    table = table[["Pitch Type", "# Thrown", "Max Velo", "Avg Velo", "IVB", "HB", "Spin Rate", "VAA", "HAA", "Vert Rel", "Horz Rel", "Extension"]].sort_values("# Thrown", ascending=False)
        
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
                ((x["PlateLocHeight"] >= 1.65) & (x["PlateLocHeight"] <= 3.65)) & 
                ((x["PlateLocSide"] >= -0.75) & (x["PlateLocSide"] <= 0.75))
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
        
        dfx["Pitch Type"] = pitch
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
        dff = dfn[["Pitch Type", "Pitch %", "Strike %", "Zone %", "Swing %", "Contact %", "CS %", "Whiff %", "CSW %", "Avg EV"]]
    
        types2.append(dff)
        
    perfs = pd.concat(types2, ignore_index=True)
    perfs = perfs.sort_values("Pitch %", ascending=False)
    
    st.dataframe(perfs, hide_index=True, use_container_width=True, height=(len(perfs) + 1) * 35 + 3)


