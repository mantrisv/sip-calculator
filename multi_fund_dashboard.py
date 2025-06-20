import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="MyMFInsights Dashboard", layout="wide")
st.title("📊 MyMFInsights: Mutual Fund Holdings Dashboard")

st.markdown("Upload multiple mutual fund holdings Excel/CSV files. Files must contain columns like: `Invested In`, `Sector`, `Outflow`, `Month`, `Year`.")

uploaded_files = st.file_uploader("📁 Upload Mutual Fund Files", type=["csv", "xlsx"], accept_multiple_files=True)

@st.cache_data

def load_file(file):
    ext = file.name.split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    df = df.rename(columns=lambda x: x.strip())
    return df

fund_data = {}

if uploaded_files:
    for file in uploaded_files:
        df = load_file(file)
        fund_name = file.name.rsplit(".", 1)[0]  # file name without extension
        if {'Invested In', 'Outflow'}.issubset(df.columns):
            df['Fund'] = fund_name
            fund_data[fund_name] = df

if fund_data:
    fund_selected = st.selectbox("Select Mutual Fund", list(fund_data.keys()))
    view_selected = st.selectbox("Select View", [
        "New Additions",
        "Top Gainers (Increased Holdings)",
        "Top Exits / Reductions",
        "Top Holdings",
        "Sectoral Allocation"
    ])

    df = fund_data[fund_selected].copy()

    if view_selected == "New Additions":
        if 'Previous Month' in df.columns:
            new_additions = df[df['Previous Month'].isna()]  # or some logic to detect new
            st.subheader("🆕 New Additions")
            st.dataframe(new_additions, use_container_width=True)
        else:
            st.info("Need previous month data to detect additions.")

    elif view_selected == "Top Gainers (Increased Holdings)":
        if 'Change %' in df.columns:
            gainers = df.sort_values(by='Change %', ascending=False).head(10)
            st.subheader("📈 Top Gainers")
            st.dataframe(gainers, use_container_width=True)
        else:
            st.info("Column 'Change %' not found in uploaded data.")

    elif view_selected == "Top Exits / Reductions":
        if 'Change %' in df.columns:
            losers = df.sort_values(by='Change %').head(10)
            st.subheader("📉 Top Reductions/Exits")
            st.dataframe(losers, use_container_width=True)
        else:
            st.info("Column 'Change %' not found in uploaded data.")

    elif view_selected == "Top Holdings":
        if 'Outflow' in df.columns:
            top_holdings = df.sort_values(by='Outflow', ascending=False).head(10)
            st.subheader("🏆 Top Holdings")
            st.dataframe(top_holdings, use_container_width=True)
        else:
            st.info("Column 'Outflow' not found in uploaded data.")

    elif view_selected == "Sectoral Allocation":
        if 'Sector' in df.columns and 'Outflow' in df.columns:
            sector_data = df.groupby('Sector')['Outflow'].sum().reset_index()
            fig = px.pie(sector_data, names='Sector', values='Outflow', title='Sectoral Allocation')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Columns 'Sector' and 'Outflow' required for sectoral chart.")
else:
    st.info("Upload at least one mutual fund holdings file to begin.")
