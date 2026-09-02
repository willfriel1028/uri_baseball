import streamlit as st
import pandas as pd
from scipy import stats
import pickle
import numpy as np
import duckdb
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
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

st.header("Stuff+ Calculator")

# Create columns for our dropdowns/input boxes where user can fill in metrics
c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])
d1, d2, d3, d4, d5, d6 = st.columns([1,1,1,1,1,1])

with c1:
    pitches = ["FA", "SI", "FC", "SL", "ST", "CU", "CH", "FS"]
    pitch = st.selectbox("Pitch Type", options=pitches)
    if pitch in ["FA", "SI"]:
        bucket = "FB"
    elif pitch in ["FC"]:
        bucket = "FC"
    elif pitch in ["SL", "ST", "CU"]:
        bucket = "BB"
    elif pitch in ["CH", "FS"]:
        bucket = "OFF"
with d1:
    sides = ["R", "L"]
    side = st.selectbox("Pitcher Hand", options=sides)
with c2:
    velo = st.number_input("Release Velocity", value=None, step=0.1)
with d2:
    spin = st.number_input("Spin Rate", value=None, step=1)
with c3:
    ivb = st.number_input("Induced Vertical Break (in)", value=None, step=0.1)
with d3:
    hb = st.number_input("Horizontal Break (in)", value=None, step=0.1)
with c4:
    relz = st.number_input("Release Height (ft)", value=None, step=0.1)
with d4:
    relx = st.number_input("Release Side (ft)", value=None, step=0.1)
with c5:
    ext = st.number_input("Extension (ft)", value=None, step=0.1)
with d5:
    fb_velo = st.number_input("Fastball Velocity (for breaking/offspeed)", value=None, step=0.1)

x = {}
x["pitchBucket"] = bucket
x["releaseVelocity"] = velo
x["inducedVertBreak"] = ivb
x["horzBreak"] = hb
x["spinRate"] = spin
x["relX"] = relx
x["relZ"] = relz
x["extension"] = ext
x["fb_velo"] = fb_velo
x["phand"] = 1 if side == "R" else 0
x["bhand"] = np.nan

fb_features = ["releaseVelocity", "inducedVertBreak", "horzBreak", "spinRate", "relX", "relZ", "extension", "phand", "bhand"]
non_fb_features = fb_features + ["fb_velo"]
target = ["rv"]

dx = pd.DataFrame([x], columns=non_fb_features)

result = duckdb.sql(
    "SELECT AVG(xRV) AS pop_mean, STDDEV_POP(xRV) AS pop_std FROM 'pitch_modeling/stuff/2026/stuff_26.parquet' WHERE pitchType = ?",
    params=[pitch]
).df()
pop_mean = result["pop_mean"].iloc[0]
pop_std = result["pop_std"].iloc[0]

def load_model(pitch):
    key = pitch
    if key not in MODELS_CACHE:
        with open(f'pitch_modeling/stuff/2026/models/stuff_{pitch}.pkl', 'rb') as f:
            MODELS_CACHE[key] = pickle.load(f)
    return MODELS_CACHE[key]

def pred_sp(test, features, target, bucket, pop_mean, pop_std):
    model = load_model(bucket)
    
    test_R = test.copy(); test_R["bhand"] = 1
    test_L = test.copy(); test_L["bhand"] = 0
    
    xrv = (model.predict(test_R[features]) + model.predict(test_L[features])) / 2
    stuff_plus = 100 + (-10 * (xrv - pop_mean) / pop_std)
    return pd.Series(stuff_plus, index=test.index)

def generate_movement_grid(row, bucket, steps=60):
    ivb_range = np.linspace(-25, 25, steps)
    hb_range = np.linspace(-25, 25, steps)
    hb_grid, ivb_grid = np.meshgrid(hb_range, ivb_range)

    if bucket in ["FB", "FC"]:
        df_grid = pd.DataFrame({
            'inducedVertBreak': ivb_grid.ravel(),
            'horzBreak':        hb_grid.ravel(),
            'extension':        row['extension'].iloc[0],
            'relX':             row['relX'].iloc[0],
            'relZ':             row['relZ'].iloc[0],
            'releaseVelocity':  row['releaseVelocity'].iloc[0],
            'spinRate':         row['spinRate'].iloc[0],
            'phand':            row['phand'].iloc[0],
            'bhand':            row['bhand'].iloc[0]
        })

    else:
        df_grid = pd.DataFrame({
            'inducedVertBreak': ivb_grid.ravel(),
            'horzBreak':        hb_grid.ravel(),
            'extension':        row['extension'].iloc[0],
            'relX':             row['relX'].iloc[0],
            'relZ':             row['relZ'].iloc[0],
            'releaseVelocity':  row['releaseVelocity'].iloc[0],
            'spinRate':         row['spinRate'].iloc[0],
            'fb_velo':          row['fb_velo'].iloc[0],
            'phand':            row['phand'].iloc[0],
            'bhand':            row['bhand'].iloc[0]
        })
    
    return ivb_range, hb_range, df_grid, ivb_grid.shape

def generate_stuff_grid(df_grid, grid_shape, bucket, pop_mean, pop_std):
    model = MODELS_CACHE[bucket]
    features = fb_features if bucket in ["FB", "FC"] else non_fb_features
    
    grid_R = df_grid.copy(); grid_R["bhand"] = 1
    grid_L = df_grid.copy(); grid_L["bhand"] = 0
    
    preds = (model.predict(grid_R[features]) + model.predict(grid_L[features])) / 2
    stuff_plus_grid = 100 + (-10 * (preds - pop_mean) / pop_std)
    stuff_plus_grid = stuff_plus_grid.reshape(grid_shape)
    stuff_plus_grid = gaussian_filter(stuff_plus_grid, sigma=2)
    return stuff_plus_grid

MOVEMENT_BOUNDS = {
    ("FA", "R"): {"hb": (0, 25),  "ivb": (0, 30)},
    ("FA", "L"): {"hb": (-25, 0),  "ivb": (0, 30)},
    ("SI", "R"): {"hb": (0, 25),   "ivb": (-5, 20)},
    ("SI", "L"): {"hb": (-25, 0), "ivb": (-5, 20)},
    ("FC", "R"): {"hb": (-15, 5),  "ivb": (-5, 15)},
    ("FC", "L"): {"hb": (-5, 15),  "ivb": (-5, 15)},
    ("SL", "R"): {"hb": (-25, 0),  "ivb": (-15, 15)},
    ("SL", "L"): {"hb": (0, 25),   "ivb": (-15, 15)},
    ("ST", "R"): {"hb": (-25, 0),  "ivb": (-15, 15)},
    ("ST", "L"): {"hb": (0, 25),   "ivb": (-15, 15)},
    ("CU", "R"): {"hb": (-25, 10),  "ivb": (-30, 0)},
    ("CU", "L"): {"hb": (-10, 25),  "ivb": (-30, 0)},
    ("CH", "R"): {"hb": (0, 25),   "ivb": (-10, 20)},
    ("CH", "L"): {"hb": (-25, 0), "ivb": (-10, 20)},
    ("FS", "R"): {"hb": (0, 25),   "ivb": (-15, 15)},
    ("FS", "L"): {"hb": (-25, 0),  "ivb": (-15, 15)},
}

def plot_movement_landscape(ivb_range, hb_range, stuff_grid, pitcher_ivb, pitcher_hb, pitcher_stuff, pitch, side, window=10):
    hb_mesh, ivb_mesh = np.meshgrid(hb_range, ivb_range)
    bounds = MOVEMENT_BOUNDS.get((pitch, side), {"hb": (-25, 25), "ivb": (-25, 25)})
    mask = (
        (hb_mesh  < bounds["hb"][0])  | (hb_mesh  > bounds["hb"][1]) |
        (ivb_mesh < bounds["ivb"][0]) | (ivb_mesh > bounds["ivb"][1])
    )
    masked_grid = np.where(mask, np.nan, stuff_grid)
    masked_grid = np.clip(masked_grid, 70, 130)
    
    plt.close('all')
    fig, ax = plt.subplots(figsize=(9, 7))
    heatmap = ax.contourf(hb_range, ivb_range, masked_grid, levels=np.linspace(70, 130, 31),
                          cmap='RdYlGn', vmin=70, vmax=130)
    cb = plt.colorbar(heatmap, ax=ax, label='Stuff+')
    cb.set_ticks([70, 80, 90, 100, 110, 120, 130])

    ax.scatter(pitcher_hb, pitcher_ivb, color='black', s=50, zorder=5)
    ax.annotate(f'  {pitcher_stuff}', (pitcher_hb, pitcher_ivb),
                color='black', fontsize=10, zorder=5)

    ax.set_xlim(-25, 25)
    ax.set_ylim(-25, 25)
    ax.set_facecolor('white')
    ax.set_xlabel('Horizontal Break (in)')
    ax.set_ylabel('Induced Vertical Break (in)')
    ax.set_title(f'Stuff+ Pitch Movement Landscape — {pitch} ({"LHP" if side == "L" else "RHP"})')
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)

    return fig

with c6:
    button = st.button("Calculate Stuff+")

h1, h2, h3 = st.columns([1,3,1])

if button:
    if bucket in ["FB", "FC"]:
        stuff_plus = round(pred_sp(dx, fb_features, target, bucket, pop_mean, pop_std).iloc[0])
    else:
        stuff_plus = round(pred_sp(dx, non_fb_features, target, bucket, pop_mean, pop_std).iloc[0])
    stuff_plus = int(stuff_plus)
    with h2:
        st.header(f"Stuff+: {stuff_plus}")
        ivb_range, hb_range, df_grid, grid_shape = generate_movement_grid(dx, bucket)
        stuff_grid = generate_stuff_grid(df_grid, grid_shape, bucket, pop_mean, pop_std)
        fig = plot_movement_landscape(ivb_range, hb_range, stuff_grid, ivb, hb, stuff_plus, pitch, side)
        st.pyplot(fig)



















