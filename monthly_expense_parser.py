import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

# Define categorization rules
CATEGORY_RULES = {
    "Education": ["school"],
    "Housing": ["home", "society", "kitchen sink", "trolley"],
    "Investments": ["ppf", "nps", "rba"],
    "Loans": ["axis", "emi"],
    "Utilities": ["phone", "PUC", "rights issue"],
    "Credit Card": ["credit card"],
    "Food": ["swagath", "chefs", "theory", "mukhis", "vithaldas"],
    "Hotwheels": ["hotwheels"],
    "Books": ["books"],
    "Miscellaneous": ["misc", "adjustment", "frameley", "mini tatal", "syed", "jio star"],
    "Savings": ["savings"],
    "Cash": ["cash"],
    "SIP/Lumpsum": ["sip"]
}

def categorize(description):
    desc = description.lower()
    if "sip" in desc:
        return "SIP/Lumpsum"
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in desc for keyword in keywords):
            return category
    return "Unclassified"

def parse_pasted_data(text):
    lines = text.strip().splitlines()
    data = []
    for line in lines:
        match = re.match(r"(\d+)\s+(.+)", line.strip())
        if match:
            amount = int(match.group(1))
            description = match.group(2)
            category = categorize(description)
            data.append({"Amount": amount, "Description": description, "Category": category})
    return pd.DataFrame(data)

def main():
    st.title("📋 Monthly Expense Categorizer")
    st.write("Paste your raw expense data below. Each line should be like:")
    st.code("amount in figures  description")

    pasted_text = st.text_area("Paste Here:", height=300)

    if pasted_text:
        df = parse_pasted_data(pasted_text)

        # Show table
        st.subheader("Parsed Expenses")
        st.dataframe(df)

        # Show category-wise summary
        st.subheader("Category Summary")
        summary = df.groupby("Category")["Amount"].sum().reset_index()
        st.dataframe(summary)

        # Pie chart
        fig, ax = plt.subplots()
        ax.pie(summary["Amount"], labels=summary["Category"], autopct='%1.1f%%')
        ax.axis("equal")
        st.pyplot(fig)

if __name__ == "__main__":
    main()
