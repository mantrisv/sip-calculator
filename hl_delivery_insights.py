
import streamlit as st
import pandas as pd
import io

st.title("📊 52-Week HL + Gainers/Losers Delivery Insights by Tier")

uploaded_files = st.file_uploader("Upload MCAP, HL, GL, and Delivery (.DAT) files", type=["csv", "DAT"], accept_multiple_files=True)

mcap_file, hl_file, delivery_file, gl_file = None, None, None, None
for file in uploaded_files:
    fname = file.name.lower()
    if "mcap" in fname and fname.endswith(".csv"):
        mcap_file = file
    elif "hl" in fname and fname.endswith(".csv"):
        hl_file = file
    elif "gl" in fname and fname.endswith(".csv"):
        gl_file = file
    elif fname.endswith(".dat"):
        delivery_file = file

def assign_tier(rank):
    if rank <= 500:
        return "T1"
    elif rank <= 1000:
        return "T2"
    elif rank <= 1500:
        return "T3"
    return "Other"

def classify_insight(high_low, delivery):
    if pd.isna(delivery):
        return "Unclassified"
    if high_low == "High":
        return "High on High Delivery = strong hands" if delivery >= 30 else "High on Low Delivery = churn"
    if high_low == "Low":
        return "Low on High Delivery = panic / pressure" if delivery >= 30 else "Low on Low Delivery = selling subsiding"
    return "Unclassified"

def classify_gl(gain_loss, delivery):
    if pd.isna(delivery):
        return "Unclassified"
    if gain_loss == "GAINER":
        return "Gainer on High Delivery = strong hands" if delivery >= 30 else "Gainer on Low Delivery = churn"
    if gain_loss == "LOSER":
        return "Loser on High Delivery = panic / pressure" if delivery >= 30 else "Loser on Low Delivery = selling subsiding"
    return "Unclassified"

def add_copy_button(df, label):
    if not df.empty:
        minimal_df = df[["Security Name"]].copy()
        tsv = minimal_df.to_csv(index=False, sep="\t")
        st.text_area(f"📋 Copy Stock Names – {label}", tsv, height=150)

if mcap_file and hl_file and delivery_file:
    st.success("All required files detected ✅")

    mcap_df = pd.read_csv(mcap_file)
    mcap_df.columns = mcap_df.columns.str.strip()
    mcap_df = mcap_df.sort_values(by="Market Cap(Rs.)", ascending=False).reset_index(drop=True)
    mcap_df["Rank"] = mcap_df.index + 1
    mcap_df["Tier"] = mcap_df["Rank"].apply(assign_tier)
    mcap_df["Security Name"] = mcap_df["Security Name"].astype(str).str.strip().str.upper()
    mcap_df["Symbol"] = mcap_df["Symbol"].astype(str).str.strip().str.upper()

    hl_df = pd.read_csv(hl_file)
    hl_df.columns = hl_df.columns.str.strip()
    hl_df = hl_df.rename(columns={"SECURITY": "Security Name", "NEW_STATUS": "High/Low"})
    hl_df["Security Name"] = hl_df["Security Name"].astype(str).str.strip().str.upper()
    hl_df["High/Low"] = hl_df["High/Low"].map({"H": "High", "L": "Low"})

    hl_merged = pd.merge(hl_df, mcap_df, on="Security Name", how="left")

    delivery_lines = delivery_file.read().decode("utf-8").splitlines()
    delivery_data = [line.strip().split(",") for line in delivery_lines if line.startswith("20,")]
    delivery_df = pd.DataFrame(delivery_data, columns=[
        "Record Type", "Sr No", "Symbol", "Series", "Traded Qty", "Delivered Qty", "% Delivery"])
    delivery_df = delivery_df[["Symbol", "% Delivery"]]
    delivery_df["Symbol"] = delivery_df["Symbol"].astype(str).str.strip().str.upper()
    delivery_df["% Delivery"] = pd.to_numeric(delivery_df["% Delivery"], errors='coerce')

    full_df = pd.merge(hl_merged, delivery_df, on="Symbol", how="left")
    full_df["% Delivery"] = pd.to_numeric(full_df["% Delivery"], errors='coerce')
    full_df["Delivery Insight"] = full_df.apply(lambda row: classify_insight(row["High/Low"], row["% Delivery"]), axis=1)

    st.header("📈 52-Week HL Delivery Insights")
    for tier in ["T1", "T2", "T3"]:
        st.subheader(f"📌 {tier} Stocks")
        tier_df = full_df[full_df["Tier"] == tier]

        for insight in [
            "High on High Delivery = strong hands",
            "High on Low Delivery = churn",
            "Low on High Delivery = panic / pressure",
            "Low on Low Delivery = selling subsiding"]:

            st.markdown(f"**{insight}**")
            filtered = tier_df[tier_df["Delivery Insight"] == insight].copy()
            filtered = filtered.sort_values(by="Rank")[
                ["Security Name", "Symbol", "High/Low", "% Delivery", "Tier", "Rank"]
            ]
            if not filtered.empty:
                st.dataframe(filtered)
                add_copy_button(filtered, f"{tier} - {insight}")
            else:
                st.info("No data found for this category.")

if gl_file:
    st.header("📊 Gainers / Losers Delivery Insights")

    gl_df = pd.read_csv(gl_file)
    gl_df.columns = gl_df.columns.str.strip()
    gl_df = gl_df.rename(columns={
        "GAIN_LOSS": "Gain/Loss", 
        "SECURITY": "Security Name"
    })

    gl_df["Gain/Loss"] = gl_df["Gain/Loss"].astype(str).str.strip().str.upper()
    gl_df["Gain/Loss"] = gl_df["Gain/Loss"].map({"G": "GAINER", "L": "LOSER"}).fillna(gl_df["Gain/Loss"])
    gl_df = gl_df[gl_df["Gain/Loss"].isin(["GAINER", "LOSER"])]

    gl_df["Security Name"] = gl_df["Security Name"].astype(str).str.strip().str.upper()
    gl_merged = pd.merge(gl_df, mcap_df, on="Security Name", how="left")
    gl_merged = pd.merge(gl_merged, delivery_df, on="Symbol", how="left")

    gl_merged["% Delivery"] = pd.to_numeric(gl_merged["% Delivery"], errors='coerce')
    gl_merged["Delivery Insight"] = gl_merged.apply(lambda row: classify_gl(row["Gain/Loss"], row["% Delivery"]), axis=1)

    st.header("📌 Tier-wise Gainers / Losers Delivery Insights")
    for tier in ["T1", "T2", "T3"]:
        st.subheader(f"📌 {tier} Stocks")
        tier_df = gl_merged[gl_merged["Tier"] == tier]

        for insight in [
            "Gainer on High Delivery = strong hands",
            "Gainer on Low Delivery = churn",
            "Loser on High Delivery = panic / pressure",
            "Loser on Low Delivery = selling subsiding"]:

            st.markdown(f"**{insight}**")
            filtered = tier_df[tier_df["Delivery Insight"] == insight].copy()
            filtered = filtered.sort_values(by="Rank")[
                ["Security Name", "Symbol", "Gain/Loss", "% Delivery", "Delivery Insight", "Rank"]
            ]
            if not filtered.empty:
                st.dataframe(filtered)
                add_copy_button(filtered, f"{tier} - {insight}")
            else:
                st.info("No data found for this category.")
