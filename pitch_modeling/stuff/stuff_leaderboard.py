# Imports
import streamlit as st
import pandas as pd
import duckdb

# Make page wide
st.set_page_config(layout="wide")

# Use SQL to get each unique team from pitchers in test set, in alphabetical order
teams = duckdb.sql("SELECT DISTINCT team FROM 'pitch_modeling/stuff/2026/stuff_table_26.parquet' ORDER BY team").df()["team"].tolist()

# Add 'TOTAL' as first option, move 'URI' to first team option
teams.remove("URI")
teams.insert(0, "URI")
teams.insert(0, "TOTAL")

# Minimum number of pitches thrown for a pitcher the user can choose from
counts = (25, 100, 250, 500, 750, 1000)

c1,c2,c3,c4 = st.columns([1,1,1,2])

with c1:
    # Give user choice to only view pitchers from certain team
    team = st.selectbox("Select a Team", options=teams)
    
with c2:
    # Give user choice to only view pitchers with certain pitch count minimum
    count = st.selectbox("Pitch Count Minimum", options=counts)
    
with c3:
    # Give user choice to look at pitchers' Stuff+ against specifically RHB or LHB
    bhand = st.selectbox("Batter Handedness", options=["-", "R", "L"])

# Based on the user's team and pitch count min. selections, build a where clause for our SQL script later on
# This function builds it for us
def build_where_clause(team, count):
    conditions = []
    if team != "TOTAL":
        conditions.append(f'"team" = \'{team}\'')
    if count:
        conditions.append(f"Total >= {count}") 
    if not conditions:
        return "1=1"
    return " AND ".join(conditions)

    # Example: If user selects "URI" for team and 500 for pitch count minimum, this function will return
    # "team" = 'URI' AND Total >= 500
    # as a string

# This function acquires the table that will be presented
def get_table(team, count, bhand):

    # Call build_where_clause() to get our where clause
    where_clause = build_where_clause(team, count)

    ### To see how tables were built, see 'pitch_modeling/stuff/2026/stuff_2026.ipynb`

    # If the user chose to look at values vs RHB, get rows from this table
    if bhand == "R":
        parquet = "pitch_modeling/stuff/2026/stuff_table_vsR_26.parquet"

    # If the user chose to look at values vs LHB, get rows from this table
    elif bhand == "L":
        parquet = "pitch_modeling/stuff/2026/stuff_table_vsL_26.parquet"

    # Otherwise, get rows from this table (Default)
    else:
        parquet = "pitch_modeling/stuff/2026/stuff_table_26.parquet"

    # Create our SQL query
    query = f"""
        SELECT
            Pitcher,
            Team,
            Total,
            Hand,
            "Stf+ FA",
            "Stf+ SI",
            "Stf+ FC",
            "Stf+ CH",
            "Stf+ FS",
            "Stf+ SL",
            "Stf+ ST",
            "Stf+ CU",
            "Stuff+"
        FROM
            '{parquet}'
        WHERE
            {where_clause} 
        ORDER BY
            "Stuff+" DESC
    """
    # Return our acquired rows as a df
    return duckdb.sql(query).df()

# Call get_table to acquire table to be displayed
table = get_table(team, count, bhand)

# Display table - Sizing for if user selected a specific team
if team != "TOTAL":
    st.dataframe(table, hide_index=True, use_container_width=True, height=(len(table) + 1) * 35 + 3)

# Display table - Sizing for if user did not select a specific team
if team == "TOTAL":
    st.dataframe(table, hide_index=True, use_container_width=True, height=25*32)


