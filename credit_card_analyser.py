import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# =======================
# PAGE CONFIG
# =======================
st.set_page_config(page_title="Credit Card Auto Analyser", layout="wide")

st.title("💳 Credit Card Spend – Auto Classified")
st.caption("Description → Category → % Breakdown (no manual tagging)")

# =======================
# INPUT
# =======================
st.subheader("📋 Paste Credit Card Statement")

raw_text = st.text_area(
    "Format: Transaction Description<TAB>Amount",
    height=400
)

if not raw_text.strip():
    st.info("⬆ Paste credit card data to begin")
    st.stop()

# =======================
# PARSE (ROBUST)
# =======================
df = pd.read_csv(
    StringIO(raw_text),
    sep=r"\s{2,}|\t",
    engine="python",
    names=["Description", "Amount"]
)

df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
df["Description"] = df["Description"].astype(str).str.lower().str.strip()

df = df[df["Amount"].notna()]

# =======================
# FILTER NON-SPEND
# =======================
non_spend_keywords = [
    "netbanking transfer",
    "cashback",
    "refund",
    "waiver",
    "cr "
]

mask_non_spend = df["Description"].str.contains(
    "|".join(non_spend_keywords),
    case=False,
    na=False
)

df = df[~mask_non_spend].copy()

# =======================
# AUTO CLASSIFICATION
# =======================
def classify(desc):
    if any(x in desc for x in ["blinkit", "ratna", "dmart", "apna bazaar", "supermarket"]):
        return "Grocery"

    if any(x in desc for x in ["swiggy", "achija", "restaurant", "cafe", "dining", "hotel", "aromas"]):
        return "Dining"

    if any(x in desc for x in ["amazon", "ebay", "amazon pay", "online"]):
        return "Online Shopping"

    if any(x in desc for x in ["netflix", "youtube", "bookmyshow", "pvr"]):
        return "Leisure"

    if any(x in desc for x in ["igst", "cbdt"]):
        return "Tax"

    if any(x in desc for x in ["airtel", "utilities"]):
        return "Utilities"

    if any(x in desc for x in ["hp service", "petroleum", "fuel", "auto"]):
        return "Fuel"

    if any(x in desc for x in ["finance charges", "markup fee", "financial charges"]):
        return "Financial Charges"

    if any(x in desc for x in ["hdfc life", "allianz", "insurance"]):
        return "Insurance"

    if any(x in desc for x in ["nps", "safegold", "gold"]):
        return "Investments"

    if any(x in desc for x in ["chatgpt", "udemy", "course", "learning"]):
        return "Learning"

    if any(x in desc for x in ["hotwheels", "gift centre"]):
        return "Hobby"

    if any(x in desc for x in ["hospital", "thyrocare", "dentist", "medical"]):
        return "Medical"

    return "Misc"

df["Category"] = df["Description"].apply(classify)

# =======================
# SUMMARY
# =======================
st.subheader("📊 Summary")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Credit Card Spend", f"₹ {df['Amount'].sum():,.0f}")
with col2:
    st.metric("Transactions", len(df))

# =======================
# CATEGORY BREAKUP
# =======================
st.subheader("🥧 Spend by Category")

summary = (
    df.groupby("Category")["Amount"]
    .sum()
    .reset_index()
    .sort_values("Amount", ascending=False)
)

total = summary["Amount"].sum()
summary["% of Spend"] = (summary["Amount"] / total * 100).round(1)

fig, ax = plt.subplots()
ax.pie(
    summary["Amount"],
    labels=summary["Category"],
    autopct="%1.1f%%",
    startangle=90
)
ax.axis("equal")
st.pyplot(fig)

st.dataframe(summary, use_container_width=True)

# =======================
# TRANSACTIONS
# =======================
with st.expander("📄 View Transactions"):
    st.dataframe(
        df[["Description", "Category", "Amount"]],
        use_container_width=True
    )
