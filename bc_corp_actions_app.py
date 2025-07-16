import streamlit as st
import pandas as pd

st.set_page_config(page_title="NSE Corporate Actions Parser", layout="wide")
st.title("📄 NSE Corporate Actions – BCDDMMYY.csv Parser")

uploaded_file = st.file_uploader("Upload bcddmmyy.csv file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Filter for SERIES == 'EQ'
    df_eq = df[df['SERIES'] == 'EQ']

    # Convert PURPOSE to upper case to normalize
    df_eq['PURPOSE'] = df_eq['PURPOSE'].str.upper()

    # Filter different corporate actions
    rights_df = df_eq[df_eq['PURPOSE'].str.contains("RIGHT")]
    bonus_df = df_eq[df_eq['PURPOSE'].str.contains("BONUS")]
    demerger_df = df_eq[df_eq['PURPOSE'].str.contains("DEMERGER")]
    split_df = df_eq[df_eq['PURPOSE'].str.contains("FV SPLIT|FVSPLT|FACE VALUE|SPLIT")]  # broader matching

    # Identify other actions
    known_keywords = ["RIGHT", "BONUS", "DEMERGER", "FV SPLIT", "FVSPLT", "FACE VALUE", "SPLIT"]
    others_df = df_eq[~df_eq['PURPOSE'].apply(lambda x: any(keyword in x for keyword in known_keywords))]

    tabs = st.tabs(["Rights Issue", "Bonus Issue", "Demerger", "Face Value Split", "Others"])

    with tabs[0]:
        st.subheader("📌 Rights Issue")
        st.dataframe(rights_df.reset_index(drop=True))

    with tabs[1]:
        st.subheader("🎁 Bonus Issue")
        st.dataframe(bonus_df.reset_index(drop=True))

    with tabs[2]:
        st.subheader("🔄 Demerger")
        st.dataframe(demerger_df.reset_index(drop=True))

    with tabs[3]:
        st.subheader("🔢 Face Value Split")
        st.dataframe(split_df.reset_index(drop=True))

    with tabs[4]:
        st.subheader("📋 Other Corporate Actions")
        st.dataframe(others_df.reset_index(drop=True))
else:
    st.info("Please upload a valid bcddmmyy.csv file to view corporate actions.")
