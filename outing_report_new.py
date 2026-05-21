import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import pickle
import numpy as np
MODELS_CACHE = {}

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

files = st.file_uploader("Import Trackman file", type="csv", accept_multiple_files=True)

if st.button("Refresh"):
    del st.session_state.data
    st.session_state.file_key = st.session_state.get("file_key", 0) + 1 
    st.rerun()

if files and "data" not in st.session_state:
    dfs = [pd.read_csv(f) for f in files]
    st.session_state.data = pd.concat(dfs, ignore_index=True)

if "data" not in st.session_state:
    st.info("Please upload a CSV to get started.")
    st.stop()

data = st.session_state.data

data["TaggedPitchType"] = data["TaggedPitchType"].replace({
        "Fastball": "FA",
        "Slider": "SL",
        "Curveball": "CU",
        "ChangeUp": "CH",
        "Sinker": "SI",
        "Cutter": "FC",
        "Splitter": "FS"
    })

############## INTERACTIVE PITCH CHARTS

x1,x2,x3 = st.columns([1,2,1])
with x2:
    names = list(data["Pitcher"].unique())
    pitcher = st.selectbox("Choose a Pitcher", options=names)

df = data[data["Pitcher"] == pitcher]
df = df[df["TaggedPitchType"] != "Other"]

df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12

c1, c2, c3 = st.columns([1,1,1])

###### PITCH BREAK CHART

with c2:
    
    pitch_types = ["FA", "SL", "CU", "CH", "SI", "FC", "FS"]
    df = df[df["TaggedPitchType"].isin(pitch_types)]

    colors = {"FA": "red", "SL": "blue", "CU": "green", "CH": "orange",
              "SI": "brown", "FC": "gray", "FS": "purple"}

    fig1 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig1.add_trace(go.Scatter(
            x=group["HorzBreak"],
            y=group["InducedVertBreak"],
            mode="markers",
            name=pitch,
            marker=dict(size=10, color=colors.get(pitch, "black")),
            customdata=group.index.tolist(),
        ))

    fig1.update_layout(
        title="Pitch Break Chart",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",
        width=100,
        height=500,
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

    event1 = st.plotly_chart(fig1, on_select="rerun", key="plot1")

    if event1 and event1.selection and event1.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event1.selection.points]
        
        st.markdown(f"**{len(selected_indices)} pitches selected**")
        
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

###### RELEASE POINT CHART

with c1:

    fig3 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig3.add_trace(go.Scatter(
            x=group["RelSidei"],
            y=group["RelHeighti"],
            mode="markers",
            name=pitch,
            marker=dict(size=10, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig3.update_layout(
        title="Release Point Chart",
        xaxis_title="Release Side (in)",
        yaxis_title="Release Height (in)",
        width=10,
        height=500,
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

    event3 = st.plotly_chart(fig3, on_select="rerun", key="rel_plot")

    if event3 and event3.selection and event3.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event3.selection.points]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Selected"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()

###### PITCH LOCATION CHART
    
with c3:

    fig4 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig4.add_trace(go.Scatter(
            x=group["PlateLocSide"],
            y=group["PlateLocHeight"],
            mode="markers",
            name=pitch,
            marker=dict(size=10, color=colors.get(pitch, "black"), line=dict(color="white", width=0.5)),
            customdata=group.index.tolist(),
        ))

    fig4.update_layout(
        title="Pitch Location Chart",
        xaxis_title="Plate Location Side (ft)",
        yaxis_title="Plate Location Height (ft)",
        width=10,
        height=500,
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

    fig4.add_shape(type="line", x0=-0.75, x1=-0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=0.75, x1=0.75, y0=1.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=-0.25, x1=-0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=0.25, x1=0.25, y0=1.65, y1=3.65, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=3.65, y1=3.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=1.65, y1=1.65, line=dict(color="black", width=2))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.32, y1=2.32, line=dict(color="black", width=1))
    fig4.add_shape(type="line", x0=-0.75, x1=0.75, y0=2.99, y1=2.99, line=dict(color="black", width=1))

    event4 = st.plotly_chart(fig4, on_select="rerun", key="loc_plot")

    if event4 and event4.selection and event4.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event4.selection.points]
        
        st.markdown(f"**{len(selected_indices)} pitches selected**")
        
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

co1, co2, co3, co4, co5 = st.columns([1,3,1,3,1])

###### SPEED / SPIN CHART

with co2:

    fig2 = go.Figure()
    for pitch, group in df.groupby("TaggedPitchType"):
        fig2.add_trace(go.Scatter(
            x=group["SpinRate"],
            y=group["RelSpeed"],
            mode="markers",
            name=pitch,
            marker=dict(size=10, color=colors.get(pitch, "black")),
            customdata=group.index.tolist(),
        ))

    fig2.update_layout(
        title="Speed / Spin Chart",
        xaxis_title="Spin Rate",
        yaxis_title="Release Speed",
        width=10,
        height=500,
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

    event2 = st.plotly_chart(fig2, on_select="rerun", key="pitch_plot")

    if event2 and event2.selection and event2.selection.points:
        selected_indices = [int(pt["customdata"]) for pt in event2.selection.points]
        
        st.markdown(f"**{len(selected_indices)} pitches selected**")
        
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

###### STUFF PLUS PLOT

def pred_rv(test, features, target, pitch, side):
    if (pitch, side) not in MODELS_CACHE:
        with open(f'stuff+/models/26_{pitch}_{side}.pkl', 'rb') as f:
            MODELS_CACHE[(pitch, side)] = pickle.load(f)

    model = MODELS_CACHE[(pitch, side)]
    X_test = test[features]
    predictions = model.predict(X_test) 
    
    return pd.Series(predictions, index=test.index)

stuff = pd.read_csv("stuff+/stuff.csv")

rows = []

for index, row in df.iterrows():

    test = {}
    test["inducedVertBreak"] = row["InducedVertBreak"]
    test["horzBreak"] = row["HorzBreak"]
    test["extension"] = row["Extension"]
    test["relX"] = row["RelSide"]
    test["relZ"] = row["RelHeight"]
    test["releaseVelocity"] = row["RelSpeed"]
    test["spinRate"] = row["SpinRate"]

    if row["PitcherThrows"] == "Right":
        side = "R"
    else:
        side = "L"
    
    features = ['inducedVertBreak', 'horzBreak', 'extension', 'relX', 'relZ', 'releaseVelocity', 'spinRate']
    target = ["rv"]
    pitch = row["TaggedPitchType"]

    test_df = pd.DataFrame([test], columns=features) 

    test_df["xrv"] = float(pred_rv(test_df, features, target, pitch, side).iloc[0])

    test_df["PitchType"] = pitch
    test_df["PitcherThrows"] = side
    test_df["PlateLocSide"] = row["PlateLocSide"]
    test_df["PlateLocHeight"] = row["PlateLocHeight"]
    test_df["PitchCall"] = row["PitchCall"]
    test_df["ExitSpeed"] = row["ExitSpeed"]
    test_df["KorBB"] = row["KorBB"]
    test_df["OutsOnPlay"] = row["OutsOnPlay"]
    test_df["PlayResult"] = row["PlayResult"]
    test_df["RunsScored"] = row["RunsScored"]
    test_df["Strikes"] = row["Strikes"]
    test_df["Balls"] = row["Balls"]
    test_df["Date"] = row["Date"]
    test_df["Inning"] = row["Inning"]
    test_df["PAofInning"] = row["PAofInning"]

    stuff_p = stuff[(stuff["PitchType"] == pitch)]

    pop_mean = stuff_p["xrv"].mean()
    pop_std = stuff_p["xrv"].std()

    test_df["Stuff+"] = 100 + (-10 * (test_df["xrv"] - pop_mean) / pop_std)

    rows.append(test_df)

df = pd.concat(rows, ignore_index=True)

df.rename(columns={'inducedVertBreak': 'InducedVertBreak', 'horzBreak': 'HorzBreak', 'extension': 'Extension', 'relX': 'RelSide', 'relZ': 'RelHeight', 'releaseVelocity': 'RelSpeed', 'spinRate': 'SpinRate', 'PitchType': 'TaggedPitchType'}, inplace=True)

with co3:
    
    pitches = list(df["TaggedPitchType"].unique())
    pitch = st.selectbox("Choose a Pitch", options=pitches)
    df_p = df[df["TaggedPitchType"] == pitch]

with co4:
    
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=df_p["HorzBreak"],
        y=df_p["InducedVertBreak"],
        mode="markers",
        marker=dict(
            size=10,
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
        title="Stuff+ On Pitch Break Chart",
        xaxis_title="Horizontal Break (in)",
        yaxis_title="Induced Vertical Break (in)",
        width=10,
        height=500,
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

    event5 = st.plotly_chart(fig5, on_select="rerun", key="stuff_plot")


############## STUFF PLUS TABLE

g1,g2 = st.columns([1,1])

with g1:
    st.header("Stuff Table")

    table = df.groupby("TaggedPitchType").agg(
        Count = ("TaggedPitchType", "count"),
        Max_Velo = ("RelSpeed", "max"),
        Avg_Velo = ("RelSpeed", "mean"),
        IVB = ("InducedVertBreak", "mean"),
        HB = ("HorzBreak", "mean"),
        Horz_Rel = ("RelSide", "mean"),
        Vert_Rel = ("RelHeight", "mean"),
        SpinRate = ("SpinRate", "mean"),
        Extension = ("Extension", "mean"),
        xrv = ("xrv", "mean")
    ).reset_index()

    table.rename(columns={"TaggedPitchType": "PitchType"}, inplace=True)
    table["Max_Velo"] = round(table["Max_Velo"], 1)
    table["Avg_Velo"] = round(table["Avg_Velo"], 1)
    table["IVB"] = round(table["IVB"], 1)
    table["HB"] = round(table["HB"], 1)
    table["Horz_Rel"] = round(table["Horz_Rel"], 1)
    table["Vert_Rel"] = round(table["Vert_Rel"], 1)
    table["SpinRate"] = round(table["SpinRate"])
    table["Extension"] = round(table["Extension"], 1)

    table["Stuff+"] = np.nan

    rows = []
    for index, row in table.iterrows():
        x = stuff[stuff["PitchType"] == row["PitchType"]]
        pop_mean = x["xrv"].mean()
        pop_std = x["xrv"].std()

        row["Stuff+"] = round(100 + (-10 * (row["xrv"] - pop_mean) / pop_std))
        rows.append(row)

    table = pd.concat(rows, axis=1, ignore_index=True).T

    table.drop(columns=["xrv"], inplace=True)
        
    st.dataframe(table, hide_index=True, use_container_width=True, height=(len(table) + 1) * 35 + 3)

############## PERFORMANCE TABLE

j1,j2 = st.columns([1,1])

with j1:
    st.header("Performance Table")
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
        
        dfx["PitchType"] = pitch
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
        dff = dfn[["PitchType", "Strike %", "Zone %", "Swing %", "Contact %", "CS %", "Whiff %", "CSW %", "Avg EV"]]
    
        types2.append(dff)
        
    perfs = pd.concat(types2, ignore_index=True)
    
    st.dataframe(perfs, hide_index=True, use_container_width=True, height=(len(perfs) + 1) * 35 + 3)

############## STATISTICS TABLE

h1,h2 = st.columns([1,1])
with h1:
    st.header("Competition Table")

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
    
    st.dataframe(pd.DataFrame([stats]), hide_index=True, use_container_width=True, height=(len(pd.DataFrame([stats])) + 1) * 35 + 3)
    
    







    
