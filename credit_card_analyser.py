import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# =======================
# PAGE CONFIG
# =======================
st.set_page_config(page_title="Credit Card Drilldown", layout="wide")

st.title("💳 Credit Card Spend – Category Drill-down")
st.caption("Category → Pie → Merchant breakup")

# =======================
# INPUT
# =======================
raw_text = st.text_area(
    "Paste: Transaction Description<TAB>Amount",
    height=400
)

if not raw_text.strip():
    st.info("⬆ Paste credit card data to begin")
    st.stop()

# =======================
# PARSE
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

df = df[
    ~df["Description"].str.contains("|".join(non_spend_keywords), na=False)
].copy()

# =======================
# AUTO CLASSIFICATION
# =======================
def classify(desc):
    if any(x in desc for x in ["blinkit", "ratna", "dmart", "apna bazaar", "supermarket"]):
        return "Grocery"
    if any(x in desc for x in ["swiggy", "achija", "restaurant", "cafe", "hotel", "aromas"]):
        return "Dining"
    if any(x in desc for x in ["amazon", "ebay", "amazon pay"]):
        return "Online Shopping"
    if any(x in desc for x in ["netflix", "youtube", "bookmyshow", "pvr"]):
        return "Leisure"
    if any(x in desc for x in ["igst", "cbdt"]):
        return "Tax"
    if any(x in desc for x in ["airtel", "utilities"]):
        return "Utilities"
    if any(x in desc for x in ["hp service", "petroleum", "fuel", "auto"]):
        return "Fuel"
    if any(x in desc for x in ["finance charges", "markup fee"]):
        return "Financial Charges"
    if any(x in desc for x in ["hdfc life", "allianz", "insurance"]):
        return "Insurance"
    if any(x in desc for x in ["nps", "safegold", "gold"]):
        return "Investments"
    if any(x in desc for x in ["chatgpt", "udemy", "learning", "course"]):
        return "Learning"
    if any(x in desc for x in ["hotwheels", "gift centre"]):
        return "Hobby"
    if any(x in desc for x in ["hospital", "thyrocare", "dentist", "medical"]):
        return "Medical"
    return "Misc"

df["Category"] = df["Description"].apply(classify)

# =======================
# SIDEBAR FILTERS
# =======================
st.sidebar.header("🔍 Filters")

categories = sorted(df["Category"].unique())
selected_categories = st.sidebar.multiselect(
    "Select Categories",
    categories,
    default=categories
)

filtered_df = df[df["Category"].isin(selected_categories)]

if filtered_df.empty:
    st.warning("No data after filters.")
    st.stop()

# =======================
# SUMMARY
# =======================
st.subheader("📊 Overall Summary")
st.metric("Total Credit Card Spend", f"₹ {filtered_df['Amount'].sum():,.0f}")

# =======================
# PIE CHART (BACK 🔥)
# =======================
st.subheader("🥧 Category-wise Spend")

pie_df = (
    filtered_df.groupby("Category")["Amount"]
    .sum()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots()
ax.pie(
    pie_df.values,
    labels=pie_df.index,
    autopct="%1.1f%%",
    startangle=90
)
ax.axis("equal")
st.pyplot(fig)

# =======================
# CATEGORY DRILL-DOWN
# =======================
st.subheader("🔍 Category Drill-down")

for category, cat_total in pie_df.items():
    with st.expander(f"{category}  |  ₹ {cat_total:,.0f}"):
        sub = (
            filtered_df[filtered_df["Category"] == category]
            .groupby("Description")["Amount"]
            .sum()
            .reset_index()
            .sort_values("Amount", ascending=False)
        )

        sub["% of Category"] = (sub["Amount"] / cat_total * 100).round(1)

        st.dataframe(
            sub.rename(columns={
                "Description": "Sub-category (Merchant)",
                "Amount": "Outflow"
            }),
            use_container_width=True
        )
