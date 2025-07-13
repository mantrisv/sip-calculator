
import streamlit as st
import pandas as pd

st.title("📊 Portfolio Tracker with Tabs + Low Weightage View")

uploaded_file = st.file_uploader("Upload your portfolio Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)

    # Normalize scrip names
    df['ScripName'] = df['ScripName'].str.strip().str.upper()
    df['% wtge'] = pd.to_numeric(df['% wtge'], errors='coerce')

    # Categorize holding periods
    def categorize_holding(days):
        if pd.isna(days):
            return 'Unknown'
        if days < 90:
            return 'Less than 3M'
        elif days < 365:
            return '3M–1Y'
        elif days < 1095:
            return '1Y–3Y'
        else:
            return '3Y+'

    def holding_status(days):
        if pd.isna(days):
            return 'Unknown'
        return 'Short Term' if days < 365 else 'Long Term'

    def classify_underperformance(days, return_pct):
        if pd.isna(days) or pd.isna(return_pct):
            return 'Unknown'
        if days <= 90:
            return 'Too Early'
        if days > 180:
            if return_pct < 0:
                return 'Dud'
            elif return_pct < 9:
                return 'Sluggish'
        if days > 90:
            if return_pct < 0:
                return 'Dragger'
            elif return_pct < 9:
                return 'Not Moving'
        return 'Healthy'

    def tag_underperformance(row):
        return classify_underperformance(row['holding period'], row['%tage'])

    df['HoldingCategory'] = df['holding period'].apply(categorize_holding)
    df['HoldingPeriodStatus'] = df['holding period'].apply(holding_status)
    df['UnderperformanceTag'] = df.apply(tag_underperformance, axis=1)

    # Consolidate holdings
    consolidated = df.groupby('ScripName').agg({
        'Quantity': 'sum',
        'Buying Quanta': 'sum',
        'Selling Quanta': 'sum',
        'Gain/Loss': 'sum',
        '% wtge': 'sum',
        'HoldingPeriodStatus': 'first',
        'UnderperformanceTag': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
    }).reset_index()

    consolidated['Status'] = consolidated['Gain/Loss'].apply(lambda x: 'Positive' if x > 0 else 'Negative' if x < 0 else 'Neutral')

    # Sidebar filters
    status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Positive", "Negative", "Neutral"])
    holding_filter = st.sidebar.selectbox("Filter by Holding Period", ["All", "Short Term", "Long Term"])

    filtered_df = consolidated.copy()

    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]

    if holding_filter != "All":
        filtered_df = filtered_df[filtered_df['HoldingPeriodStatus'] == holding_filter]

    filter_mode = st.sidebar.radio("Scrip Filter Mode", ["Include Only", "Exclude"])
    selected_scrips = st.sidebar.multiselect("Select Scrips", options=sorted(consolidated['ScripName'].unique().tolist()))

    if selected_scrips:
        if filter_mode == "Include Only":
            filtered_df = filtered_df[filtered_df['ScripName'].isin(selected_scrips)]
        else:
            filtered_df = filtered_df[~filtered_df['ScripName'].isin(selected_scrips)]

    # Portfolio metrics
    total_invested = filtered_df['Buying Quanta'].sum()
    total_current_value = filtered_df['Selling Quanta'].sum()
    total_weight = filtered_df['% wtge'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested Value (₹)", f"{total_invested:,.2f}")
    col2.metric("Total Current Value (₹)", f"{total_current_value:,.2f}")
    col3.metric("Sum of % Weights", f"{total_weight:.2f}%")

    # Main table
    st.subheader("🧾 Consolidated Holdings")
    st.dataframe(pd.concat([filtered_df, pd.DataFrame([{
        'ScripName': 'TOTAL',
        'Quantity': filtered_df['Quantity'].sum(),
        'Buying Quanta': total_invested,
        'Selling Quanta': total_current_value,
        'Gain/Loss': filtered_df['Gain/Loss'].sum(),
        '% wtge': total_weight,
        'HoldingPeriodStatus': ''
    }])], ignore_index=True))

    # Tabs section
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⭐ Top 5 Holdings",
        "🔟 Top 10 Holdings",
        "📌 Insights & Alerts",
        "🧿 Sub-1% Holdings",
        "🐢 Underperformers"
    ])

    with tab1:
        top_5 = consolidated.sort_values(by='% wtge', ascending=False).head(5)
        top_5_total = pd.DataFrame([{
            'ScripName': 'TOTAL',
            '% wtge': top_5['% wtge'].sum(),
            'Gain/Loss': top_5['Gain/Loss'].sum(),
            'Buying Quanta': top_5['Buying Quanta'].sum(),
            'Selling Quanta': top_5['Selling Quanta'].sum(),
            'HoldingPeriodStatus': ''
        }])
        st.dataframe(pd.concat([top_5[['ScripName', '% wtge', 'Gain/Loss', 'Buying Quanta', 'Selling Quanta', 'HoldingPeriodStatus']], top_5_total], ignore_index=True))

    with tab2:
        top_10 = consolidated.sort_values(by='% wtge', ascending=False).head(10)
        top_10_total = pd.DataFrame([{
            'ScripName': 'TOTAL',
            '% wtge': top_10['% wtge'].sum(),
            'Gain/Loss': top_10['Gain/Loss'].sum(),
            'Buying Quanta': top_10['Buying Quanta'].sum(),
            'Selling Quanta': top_10['Selling Quanta'].sum(),
            'HoldingPeriodStatus': ''
        }])
        st.dataframe(pd.concat([top_10[['ScripName', '% wtge', 'Gain/Loss', 'Buying Quanta', 'Selling Quanta', 'HoldingPeriodStatus']], top_10_total], ignore_index=True))

    with tab3:
        insights = consolidated[
            (consolidated['% wtge'] > 2.0) & (consolidated['Gain/Loss'] < 0)
        ].sort_values(by='% wtge', ascending=False)

        if insights.empty:
            st.info("✅ No high-weight negative scrips found.")
        else:
            for _, row in insights.iterrows():
                st.warning(f"⚠️ {row['ScripName']} has a high portfolio weight of {row['% wtge']:.2f}% but is running at a loss of ₹{abs(row['Gain/Loss']):,.0f}.")

    with tab4:
        low_weight = consolidated[consolidated['% wtge'] < 1.0]
        total_low_weight = low_weight['% wtge'].sum()
        st.markdown(f"🧮 **Total Weight of Sub-1% Holdings:** {total_low_weight:.2f}%")
        st.dataframe(low_weight[['ScripName', '% wtge', 'Gain/Loss', 'HoldingPeriodStatus']])

    with tab5:
        underperf = consolidated[consolidated['UnderperformanceTag'].isin(['Dud', 'Sluggish', 'Dragger', 'Not Moving'])]
        if underperf.empty:
            st.success("🚀 No underperformers detected! Good going.")
        else:
            st.markdown("### 🐢 Stocks Tagged as Underperformers")
            st.dataframe(underperf[['ScripName', '% wtge', 'Gain/Loss', 'UnderperformanceTag', 'HoldingPeriodStatus']].sort_values(by='% wtge', ascending=False))
