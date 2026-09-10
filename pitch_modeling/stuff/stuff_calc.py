# Imports
import streamlit as st
import pandas as pd
from scipy import stats
import pickle
import numpy as np
import duckdb
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

# This dict will be used to store any models the user may call - makes it quicker to use them going forward once cached
MODELS_CACHE = {}

# Makes app takes up whole page
st.set_page_config(layout="wide")

# Makes app scrollable
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

# Header
st.header("Stuff+ Calculator")

# Create columns for our dropdowns/input boxes where user can fill in metrics
# Boxes go horizontally along the top of the page
c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])
d1, d2, d3, d4, d5, d6 = st.columns([1,1,1,1,1,1])

with c1:
    # Pitch type choices
    pitches = ["FA", "SI", "FC", "SL", "ST", "CU", "CH", "FS"]

    # Select pitch type from choices
    pitch = st.selectbox("Pitch Type", options=pitches)

    # Assign pitch buckets based on pitch type choice, will be used to decide what model to use 
    if pitch in ["FA", "SI"]:
        bucket = "FB"
    elif pitch in ["FC"]:
        bucket = "FC"
    elif pitch in ["SL", "ST", "CU"]:
        bucket = "BB"
    elif pitch in ["CH", "FS"]:
        bucket = "OFF"
        
with d1:
    # Pitcher handedness choices
    sides = ["R", "L"]

    # Select pitcher handedness
    side = st.selectbox("Pitcher Hand", options=sides)
    
with c2:
    # Input release velocity
    velo = st.number_input("Release Velocity", value=None, step=0.1)
    
with d2:
    # Input spin rate
    spin = st.number_input("Spin Rate", value=None, step=1)
    
with c3:
    # Input IVB
    ivb = st.number_input("Induced Vertical Break (in)", value=None, step=0.1)
    
with d3:
    # Input HB
    hb = st.number_input("Horizontal Break (in)", value=None, step=0.1)
    
with c4:
    # Input vertical release point
    relz = st.number_input("Release Height (ft)", value=None, step=0.1)
    
with d4:
    # Input horizontal release point
    relx = st.number_input("Release Side (ft)", value=None, step=0.1)
    
with c5:
    # Input extension
    ext = st.number_input("Extension (ft)", value=None, step=0.1)
    
with d5:
    # Input fastball velo (only necessary for breaking and offspeed pitches)
    fb_velo = st.number_input("Fastball Velocity (for breaking/offspeed)", value=None, step=0.1)

# Create row of df with all user input values
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

# Define features for fastballs and non-fastballs
fb_features = ["releaseVelocity", "inducedVertBreak", "horzBreak", "spinRate", "relX", "relZ", "extension", "phand", "bhand"]
non_fb_features = fb_features + ["fb_velo"]
target = ["rv"]

# Save row as dx
dx = pd.DataFrame([x], columns=non_fb_features)

# Use SQL to attain population mean and standard deviation of xRV from 2026 test sample
result = duckdb.sql(
    "SELECT AVG(xRV) AS pop_mean, STDDEV_POP(xRV) AS pop_std FROM 'pitch_modeling/stuff/2026/stuff_26.parquet' WHERE pitchType = ?",
    params=[pitch]
).df()
pop_mean = result["pop_mean"].iloc[0]
pop_std = result["pop_std"].iloc[0]

# Define load_model() function 
# This function simply loads the corresponding model based on pitch bucket and stores it in cache
def load_model(pitch):
    key = pitch
    if key not in MODELS_CACHE:
        with open(f'pitch_modeling/stuff/2026/models/stuff_{pitch}.pkl', 'rb') as f:
            MODELS_CACHE[key] = pickle.load(f)
    return MODELS_CACHE[key]

# Define pred_sp() function
# This function loads in the chosen model, uses it to predict xRV vs both RHB and LHB based on corresponding features, 
# and converts the mean of both expected values to the standard Stuff+ scale
def pred_sp(test, features, target, bucket, pop_mean, pop_std):
    # Load model
    model = load_model(bucket)

    # Create 2 instances of this pitch - 1 vs RHB and 1 vs LHB
    test_R = test.copy(); test_R["bhand"] = 1
    test_L = test.copy(); test_L["bhand"] = 0

    # xrv is the mean predicted xRV value of this pitch vs RHB and LHB by the model
    xrv = (model.predict(test_R[features]) + model.predict(test_L[features])) / 2

    # Scale xRV to Stuff+
    stuff_plus = 100 + (-10 * (xrv - pop_mean) / pop_std)

    # Return Stuff+ value
    return pd.Series(stuff_plus, index=test.index)

##### THE NEXT 3 FUNCTIONS WILL BE CREATING THE VISUALIZATION THAT GOES ALONG WITH THE PRODUCED STUFF+ VALUE #####

# This function takes user-input stuff row and expands it into a 50x50 grid (2,500 points) on a pitch break plot - the rest of the stuff features are constant across all location points
# Everything downstream operates on that grid, not the original single row.
def generate_movement_grid(row, bucket, steps=60):

    # [-30,30] bounds for both IVB and HB
    ivb_range = np.linspace(-30, 30, steps)
    hb_range = np.linspace(-30, 30, steps)
    hb_grid, ivb_grid = np.meshgrid(hb_range, ivb_range)

    # Create feature rows for fastballs and cutters
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

    # Create feature rows for non-fastballs
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

# This function calls in our pre-trained model and predicts the run value of each stuff combination on our grid
# Run values are then converted to Stuff+
def generate_stuff_grid(df_grid, grid_shape, bucket, pop_mean, pop_std):

    # Call model from cache
    model = MODELS_CACHE[bucket]

    # Define features
    features = fb_features if bucket in ["FB", "FC"] else non_fb_features

    # Create one grid vs RHB and one vs LHB
    grid_R = df_grid.copy(); grid_R["bhand"] = 1
    grid_L = df_grid.copy(); grid_L["bhand"] = 0

    # Take the mean xRV from both results (vs RHB and LHB)
    preds = (model.predict(grid_R[features]) + model.predict(grid_L[features])) / 2

    # Convert xRV to Stuff+ based on population mean and std. dev. xRV values for selected pitch type
    stuff_plus_grid = 100 + (-10 * (preds - pop_mean) / pop_std)
    
    stuff_plus_grid = stuff_plus_grid.reshape(grid_shape)

    # Apply a gaussian filter to smooth results out - helps to reduce the affects of any noise the model may have picked up on
    stuff_plus_grid = gaussian_filter(stuff_plus_grid, sigma=2)
    return stuff_plus_grid

# This is the bounds based on IVB/HB that pitches will be displayed
# Bounds are set to where it would make sense to see each pitch type land on an IVB/HB plot
# For example, there is no need to display Stuff+ values on a RHP FA on the bottom left quadrant - the training data probably has not seen any like this and it will produce weird results
MOVEMENT_BOUNDS = {
    ("FA", "R"): {"hb": (-5, 25),  "ivb": (0, 30)},
    ("FA", "L"): {"hb": (-25, 5),  "ivb": (0, 30)},
    ("SI", "R"): {"hb": (0, 30),   "ivb": (-10, 20)},
    ("SI", "L"): {"hb": (-30, 0), "ivb": (-10, 20)},
    ("FC", "R"): {"hb": (-15, 5),  "ivb": (-5, 15)},
    ("FC", "L"): {"hb": (-5, 15),  "ivb": (-5, 15)},
    ("SL", "R"): {"hb": (-30, 0),  "ivb": (-15, 15)},
    ("SL", "L"): {"hb": (0, 30),   "ivb": (-15, 15)},
    ("ST", "R"): {"hb": (-30, 0),  "ivb": (-15, 15)},
    ("ST", "L"): {"hb": (0, 30),   "ivb": (-15, 15)},
    ("CU", "R"): {"hb": (-30, 5),  "ivb": (-30, 0)},
    ("CU", "L"): {"hb": (-5, 30),  "ivb": (-30, 0)},
    ("CH", "R"): {"hb": (0, 30),   "ivb": (-10, 20)},
    ("CH", "L"): {"hb": (-30, 0), "ivb": (-10, 20)},
    ("FS", "R"): {"hb": (0, 30),   "ivb": (-15, 15)},
    ("FS", "L"): {"hb": (-30, 0),  "ivb": (-15, 15)},
}

# This function creates our visualization
# Creates plot, populates it, filters it accordingly, colors it based on heatmap of Stuff+
def plot_movement_landscape(ivb_range, hb_range, stuff_grid, ivb, hb, pitcher_stuff, pitch, side):

    # Takes two 1D arrays (the HB values and IVB values that define the grid axes) and expands them into two 2D arrays
    # So for any index (i, j), the pair (hb_mesh[i, j], ivb_mesh[i, j]) gives you the coordinates of one point on the grid
    # This is what lets the rest of the function work elementwise across the whole grid instead of looping.
    hb_mesh, ivb_mesh = np.meshgrid(hb_range, ivb_range)

    # Gets the IVB/HB bounds defined for this specific combination of pitch type / pitcher handedness, so only relevant combinations are displayed on the visualization
    bounds = MOVEMENT_BOUNDS.get((pitch, side), {"hb": (-30, 30), "ivb": (-30, 30)})

    # Creates mask based on defined bounds
    mask = (
        (hb_mesh  < bounds["hb"][0])  | (hb_mesh  > bounds["hb"][1]) |
        (ivb_mesh < bounds["ivb"][0]) | (ivb_mesh > bounds["ivb"][1])
    )

    # If a point is not within boundaries, define it as NAN
    masked_grid = np.where(mask, np.nan, stuff_grid)

    # This caps every value in the array to fall between 70 and 130: anything below 70 gets pushed up to 70 and anything above 130 gets pushed down to 130
    # Solely for visualization purposes, actual Stuff+ printed value not affected
    masked_grid = np.clip(masked_grid, 70, 130)

    # Clear any previously open figures before creating a new one
    plt.close('all')

    # Initialize figure and axes object
    fig, ax = plt.subplots(figsize=(9, 7))

    # Heatmap viz on our grid, colored based on Stuff+ value of a pitch with each combo of IVB/HB, with a range of 70-130 Stuff+
    heatmap = ax.contourf(hb_range, ivb_range, masked_grid, levels=np.linspace(70, 130, 31),
                          cmap='RdYlGn', vmin=70, vmax=130)

    # Color bar for visual guide of what colors mean (Green = better Stuff+, Red = worse Stuff+)
    cb = plt.colorbar(heatmap, ax=ax, label='Stuff+')

    # Set custom ticks on color bar
    cb.set_ticks([70, 80, 90, 100, 110, 120, 130])

    # Create a point on figure representing the specific pitch that the user entered
    ax.scatter(hb, ivb, color='black', s=50, zorder=5)

    # Write the Stuff+ value next to point
    ax.annotate(f'  {pitcher_stuff}', (hb, ivb),
                color='black', fontsize=10, zorder=5)

    # Set x and y ranges for figure - ensures full ivb/hb plot will be shown no matter the pitch type selected
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_facecolor('white')

    # Labels and Title
    ax.set_xlabel('Horizontal Break (in)')
    ax.set_ylabel('Induced Vertical Break (in)')
    ax.set_title(f'Stuff+ Pitch Movement Landscape — {pitch} ({"LHP" if side == "L" else "RHP"})')

    # Create lines representing the vertical axis (for ivb) and horizontal axis (for hb)
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--', zorder=3)

    # Return our figure
    return fig

# Create button
with c6:
    button = st.button("Calculate Stuff+")

h1, h2, h3 = st.columns([1,3,1])

# If the button is pressed...
if button:

    # Fastballs - calculate Stuff+ value using fastball features
    if bucket in ["FB", "FC"]:
        stuff_plus = round(pred_sp(dx, fb_features, target, bucket, pop_mean, pop_std).iloc[0])

    # Non-fastballs - calculate Stuff+ value using non-fastball features
    else:
        stuff_plus = round(pred_sp(dx, non_fb_features, target, bucket, pop_mean, pop_std).iloc[0])
    stuff_plus = int(stuff_plus)

    # With the middle column (so it is centered)
    with h2:
        # Print inputted pitch Stuff+ value at top
        st.header(f"Stuff+: {stuff_plus}")

        # Call generate_movement_grid() to attain ivb/hb ranges, our grid, and its shape
        ivb_range, hb_range, df_grid, grid_shape = generate_movement_grid(dx, bucket)

        # Call generate_stuff_grid() to assign a Stuff+ value to each point on our grid
        stuff_grid = generate_stuff_grid(df_grid, grid_shape, bucket, pop_mean, pop_std)

        # Call plot_movement_landscape() to get our finalized figure 
        fig = plot_movement_landscape(ivb_range, hb_range, stuff_grid, ivb, hb, stuff_plus, pitch, side)

        # Print figure
        st.pyplot(fig)



















