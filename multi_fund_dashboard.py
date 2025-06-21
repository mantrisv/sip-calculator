import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Multi-MF Analyzer", layout="wide")
st.title("📊 Mutual Fund Multi-File Analyzer")

DATA_FOLDER = "data"
funds_data = {}

if os.path.exists(DATA_FOLDER):
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.csv', '.xlsx'))]

    for filename in files:
        filepath = os.path.join(DATA_FOLDER, filename)
        try:
            df = pd.read_csv(filepath) if filename.endswith(".csv") else pd.read_excel(filepath)
            if 'Invested In' not in df.columns or 'Month Change <br> in Shares %' not in df.columns:
                st.warning(f"'{filename}' missing required columns.")
                continue
            df['Month Change <br> in Shares %'] = df['Month Change <br> in Shares %'].astype(str)
            fund_name = filename.replace(".csv", "").replace(".xlsx", "")
            funds_data[fund_name] = df
        except Exception as e:
            st.error(f"Error processing {filename}: {e}")

if funds_data:
    selected_fund = st.selectbox("Select a Mutual Fund", list(funds_data.keys()))
    selected_view = st.selectbox("Select Analysis View", [
        "New Additions",
        "Top Gainers",
        "Top Exits / Reductions",
        "Top Holdings",
        "Sectoral Allocation"
    ])

    df = funds_data[selected_fund]

    st.header(f"📈 Analysis for: {selected_fund} → {selected_view}")

    if selected_view == "New Additions":
        new_stocks = df[df['Month Change <br> in Shares %'].str.contains('new', case=False, na=False)]
        st.dataframe(new_stocks[["Invested In", "Sector", "Month Change <br> in Shares %"]])

    elif selected_view == "Top Gainers":
        gainers = df[df['Month Change <br> in Shares %'].str.contains('^[+]?[0-9]', na=False, regex=True)]
        st.dataframe(gainers.sort_values(by='Month Change <br> in Shares %', ascending=False)[["Invested In", "Month Change <br> in Shares %"]].head(5))

    elif selected_view == "Top Exits / Reductions":
        reducers = df[df['Month Change <br> in Shares %'].str.contains('^-', na=False)]
        st.dataframe(reducers.sort_values(by='Month Change <br> in Shares %')[["Invested In", "Month Change <br> in Shares %"]].head(5))

    elif selected_view == "Top Holdings":
        if '% of Total Holding' in df.columns:
            top_holdings = df[['Invested In', '% of Total Holding']].dropna().sort_values(by='% of Total Holding', ascending=False).head(5)
            st.dataframe(top_holdings)
        else:
            st.warning("'% of Total Holding' column missing in the file.")

    elif selected_view == "Sectoral Allocation":
        if 'Sector' in df.columns and '% of Total Holding' in df.columns:
            sector_summary = df[['Sector', '% of Total Holding']].dropna().groupby('Sector')['% of Total Holding'].sum().reset_index().sort_values(by='% of Total Holding', ascending=False)
            st.dataframe(sector_summary)
        else:
            st.warning("'Sector' or '% of Total Holding' column missing in the file.")
else:
    st.info("No mutual fund files found in the /data folder. Please add .csv or .xlsx files there.")
