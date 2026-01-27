import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# =======================
# PAGE CONFIG
# =======================
st.set_page_config(page_title="Expense Analyser", layout="wide")

# =======================
# TITLE
# =======================
st.title("💸 Personal Expense Analyser")
st.caption("Bucket → Sub-category → Transactions")

# =======================
# BUCKET LOGIC (FINAL)
# =======================
def bucketize(head):
    h = head.lower()

    # -------- INVESTMENTS (TOP PRIORITY) --------
    if any(x in h for x in [
        "sushil", "rba",        # equity / shares
        "safeg",                # gold
        "savings",              # cash savings
        "sip", "nps", "fund", "gold", "ppf"
    ]):
        return "Investment"

    # -------- FIXED --------
    if any(x in h for x in [
        "school", "emi", "maintenance",
        "electricity", "credit", "home", "interest"
    ]):
        return "Fixed"

    # -------- LIFESTYLE --------
    if any(x in h for x in [
        "food", "hotel", "restaurant",
        "cafe", "swagath", "travel",
        "taxi", "shopping"
    ]):
        return "Lifestyle"

    # -------- HOBBY --------
    if any(x in h for x in [
        "hotwheels", "lego", "toy", "collect"
    ]):
        return "Hobby"

    return "Misc"


def sub_category(head):
    h = head.lower()

    # -------- INVESTMENT SUB-CATEGORIES --------
    if "sushil" in h or "rba" in h:
        return "Equity / Shares"

    if "safeg" in h:
        return "Gold Investment"

    if "savings" in h:
        return "Cash / Savings"

    if any(x in h for x in ["sip", "nps", "fund", "ppf"]):
        return "Market Investments"

    # -------- FIXED --------
    if "school" in h:
        return "School Fees"

    if "home" in h or "emi" in h:
        return "Home / Loan EMI"

    if "maintenance" in h:
        return "Society Maintenance"

    if "electricity" in h:
        return "Utilities"

    if "credit" in h:
        return "Credit Card"

    # -------- LIFESTYLE --------
    if any(x in h for x in ["food","hotel","restaurant","cafe","shopping"]):
        return "Food & Lifestyle"

    return "Other"

# =======================
# INPUT
# =======================
st.subheader("📋 Paste Expense Data")

sample_data = """25025\tsushil rba
20547\tsavings
4203\tsafeg
24900\tcredit card
17500\tpremium school
6559\tswagath
"""

use_sample = st.checkbox("Load sample data")

raw_text = st.text_area(
    "Format: Outflow<TAB>Description",
    value=sample_data if use_sample else "",
    height=260
)

if not raw_text.strip():
    st.info("⬆ Paste data or load sample to begin analysis")
    st.stop()

# =======================
# DATA PARSE
# =======================
df = pd.read_csv(StringIO(raw_text), sep="\t", names=["Outflow", "Head"])
df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")
df.dropna(inplace=True)

df["Bucket"] = df["Head"].apply(bucketize)
df["SubCategory"] = df["Head"].apply(sub_category)

# =======================
# SIDEBAR FILTERS
# =======================
st.sidebar.title("🎛 Filters")

bucket_filter = st.sidebar.multiselect(
    "Select Expense Type",
    options=df["Bucket"].unique(),
    default=df["Bucket"].unique()
)

filtered = df[df["Bucket"].isin(bucket_filter)]

# =======================
# SUMMARY METRICS
# =======================
st.subheader("📊 Summary")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Amount", f"₹ {filtered['Outflow'].sum():,.0f}")
with col2:
    st.metric("Transactions", len(filtered))

# =======================
# PIE CHART
# =======================
st.subheader("🥧 Distribution by Bucket")

summary = filtered.groupby("Bucket")["Outflow"].sum()

fig, ax = plt.subplots()
ax.pie(
    summary.values,
    labels=summary.index,
    autopct="%1.1f%%",
    startangle=90
)
ax.axis("equal")
st.pyplot(fig)

# =======================
# DRILL-DOWN VIEW
# =======================
st.subheader("🔍 Category Drill-down")

for bucket in filtered["Bucket"].unique():
    with st.expander(f"{bucket} Details"):
        temp = filtered[filtered["Bucket"] == bucket]

        st.metric(
            "Total",
            f"₹ {temp['Outflow'].sum():,.0f}"
        )

        tab1, tab2 = st.tabs(["📊 Sub-category breakup", "📄 Transactions"])

        with tab1:
            st.dataframe(
                temp.groupby("SubCategory")["Outflow"]
                .sum()
                .reset_index()
                .sort_values("Outflow", ascending=False),
                use_container_width=True
            )

        with tab2:
            st.dataframe(
                temp[["Outflow", "Head", "SubCategory"]],
                use_container_width=True
            )
