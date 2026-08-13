"""
app.py — Navigation entrypoint for the Hydrological Forecasting app.
Defines two pages: Forecast tool and Documentation.
"""
import streamlit as st

forecast_page = st.Page(
    "pages/0_Forecast.py",
    title="River Outlook",
    icon=":material/water_drop:",
    default=True,
)
docs_page = st.Page(
    "pages/1_Documentation.py",
    title="How This Works",
    icon=":material/menu_book:",
)

pg = st.navigation([forecast_page, docs_page], position="top")
pg.run()
