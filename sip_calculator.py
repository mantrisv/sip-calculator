
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets credentials from local file
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("client_secret.json", scopes=scope)
client = gspread.authorize(creds)

# Logging function to write data to Google Sheet
def log_user_data(name, email, mobile):
    try:
        sheet = client.open("Visitor_Log").sheet1
        sheet.append_row([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            name, email, mobile
        ])
    except Exception as e:
        st.error("Could not log to Google Sheet.")
        st.exception(e)

# Streamlit App UI
st.set_page_config(page_title="SIP Calculator", layout="centered")
st.title("📈 SIP Calculator")

tab1, tab2, spacer, tab3 = st.tabs(["Forward SIP", "Reverse SIP", "        ", "💬 Let's Get Connected"])


# ---------- FORWARD CALCULATION ----------
with tab1:
    st.header("🔹 Forward SIP Calculator")
    monthly_investment = st.number_input("Monthly Investment (₹)", min_value=100, step=100)
    annual_rate = st.number_input("Expected Annual Return (%)", min_value=1.0, value=12.0)
    years = st.number_input("Investment Period (Years)", min_value=1, value=10)

    r = annual_rate / 12 / 100
    n = int(years * 12)

    fv = monthly_investment * (((1 + r) ** n - 1) / r) * (1 + r)
    total_invested = monthly_investment * n
    gain = fv - total_invested

    st.subheader(f"📌 Future Value: ₹{fv:,.0f}")
    st.write(f"💰 Total Invested: ₹{total_invested:,.0f}")
    st.write(f"📈 Estimated Gain: ₹{gain:,.0f}")

    # Plotting
    df = pd.DataFrame({
        "Month": list(range(1, n + 1)),
        "Invested Amount": [monthly_investment * i for i in range(1, n + 1)],
        "Future Value": [monthly_investment * (((1 + r) ** i - 1) / r) * (1 + r) for i in range(1, n + 1)]
    })

    fig, ax = plt.subplots()
    ax.plot(df["Month"], df["Invested Amount"], label="Invested", color="blue")
    ax.plot(df["Month"], df["Future Value"], label="Value", color="green")
    ax.set_title("SIP Growth Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    ax.legend()
    st.pyplot(fig)

# ---------- REVERSE CALCULATION ----------
with tab2:
    st.header("🔁 Reverse SIP Calculator")
    goal_amount = st.number_input("Target Amount (₹)", min_value=10000, step=10000, value=500000)
    reverse_annual_rate = st.number_input("Expected Annual Return (%)", min_value=1.0, value=12.0, key="reverse_rate")
    reverse_years = st.number_input("Investment Period (Years)", min_value=1, value=10, key="reverse_years")

    r_rev = reverse_annual_rate / 12 / 100
    n_rev = int(reverse_years * 12)

    if r_rev > 0:
        required_sip = goal_amount * r_rev / (((1 + r_rev) ** n_rev - 1) * (1 + r_rev))
        st.subheader(f"💸 Required Monthly SIP: ₹{required_sip:,.0f}")
    else:
        st.warning("Interest rate must be greater than 0")

# -------------- Visitor Info Tab ----------------
with tab3:
    st.header("📬 Let's Stay in Touch!")

    with st.form("visitor_form_tab"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        mobile = st.text_input("Your Mobile")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not email:
                st.warning("Email is required.")
            else:
                st.success("Thanks! Details received.")
                log_user_data(name, email, mobile)

    st.markdown("""
    🔹 Want to stay updated with new features?  
    🔹 Have feedback or suggestions?  
    Just fill in your details and we’ll reach out!
    """)


