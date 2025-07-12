import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper functions ---
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

def classify_high_low_delivery(hl_df_with_symbols, delivery_df):
    merged_df = hl_df_with_symbols.merge(delivery_df, on='SYMBOL', how='left')
    merged_df = merged_df.dropna(subset=['DELIV_PERC'])

    def interpret(row):
        if row['NEW_STATUS'] == 'H':
            if row['DELIV_PERC'] < 30:
                return "52W High on Low Delivery – Possible churn"
            else:
                return "52W High on High Delivery – Strong hands entry"
        elif row['NEW_STATUS'] == 'L':
            if row['DELIV_PERC'] < 30:
                return "52W Low on Low Delivery – Selling subsiding"
            else:
                return "52W Low on High Delivery – Panic or distribution"
        return None

    merged_df['INTERPRETATION'] = merged_df.apply(interpret, axis=1)
    return merged_df[['SECURITY', 'NEW_STATUS', 'DELIV_PERC', 'INTERPRETATION']]

def add_symbols_to_hl(hl_df, mcap_df):
    mcap_df = mcap_df.copy()
    mcap_df.columns = mcap_df.columns.str.strip()
    col_map = {col: col.replace('\xa0', ' ').replace('\u200b', '').strip() for col in mcap_df.columns}
    mcap_df.rename(columns=col_map, inplace=True)
    symbol_map = dict(zip(mcap_df['Security Name'].str.strip(), mcap_df['Symbol'].str.strip()))
    hl_df['SYMBOL'] = hl_df['SECURITY'].str.strip().map(symbol_map)
    return hl_df

# --- Streamlit UI ---
st.title("📈 Morning Market Brief - Dealing Desk")

# Inputs
outlook = st.text_input("Nifty Opening Outlook", "Nifty likely to open flat tracking global cues.")
support = st.text_input("Support Levels", "24300 / 24200")
resistance = st.text_input("Resistance Levels", "24500 / 24630")

st.subheader("📤 Upload All 4 Files (GL, HL, MCAP, Delivery)")

uploaded_files = st.file_uploader(
    "📥 Drag and drop or browse files",
    type=["csv", "dat"],
    accept_multiple_files=True
)

# Initialize placeholders
gl_file = hl_file = mcap_file = delivery_file = None

# Smart auto-identify based on filename
for file in uploaded_files or []:
    name = file.name.lower()
    if "gl" in name and name.endswith(".csv"):
        gl_file = file
    elif "hl" in name and name.endswith(".csv"):
        hl_file = file
    elif "mcap" in name and name.endswith(".csv"):
        mcap_file = file
    elif name.endswith(".dat"):
        delivery_file = file


today = datetime.now()
brief_text = f"""📰 Morning Brief – {today.strftime('%d %b %Y')}

🔹 Nifty View: {outlook}

📈 Nifty Levels:
- Support: {support}
- Resistance: {resistance}
"""

commentary = ""
top_500 = None
mcap_df = pd.DataFrame()

# --- Parse MCAP file ---
if mcap_file:
    try:
        mcap_df = pd.read_csv(mcap_file)
        mcap_df.columns = mcap_df.columns.str.strip()
        col_map = {col: col.replace('\xa0', ' ').replace('\u200b', '').strip() for col in mcap_df.columns}
        mcap_df.rename(columns=col_map, inplace=True)
        mcap_df = mcap_df[['Symbol', 'Security Name', 'Market Cap(Rs.)']].dropna()
        mcap_df['Market Cap(Rs.)'] = pd.to_numeric(mcap_df['Market Cap(Rs.)'], errors='coerce')
        mcap_df = mcap_df.sort_values(by='Market Cap(Rs.)', ascending=False)
        top_500 = set(mcap_df.head(500)['Symbol'].str.strip())
    except Exception as e:
        st.error(f"Error reading MCAP file: {e}")

# --- Parse GL file ---
gainers = pd.DataFrame()
losers = pd.DataFrame()
if gl_file:
    try:
        gl_df = pd.read_csv(gl_file)
        gainers, losers = get_gainers_losers(gl_df, top_500)
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

# --- Parse HL file ---
hl_df = pd.DataFrame()
if hl_file:
    try:
        hl_df = pd.read_csv(hl_file)
        hl_df = get_52w_highs_lows(hl_df)
        if not hl_df.empty:
            brief_text += "\n🚀 52-Week Highs / Lows:\n"
            for _, row in hl_df.iterrows():
                status = "High" if row['NEW_STATUS'] == 'H' else "Low"
                brief_text += f"- {row['SECURITY']} – {status}\n"
    except Exception as e:
        st.error(f"Error reading HL file: {e}")

# --- Parse Delivery file ---
delivery_df = pd.DataFrame()
top_delivery = pd.DataFrame()
if delivery_file:
    try:
        lines = delivery_file.getvalue().decode('utf-8').splitlines()
        data_lines = lines[4:]
        records = []
        for line in data_lines:
            parts = line.strip().split(',')
            if len(parts) >= 7:
                segment = parts[3].strip()
                symbol = parts[2].strip()
                try:
                    deliv_perc = float(parts[6])
                    if segment == 'EQ':
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

# --- Combine HL + SYMBOL + Delivery
if not hl_df.empty and not delivery_df.empty and not mcap_df.empty:
    try:
        hl_df = add_symbols_to_hl(hl_df, mcap_df)
        hl_analysis = classify_high_low_delivery(hl_df, delivery_df)
        if not hl_analysis.empty:
            brief_text += "\n📊 Delivery Insight on 52W Highs/Lows:\n"
            for _, row in hl_analysis.iterrows():
                brief_text += f"- {row['SECURITY']}: {row['INTERPRETATION']} ({row['DELIV_PERC']}%)\n"
    except Exception as e:
        st.warning(f"Could not cross-link HL with delivery: {e}")

# --- AI Commentary ---
commentary += "🧠 AI Commentary:\n"

# Hybrid delivery insight
if not delivery_df.empty:
    high_deliv_top_100 = delivery_df.sort_values(by='DELIV_PERC', ascending=False).head(100)
    avg_top_100 = high_deliv_top_100['DELIV_PERC'].mean()
    median_all = delivery_df['DELIV_PERC'].median()

    if avg_top_100 > 60:
        commentary += f"• Strong delivery interest in top 100 stocks (avg {avg_top_100:.1f}%) – likely smart money activity.\n"
    if median_all > 45:
        commentary += f"• Overall delivery trend across top 500 stocks remains healthy (median {median_all:.1f}%).\n"


# --- Output ---
if st.button("📋 Generate Morning Brief"):
    st.text_area("📋 Copy this brief", brief_text, height=400)
    if commentary.strip():
        st.text_area("🧠 Market View", commentary, height=150)
    st.download_button("💾 Download as .txt", brief_text + "\n\n" + commentary, file_name="morning_brief.txt")
    st.success("Brief ready.")
