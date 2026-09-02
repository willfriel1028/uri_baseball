import streamlit as st
import pandas as pd
import duckdb

st.set_page_config(layout="wide")

teams = duckdb.sql("SELECT DISTINCT team FROM '2026/stuff_table_26.parquet' ORDER BY team").df()["team"].tolist()
teams.remove("URI")
teams.insert(0, "URI")
teams.insert(0, "TOTAL")

counts = (25, 100, 250, 500, 750, 1000)

c1,c2,c3,c4 = st.columns([1,1,1,2])
with c1:
    team = st.selectbox("Select a Team", options=teams)
with c2:
    count = st.selectbox("Pitch Count Minimum", options=counts)
with c3:
    bhand = st.selectbox("Batter Handedness", options=["-", "R", "L"])

def build_where_clause(team, count):
    conditions = []
    if team != "TOTAL":
        conditions.append(f'"team" = \'{team}\'')
        
    if count:
        conditions.append(f"Total >= {count}")
        
    if not conditions:
        return "1=1"
    return " AND ".join(conditions)

def get_table(team, count, bhand):
    where_clause = build_where_clause(team, count)

    if bhand == "R":
        parquet = "2026/stuff_table_vsR_26.parquet"
    elif bhand == "L":
        parquet = "2026/stuff_table_vsL_26.parquet"
    else:
        parquet = "2026/stuff_table_26.parquet"
    
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
    return duckdb.sql(query).df()

table = get_table(team, count, bhand)

print(duckdb.sql("SELECT COUNT(*) FROM '2026/stuff_table_26.parquet' WHERE Total >= 25").df())

if team != "TOTAL":
    st.dataframe(table, hide_index=True, use_container_width=True, height=(len(table) + 1) * 35 + 3)
if team == "TOTAL":
    st.dataframe(table, hide_index=True, use_container_width=True, height=25*32)


