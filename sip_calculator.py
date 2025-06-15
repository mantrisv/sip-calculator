import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Title
st.title("📈 SIP Calculator")

# Inputs
monthly_investment = st.number_input("Monthly Investment (₹)", value=5000, step=500)
annual_return = st.number_input("Expected Annual Return (%)", value=12.0, step=0.1)
years = st.number_input("Investment Duration (Years)", value=10, step=1)

# Derived values
months = int(years * 12)
monthly_rate = annual_return / 12 / 100

# SIP Calculation
data = []
total = 0
cumulative_investment = 0

for month in range(1, months + 1):
    interest = total * monthly_rate
    total += monthly_investment + interest
    cumulative_investment += monthly_investment
    data.append([month, cumulative_investment, round(total, 2), round(interest, 2)])

df = pd.DataFrame(data, columns=["Month", "Cumulative Investment", "Total Value", "Interest Earned"])

# Output Table
st.subheader("📋 SIP Schedule")
st.dataframe(df.tail(10), use_container_width=True)

# Chart
st.subheader("📊 Investment Growth Chart")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Month"], df["Total Value"], label="Total Value", color="green")
ax.plot(df["Month"], df["Cumulative Investment"], label="Cumulative Investment", linestyle="--", color="blue")
ax.fill_between(df["Month"], df["Cumulative Investment"], df["Total Value"], color="lightgreen", alpha=0.3)
ax.set_xlabel("Month")
ax.set_ylabel("Value (₹)")
ax.legend()
st.pyplot(fig)

# Final Summary
st.success(f"💰 Final Corpus: ₹{df['Total Value'].iloc[-1]:,.2f}")
