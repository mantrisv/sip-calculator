import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from newsapi import NewsApiClient

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

# ---------------- API CONFIG ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])


# ---------------- STOCK DATA ----------------
@st.cache_data(ttl=600)
def get_stock_data(symbol, load_financials=False):

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="1y")

    if hist.empty:
        raise Exception("No stock data found.")

    hist["50DMA"] = hist["Close"].rolling(50).mean()
    hist["200DMA"] = hist["Close"].rolling(200).mean()

    try:
        info = ticker.fast_info
    except:
        info = {}

    tech = {
        "Current Price": round(hist["Close"].iloc[-1], 2),
        "50DMA": round(hist["50DMA"].iloc[-1], 2),
        "200DMA": round(hist["200DMA"].iloc[-1], 2),
        "52W High": round(hist["High"].max(), 2),
        "52W Low": round(hist["Low"].min(), 2),
        "Volume": int(hist["Volume"].iloc[-1])
    }

    fundamentals = {
        "Market Cap": info.get("market_cap", "N/A"),
        "PE Ratio": info.get("trailing_pe", "N/A"),
        "EPS": info.get("eps", "N/A"),
        "Dividend Yield": info.get("dividend_yield", "N/A"),
        "Beta": info.get("beta", "N/A")
    }

    statements = {}

    if load_financials:

        try:
            statements["Income Statement"] = ticker.financials
        except:
            statements["Income Statement"] = pd.DataFrame()

        try:
            statements["Balance Sheet"] = ticker.balance_sheet
        except:
            statements["Balance Sheet"] = pd.DataFrame()

        try:
            statements["Cashflow"] = ticker.cashflow
        except:
            statements["Cashflow"] = pd.DataFrame()

    return tech, fundamentals, statements, hist


# ---------------- NEWS ----------------
@st.cache_data(ttl=1800)
def get_news(symbol):

    try:
        articles = newsapi.get_everything(
            q=symbol,
            language="en",
            sort_by="publishedAt",
            page_size=5
        )

        return [article["title"] for article in articles["articles"]]

    except:
        return []


# ---------------- AI ANALYSIS ----------------
def generate_analysis(symbol, tech, fundamentals, news_text):

    prompt = f"""
    You are a professional equity research analyst.

    Analyze stock: {symbol}

    Technical Metrics:
    {tech}

    Fundamental Metrics:
    {fundamentals}

    Recent News:
    {news_text}

    Format Response As:
    1. Technical Outlook
    2. Fundamental Analysis
    3. News Sentiment
    4. Risks
    5. Investment Recommendation
    """

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI generation failed: {e}"


# ---------------- USER INPUT ----------------
symbol = st.text_input("Enter Stock Symbol", "RELIANCE.NS")

load_financials = st.checkbox("Load Detailed Financial Statements")

if st.button("Analyze Stock"):

    try:

        st.write("Fetching stock data...")

        tech, fundamentals, statements, hist = get_stock_data(
            symbol,
            load_financials
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Technical Data")
            st.json(tech)

        with col2:
            st.subheader("Fundamental Metrics")
            st.json(fundamentals)

        # ---------------- CHART ----------------
        st.subheader("Price Chart")

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(hist.index, hist["Close"], label="Close")
        ax.plot(hist.index, hist["50DMA"], label="50DMA")
        ax.plot(hist.index, hist["200DMA"], label="200DMA")

        ax.legend()

        st.pyplot(fig)

        # ---------------- FINANCIALS ----------------
        if load_financials:

            st.subheader("Financial Statements")

            for name, df in statements.items():

                st.write(f"### {name}")

                if not df.empty:
                    st.dataframe(df)

                else:
                    st.write("No data available")

        # ---------------- NEWS ----------------
        st.write("Fetching news...")

        news = get_news(symbol)

        st.subheader("Latest News")

        if news:

            for n in news:
                st.write("•", n)

        else:
            st.write("No recent news found.")

        news_text = " ".join(news)

        # ---------------- AI ANALYSIS ----------------
        st.write("Generating AI Analysis...")

        analysis = generate_analysis(
            symbol,
            tech,
            fundamentals,
            news_text
        )

        st.markdown(analysis)

    except Exception as e:

        st.error(f"Error: {e}")