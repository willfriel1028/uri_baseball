# Imports
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors as rl_colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

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

def add_letterhead(canvas, doc):
    canvas.saveState()
    
    # Small text, top-left corner
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(rl_colors.HexColor("#555555"))
    canvas.drawString(0.5 * inch, 10.5 * inch, "University of Rhode Island Baseball")
    
    # Logo image, top-right corner - vertically centered on the text's line
    logo_width, logo_height = 1 * inch, 1 * inch
    canvas.drawImage(
        "images/urilogo.png",
        letter[0] - 0.5 * inch - logo_width,  # right-aligned against the margin
        10.14 * inch,  # centers the logo on the text baseline (accounts for 8pt cap height)
        width=logo_width, height=logo_height,
        preserveAspectRatio=True, mask='auto'
    )
    
    canvas.restoreState()

def make_pdf_table(df):
    data = [list(df.columns)] + df.values.tolist()
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, rl_colors.grey),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
    ]))
    return t

def generate_pdf(stats_df, pitcher_display, table_df, perf_df, fig_rel, fig_break, fig_loc):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.9 * inch, bottomMargin=0.5 * inch
    )
    styles = getSampleStyleSheet()
    centered_heading = ParagraphStyle(
        'CenteredHeading',
        parent=styles['Heading2'],
        alignment=TA_CENTER
    )
    elements = [Spacer(1, 15), Paragraph(f"Prospect Report for {pitcher_display}", styles["Title"]), Spacer(1, 10)]

    elements.append(Paragraph("Stats", centered_heading))
    elements.append(make_pdf_table(stats_df))
    elements.append(Spacer(1, 30))

    # Usable width on a Letter page with 0.5in margins is 7.5in - split 3 ways with small gaps
    img_width, img_height = 2.45 * inch, 2.45 * inch
    chart_images = []
    for fig in [fig_rel, fig_break, fig_loc]:
        img_bytes = fig.to_image(format="png", scale=3)
        chart_images.append(Image(io.BytesIO(img_bytes), width=img_width, height=img_height))
    
    chart_row = Table([chart_images], colWidths=[img_width + 0.05 * inch] * 3)
    chart_row.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(chart_row)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Stuff Table", centered_heading))
    elements.append(make_pdf_table(table_df))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Performance Table", centered_heading))
    elements.append(make_pdf_table(perf_df))

    doc.build(elements, onFirstPage=add_letterhead, onLaterPages=add_letterhead)
    buffer.seek(0)
    return buffer

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

# Maps colors to pitch types, so they are consistent across all plots
colors = {"Fastball": "red", "Slider": "blue", "Curveball": "green", "ChangeUp": "orange",
          "Sinker": "brown", "Cutter": "gray", "Splitter": "purple"}

pitch_types = ["Fastball", "Slider", "ChangeUp", "Curveball", "Cutter", "Sinker", "Splitter"]

# Creates three equal-sized columns for our top 3 charts
c1, c2, c3 = st.columns([1,1,1])

# Determine pitcher handedness to decide which corner the inset legend goes in
pitcher_hand = df["PitcherThrows"].iloc[0] if "PitcherThrows" in df.columns and len(df) > 0 else "Right"

############## INTERACTIVE PITCH CHARTS

###### RELEASE POINT CHART

with c1:

    # Initialize plot
    fig1 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig1.add_trace(go.Scatter(

            # Release Side (inches) on x-axis, Release Height (inches) on y-axis
            x=group["RelSidei"],
            y=group["RelHeighti"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plot
            marker=dict(size=12, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig1.update_layout(

        # Add titles (centered)
        title=dict(text="<b>Release Point Chart</b>", x=0.5, xanchor="center"),

        # Portrait aspect - taller than wide, per request
        width=580,
        height=640,
        autosize=False,
        showlegend=False,

        # Set axes range - standoff pushes the axis title away from the tick numbers
        xaxis=dict(title=dict(text="Release Side (in)", standoff=15), range=[-48, 48], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(title=dict(text="Release Height (in)", standoff=15), range=[0, 96], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=70, r=20, t=40, b=60),
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
            if st.button("Delete Selected"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()


###### PITCH BREAK CHART

with c2:

    # Initializes empty plot
    fig2 = go.Figure()

    # Iterates over each pitch, grouped by pitch type, and performs the following
    for pitch, group in df.groupby("TaggedPitchType"):

        # for each pitch type group, adds a new scatter plot layer to the figure with:
        fig2.add_trace(go.Scatter(

            # Horizontal Break on x-axis, Induced Vertical Break on y-axis
            x=group["HorzBreak"],
            y=group["InducedVertBreak"],
            mode="markers",

            # Labels each dot as their respective pitch type
            name=pitch,

            # Styles each dot to size 8, and the color is based on correlating pitch type color that we mapped earlier
            marker=dict(size=12, color=colors.get(pitch, "black")),

            # Attaches dataframe row indeces to each point, will be helpful for click interactions later on
            customdata=group.index.tolist(),
        ))

    fig2.update_layout(

        # Add titles (centered)
        title=dict(text="<b>Pitch Break Chart</b>", x=0.5, xanchor="center"),

        # Square aspect
        width=580,
        height=580,
        autosize=False,

        # Inset legend inside the plot: top-left for RHP, top-right for LHP
        legend=dict(
            x=0.02 if pitcher_hand == "Right" else 0.98,
            y=0.98,
            xanchor="left" if pitcher_hand == "Right" else "right",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="black",
            borderwidth=1
        ),

        # Set axes - standoff pushes the axis title away from the tick numbers
        xaxis=dict(title=dict(text="Horizontal Break (in)", standoff=15), range=[-25, 25], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(title=dict(text="Induced Vertical Break (in)", standoff=15), range=[-25, 25], showgrid=False, zeroline=True, zerolinecolor="black", zerolinewidth=2),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=70, r=20, t=40, b=60),
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
    fig3 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig3.add_trace(go.Scatter(

            # Plate Location Side (ft) on x-axis, Plate Location Height (feet) on y-axis
            x=group["PlateLocSide"],
            y=group["PlateLocHeight"],
            mode="markers",

            # Label each dot as their respective pitch type
            name=pitch,

            # Everything here is identical to previous plots
            marker=dict(size=12, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig3.update_layout(

        # Add titles (centered)
        title=dict(text="<b>Pitch Location Chart</b>", x=0.5, xanchor="center"),

        # Square aspect
        width=580,
        height=580,
        autosize=False,
        showlegend=False,

        # Set axes - standoff pushes the axis title away from the tick numbers
        xaxis=dict(title=dict(text="Plate Location Side (ft)", standoff=15), range=[-3, 3], showgrid=False, zeroline=False, zerolinecolor="black", zerolinewidth=2),
        yaxis=dict(title=dict(text="Plate Location Height (ft)", standoff=15), range=[-1, 6], showgrid=False, zeroline=False, zerolinecolor="black", zerolinewidth=2),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=70, r=20, t=40, b=60),
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
    fig3.add_shape(type="line", x0=-0.75, x1=-0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig3.add_shape(type="line", x0=0.75, x1=0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig3.add_shape(type="line", x0=-0.25, x1=-0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig3.add_shape(type="line", x0=0.25, x1=0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig3.add_shape(type="line", x0=-0.75, x1=0.75, y0=3.65, y1=3.65, line=dict(color="black", width=2))
    fig3.add_shape(type="line", x0=-0.75, x1=0.75, y0=1.65, y1=1.65, line=dict(color="black", width=2))
    fig3.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.32, y1=2.32, line=dict(color="black", width=1))
    fig3.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.99, y1=2.99, line=dict(color="black", width=1))

    # Display plot with key "loc_plot"
    event3 = st.plotly_chart(fig3, on_select="rerun", key="loc_plot", use_container_width=False)

    # When pitch(es) are selected
    if event3 and event3.selection and event3.selection.points:

        # Give users the option between reassigning pitch types or deleting selected pitches
        
        selected_indices = [int(pt["customdata"]) for pt in event3.selection.points]

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
    table["Spin Rate"] = round(table["SpinRate"]).astype("int64")
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
            dfx["CSW %"] = round(dfx["CS %"] + dfx["Whiff %"], 1)
        else:
            dfx["Strike %"] = np.nan
            dfx["Zone %"] = np.nan
            dfx["Swing %"] = np.nan
            dfx["Contact %"] = np.nan
            dfx["CS %"] = np.nan
            dfx["Whiff %"] = np.nan
            dfx["CSW %"] = np.nan
    
        dfn = pd.DataFrame([dfx])
        dff = dfn[["Pitch Type", "Pitch %", "Strike %", "Zone %", "Swing %", "Contact %", "CS %", "Whiff %", "CSW %"]]
    
        types2.append(dff)
        
    perfs = pd.concat(types2, ignore_index=True)
    perfs = perfs.sort_values("Pitch %", ascending=False)
    
    st.dataframe(perfs, hide_index=True, use_container_width=True, height=(len(perfs) + 1) * 35 + 3)


############## STATS TABLE

st.text("STATS")

stats = {}

stats["IP"] = round((len(df[df["KorBB"] == "Strikeout"]) + sum(df["OutsOnPlay"])) / 3, 2)
stats["Hits"] = int(len(df[(df["PlayResult"] == "Single") | (df["PlayResult"] == "Double") | (df["PlayResult"] == "Triple") | (df["PlayResult"] == "HomeRun")]))
stats["Runs"] = int(sum(df["RunsScored"]))
stats["K"] = int(len(df[df["KorBB"] == "Strikeout"]))
stats["BB"] = int(len(df[df["KorBB"] == "Walk"]))
stats["HR"] = int(len(df[df["PlayReslt"] == "HomeRun"]))
stats["HBP"] = int(len(df[df["PitchCall"] == "HitByPitch"]))

stats_df = pd.DataFrame([stats])

st.dataframe(stats_df, hide_index=True, use_container_width=False, height=(len(stats_df) + 1) * 35 + 3)

pdf_buffer = generate_pdf(stats_df, pitcher_display, table, perfs, fig1, fig2, fig3)

st.download_button(
    label="Download PDF Report",
    data=pdf_buffer,
    file_name=f"{pitcher_display.replace(' ', '_')}_report.pdf",
    mime="application/pdf"
)


st.markdown(f"<div style='margin-top: {600}px;'></div>", unsafe_allow_html=True)