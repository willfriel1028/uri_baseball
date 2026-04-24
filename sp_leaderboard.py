import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

table = pd.read_csv("stuff+/stuff_table.csv")
del table["Unnamed: 0"]

table.rename(columns={"Stf+ CU": "Stf+ CB", "Stf+ FC": "Stf+ CT", "Total": "# Pitches", "Stf+ FS": "Stf+ SPLT"}, inplace=True)
table.drop(columns="pitcherId", inplace=True)

teams = list(table["Team"].unique())
teams.sort()
teams.remove("URI")
teams.insert(0, "URI")
teams.insert(0, "TOTAL")

counts = (1, 50, 100, 250, 500)

c1,c2,c3 = st.columns([1,1,3])
with c1:
    team = st.selectbox("Select a Team", options=teams)
with c2:
    count = st.selectbox("Pitch Count Minimum", options=counts)

if team != "TOTAL":
    frame = table[(table["Team"] == team) & (table["# Pitches"] >= count)].sort_values("Stuff+", ascending=False)
    st.dataframe(frame, hide_index=True, use_container_width=True, height=(len(frame) + 1) * 35 + 3)
if team == "TOTAL":
    frame = table[(table["# Pitches"] >= count)].sort_values("Stuff+", ascending=False)
    st.dataframe(frame, hide_index=True, use_container_width=True, height=25*32)

