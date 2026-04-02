import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from scipy import stats
import pickle
import numpy as np
MODELS_CACHE = {}

st.set_page_config(layout="wide")

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
df["RelSidei"] = df["RelSide"] * 12
df["RelHeighti"] = df["RelHeight"] * 12

c1, c2 = st.columns([1,1])

###### PITCH BREAK CHART

with c2:
    
    pitch_types = ["FA", "SL", "CU", "CH", "SI", "FC", "FS"]
    df = df[df["TaggedPitchType"].isin(pitch_types)]

    colors = {"FA": "red", "SL": "blue", "CU": "green", "CH": "orange",
              "SI": "yellow", "FC": "gray", "FS": "purple"}

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
        width=600,
        height=600,
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

###### SPEED / SPIN CHART
    
with c1:
    
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
        width=600,
        height=600,
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

c1, c2 = st.columns([1,1])

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
        width=600,
        height=600,
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
            if st.button("Apply Change"):
                for idx in selected_indices:
                    st.session_state.data.at[idx, "TaggedPitchType"] = new_type
                st.rerun()
        with col2:
            if st.button("Delete Selected"):
                st.session_state.data = st.session_state.data.drop(index=selected_indices).reset_index(drop=True)
                st.rerun()

###### PITCH LOCATION CHART
    
with c2:

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
        width=600,
        height=600,
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

############## STUFF PLUS TABLE

st.header("Stuff Table")

def pred_rv(test, features, target, pitch, side):
    if (pitch, side) not in MODELS_CACHE:
        with open(f'stuff+/models/25_{pitch}_{side}.pkl', 'rb') as f:
            MODELS_CACHE[(pitch, side)] = pickle.load(f)

    model = MODELS_CACHE[(pitch, side)]
    X_test = test[features]
    predictions = model.predict(X_test) 
    
    return pd.Series(predictions, index=test.index)

types = []

for pitch in list(df["TaggedPitchType"].unique()):
    dfx = {}
    x = df[df["TaggedPitchType"] == pitch]
    dfx["PitchType"] = pitch
    if x["PitcherThrows"].iloc[0] == "Right":
        dfx["PitcherThrows"] = "R"
    else:
        dfx["PitcherThrows"] = "L"
    dfx["Count"] = len(x)
    dfx["vertApprAngle"] = x["VertApprAngle"].mean()
    dfx["horzApprAngle"] = x["HorzApprAngle"].mean()
    dfx["releaseVelocity"] = x["RelSpeed"].mean()
    dfx["inducedVertBreak"] = x["InducedVertBreak"].mean()
    dfx["horzBreak"] = x["HorzBreak"].mean()
    dfx["relX"] = -x["RelSide"].mean()
    dfx["relZ"] = x["RelHeight"].mean()
    dfx["spinRate"] = x["SpinRate"].mean()
    dfx["spinDir"] = x["SpinAxis"].mean()
    dfx["extension"] = x["Extension"].mean()
    
    side = dfx["PitcherThrows"]
    features = ['vertApprAngle', 'inducedVertBreak', 'horzBreak', 'horzApprAngle', 'extension', 'relX', 'relZ', 'releaseVelocity', 'spinRate', 'spinDir']
    target = ["rv"]
    
    dfz = pd.DataFrame([dfx], columns=features) 

    dfx["xrv"] = float(pred_rv(dfz, features, target, pitch, side).iloc[0])

    dfd = pd.DataFrame([dfx])

    stuff = pd.read_csv("stuff+/stuff.csv")
    stuff_p = stuff[(stuff["PitchType"] == pitch)]

    pop_mean = stuff_p["xrv"].mean()
    pop_std = stuff_p["xrv"].std()
    
    xrv = dfx["xrv"]
    stuff_plus = 100 + (-10 * (xrv - pop_mean) / pop_std)

    f = {}
    f["PitchType"] = pitch
    f["Count"] = len(x)
    f["Pitch %"] = round(((len(x) / len(df)) * 100), 1)
    f["Max Velo"] = round(x["RelSpeed"].max(), 1)
    f["Avg Velo"] = round(x["RelSpeed"].mean(), 1)
    f["IVB"] = round(x["InducedVertBreak"].mean(), 1)
    f["HB"] = round(x["HorzBreak"].mean(), 1)
    f["Horz Rel"] = round(x["RelSide"].mean(), 1)
    f["Vert Rel"] = round(x["RelHeight"].mean(), 1)
    f["Spin Rate"] = int(x["SpinRate"].mean())
    f["Extension"] = round(x["Extension"].mean(), 1)
    f["Stuff+"] = round(stuff_plus)
    
    types.append(pd.DataFrame([f]))

stuffs = pd.concat(types, ignore_index=True)

st.dataframe(stuffs, hide_index=True, use_container_width=True, height=(len(stuffs) + 1) * 35 + 3)

############## PERFORMANCE TABLE

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
    xc = x[x["ExitSpeed"].notna()]
    
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
            dfx["Whiff %"] = round(((len(x[x["PitchCall"] == "StrikeSwinging"]) / len(xs)) * 100), 1)
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
    
    







    
