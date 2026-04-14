import streamlit as st
import pandas as pd
from scipy import stats
import pickle
import numpy as np
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

c1, c2, c3, c4 = st.columns([2, 1, 4, 1])
with c1:
    pitches = ["FA", "SL", "CH", "CU", "FC", "SI", "FS"]
    pitch = st.selectbox("Pitch Type", options=pitches)
    sides = ["R", "L"]
    side = st.selectbox("Pitcher Hand", options=sides)
    velo = st.number_input("Release Velocity", value=None, step=0.1)
    ivb = st.number_input("Induced Vertical Break (in)", value=None, step=0.1)
    hb = st.number_input("Horizontal Break (in)", value=None, step=0.1)
    spin = st.number_input("Spin Rate", value=None, step=1)
    relx = st.number_input("Release Side (ft)", value=None, step=0.1)
    relz = st.number_input("Release Height (ft)", value=None, step=0.1)
    ext = st.number_input("Extension (ft)", value=None, step=0.1)

x = {}
x["PitchType"] = pitch
x["PitcherThrows"] = side
x["releaseVelocity"] = velo
x["inducedVertBreak"] = ivb
x["horzBreak"] = hb
x["spinRate"] = spin
if pd.notna(relx):
    x["relX"] = -relx
x["relZ"] = relz
x["extension"] = ext

features = ['inducedVertBreak', 'horzBreak', 'extension', 'relX', 'relZ', 'releaseVelocity', 'spinRate']
target = ["rv"]
dx = pd.DataFrame([x], columns=features)

stuff = pd.read_csv("stuff+/stuff.csv")

def pred_sp(test, features, target, pitch, side, stuff):
    if (pitch, side) not in MODELS_CACHE:
        with open(f'stuff+/models/26_{pitch}_{side}.pkl', 'rb') as f:
            MODELS_CACHE[(pitch, side)] = pickle.load(f)
    model = MODELS_CACHE[(pitch, side)]
    X_test = test[features]
    predictions = model.predict(X_test)
    stuff_p = stuff[(stuff["PitchType"] == pitch)]
    pop_mean = stuff_p["xrv"].mean()
    pop_std = stuff_p["xrv"].std()
    xrv = predictions
    stuff_plus = 100 + (-10 * (xrv - pop_mean) / pop_std)
    return pd.Series(stuff_plus, index=test.index)

def generate_movement_grid(pitcher_row, steps=60):
    ivb_range = np.linspace(-30, 30, steps)
    hb_range = np.linspace(-30, 30, steps)
    hb_grid, ivb_grid = np.meshgrid(hb_range, ivb_range)
    df_grid = pd.DataFrame({
        'inducedVertBreak': ivb_grid.ravel(),
        'horzBreak':        hb_grid.ravel(),
        'extension':        pitcher_row['extension'].iloc[0],
        'relX':             pitcher_row['relX'].iloc[0],
        'relZ':             pitcher_row['relZ'].iloc[0],
        'releaseVelocity':  pitcher_row['releaseVelocity'].iloc[0],
        'spinRate':         pitcher_row['spinRate'].iloc[0],
    })
    return ivb_range, hb_range, df_grid, ivb_grid.shape

def generate_stuff_grid(df_grid, grid_shape, pitch, side, stuff):
    model = MODELS_CACHE[(pitch, side)]
    preds = model.predict(df_grid[features])
    stuff_p = stuff[stuff["PitchType"] == pitch]
    pop_mean = stuff_p["xrv"].mean()
    pop_std = stuff_p["xrv"].std()
    stuff_plus_grid = 100 + (-10 * (preds - pop_mean) / pop_std)
    stuff_plus_grid = stuff_plus_grid.reshape(grid_shape)
    stuff_plus_grid = gaussian_filter(stuff_plus_grid, sigma=2)
    return stuff_plus_grid

MOVEMENT_BOUNDS = {
    ("FA", "R"): {"hb": (0, 30),  "ivb": (0, 30)},
    ("FA", "L"): {"hb": (-30, 0),  "ivb": (0, 30)},
    ("SI", "R"): {"hb": (0, 30),   "ivb": (-5, 20)},
    ("SI", "L"): {"hb": (-30, 0), "ivb": (-5, 20)},
    ("FC", "R"): {"hb": (-15, 15),  "ivb": (-5, 20)},
    ("FC", "L"): {"hb": (-15, 15),  "ivb": (-5, 20)},
    ("SL", "R"): {"hb": (-30, 0),  "ivb": (-15, 15)},
    ("SL", "L"): {"hb": (0, 30),   "ivb": (-15, 15)},
    ("CU", "R"): {"hb": (-25, 10),  "ivb": (-30, 0)},
    ("CU", "L"): {"hb": (-10, 25),  "ivb": (-30, 0)},
    ("CH", "R"): {"hb": (0, 30),   "ivb": (-10, 20)},
    ("CH", "L"): {"hb": (-30, 0), "ivb": (-10, 20)},
    ("FS", "R"): {"hb": (0, 30),   "ivb": (-15, 15)},
    ("FS", "L"): {"hb": (-30, 0),  "ivb": (-15, 15)},
}

def plot_movement_landscape(ivb_range, hb_range, stuff_grid, pitcher_ivb, pitcher_hb, pitcher_stuff, pitch, side, window=10):
    hb_mesh, ivb_mesh = np.meshgrid(hb_range, ivb_range)
    bounds = MOVEMENT_BOUNDS.get((pitch, side), {"hb": (-30, 30), "ivb": (-30, 30)})
    mask = (
        (hb_mesh  < bounds["hb"][0])  | (hb_mesh  > bounds["hb"][1]) |
        (ivb_mesh < bounds["ivb"][0]) | (ivb_mesh > bounds["ivb"][1])
    )
    masked_grid = np.where(mask, np.nan, stuff_grid)
    masked_grid = np.clip(masked_grid, 70, 130)
    
    plt.close('all')
    fig, ax = plt.subplots(figsize=(8, 7))
    heatmap = ax.contourf(hb_range, ivb_range, masked_grid, levels=np.linspace(70, 130, 31),
                          cmap='RdYlGn', vmin=70, vmax=130)
    cb = plt.colorbar(heatmap, ax=ax, label='Stuff+')
    cb.set_ticks([70, 80, 90, 100, 110, 120, 130])

    ax.scatter(pitcher_hb, pitcher_ivb, color='black', s=50, zorder=5)
    ax.annotate(f'  {pitcher_stuff}', (pitcher_hb, pitcher_ivb),
                color='black', fontsize=10, zorder=5)

    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_facecolor('white')
    ax.set_xlabel('Horizontal Break (in)')
    ax.set_ylabel('Induced Vertical Break (in)')
    ax.set_title(f'Stuff+ Pitch Movement Landscape — {pitch} ({"LHP" if side == "L" else "RHP"})')
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)

    return fig

with c1:
    button = st.button("Calculate Stuff+")

if button:
    stuff_plus = round(pred_sp(dx, features, target, pitch, side, stuff).iloc[0])
    stuff_plus = int(stuff_plus)
    with c1:
        st.header(f"Stuff+: {stuff_plus}")
    with c3:
        ivb_range, hb_range, df_grid, grid_shape = generate_movement_grid(dx)
        stuff_grid = generate_stuff_grid(df_grid, grid_shape, pitch, side, stuff)
        fig = plot_movement_landscape(ivb_range, hb_range, stuff_grid, ivb, hb, stuff_plus, pitch, side)
        st.pyplot(fig)