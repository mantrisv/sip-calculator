import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper functions ---
def get_top_traded(df):
    if 'SECURITY' in df.columns and 'NET_TRDQTY' in df.columns:
        df = df.sort_values(by='NET_TRDQTY', ascending=False)
        return df[['SECURITY', 'NET_TRDQTY']].head(5)
    return None

def get_gainers_losers(gl_df, top_500=None):
    gl_df = gl_df.dropna(subset=['SECURITY', 'PERCENT_CG', 'GAIN_LOSS'])
    gl_df['GAIN_LOSS'] = gl_df['GAIN_LOSS'].astype(str).str.strip()
    gl_df['SECURITY'] = gl_df['SECURITY'].astype(str).str.strip()
    gl_df['PERCENT_CG'] = pd.to_numeric(gl_df['PERCENT_CG'], errors='coerce')
    gl_df = gl_df.dropna(subset=['PERCENT_CG'])
    if top_500:
        gl_df = gl_df[gl_df['SECURITY'].isin(top_500)]
    gainers = gl_df[gl_df['GAIN_LOSS'] == 'G'].sort_values(by='PERCENT_CG', ascending=False).head(3)
    losers = gl_df[gl_df['GAIN_LOSS'] == 'L'].sort_values(by='PERCENT_CG').head(3)
    return gainers, losers

def get_52w_highs_lows(hl_df):
    hl_df = hl_df[hl_df['NEW_STATUS'].isin(['H', 'L'])]
    return hl_df[['SECURITY', 'NEW_STATUS']].head(5)

# --- Streamlit UI ---
st.title("📈 Morning Market Brief - Dealing Desk")

# Inputs
outlook = st.text_input("Nifty Opening Outlook", "Nifty likely to open flat tracking global cues.")
support = st.text_input("Support Levels", "24300 / 24200")
resistance = st.text_input("Resistance Levels", "24500 / 24630")

st.subheader("📤 Upload Bhavcopy CSVs")
pr_file = st.file_uploader("Upload PR File (e.g., PRddmmyy.csv)", type="csv")
gl_file = st.file_uploader("Upload GL File (e.g., GLddmmyy.csv)", type="csv")
hl_file = st.file_uploader("Upload HL File (e.g., HLddmmyy.csv)", type="csv")
delivery_file = st.file_uploader("Upload Delivery File (e.g., MTO_ddmmyy.DAT)", type=["DAT", "dat"])
mcap_file = st.file_uploader("Upload MCAP File (e.g., MCAPddmmyy.csv)", type="csv")

today = datetime.now()
brief_text = f"""📰 Morning Brief – {today.strftime('%d %b %Y')}

🔹 Nifty View: {outlook}

📈 Nifty Levels:
- Support: {support}
- Resistance: {resistance}
"""

# Parse MCAP file
top_500 = None
if mcap_file:
    try:
        mcap_df = pd.read_csv(mcap_file)
        mcap_df = mcap_df[['Symbol', 'Market Cap(Rs.)              ']].dropna()
        mcap_df['Market Cap(Rs.)              '] = pd.to_numeric(mcap_df['Market Cap(Rs.)              '], errors='coerce')
        mcap_df = mcap_df.sort_values(by='Market Cap(Rs.)              ', ascending=False)
        top_500 = set(mcap_df.head(500)['Symbol'].str.strip())
    except Exception as e:
        st.error(f"Error reading MCAP file: {e}")

# Parse PR file
if pr_file:
    try:
        pr_df = pd.read_csv(pr_file, on_bad_lines='skip', encoding='utf-8', engine='python')
        top_traded_df = get_top_traded(pr_df)
        if top_traded_df is not None:
            brief_text += "\n📌 Top Traded Stocks:\n"
            for _, row in top_traded_df.iterrows():
                brief_text += f"- {row['SECURITY']} – {row['NET_TRDQTY']} qty\n"
    except Exception as e:
        st.error(f"Error reading PR file: {e}")

# Parse GL file
if gl_file:
    try:
        gl_df = pd.read_csv(gl_file)
        gainers, losers = get_gainers_losers(gl_df, top_500)
        cmp_column = 'CLOSE_PRIC' if 'CLOSE_PRIC' in gl_df.columns else None
        if not gainers.empty:
            brief_text += "\n📈 Gainers:\n"
            for _, row in gainers.iterrows():
                brief_text += f"- {row['SECURITY']} – up {round(row['PERCENT_CG'], 1)}%\n"
        if not losers.empty:
            brief_text += "\n📉 Losers:\n"
            for _, row in losers.iterrows():
                brief_text += f"- {row['SECURITY']} – down {abs(round(row['PERCENT_CG'], 1))}%\n"
    except Exception as e:
        st.error(f"Error reading GL file: {e}")

# Parse HL file
if hl_file:
    try:
        hl_df = pd.read_csv(hl_file)
        highs_lows_df = get_52w_highs_lows(hl_df)
        if not highs_lows_df.empty:
            brief_text += "\n🚀 52-Week Highs / Lows:\n"
            for _, row in highs_lows_df.iterrows():
                status = "High" if row['NEW_STATUS'] == 'H' else "Low"
                brief_text += f"- {row['SECURITY']} – {status}\n"
    except Exception as e:
        st.error(f"Error reading HL file: {e}")

# Parse Delivery file (.DAT)
if delivery_file:
    try:
        lines = delivery_file.getvalue().decode('utf-8').splitlines()
        data_lines = lines[4:]  # Skip headers
        records = []
        for line in data_lines:
            parts = line.strip().split(',')
            if len(parts) >= 7:
                symbol = parts[2].strip()
                try:
                    deliv_perc = float(parts[6])
                    records.append((symbol, deliv_perc))
                except:
                    continue
        delivery_df = pd.DataFrame(records, columns=['SYMBOL', 'DELIV_PERC'])
        if top_500:
            delivery_df = delivery_df[delivery_df['SYMBOL'].isin(top_500)]
        top_delivery = delivery_df.sort_values(by='DELIV_PERC', ascending=False).head(3)
        if not top_delivery.empty:
            brief_text += "\n📦 High Delivery % Stocks:\n"
            for _, row in top_delivery.iterrows():
                brief_text += f"- {row['SYMBOL']} – {row['DELIV_PERC']}%\n"
    except Exception as e:
        st.error(f"Error reading Delivery file: {e}")

# Output Brief
if st.button("📋 Generate Morning Brief"):
    st.text_area("📋 Copy this brief", brief_text, height=400)
    st.download_button("💾 Download as .txt", brief_text, file_name="morning_brief.txt")
    st.success("Brief ready.")
