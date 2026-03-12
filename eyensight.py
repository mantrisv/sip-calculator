import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from newsapi import NewsApiClient

st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

# ---------------- GEMINI CONFIG ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- NEWS API ----------------
newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])

# ---------------- GET STOCK DATA ----------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="1y")

    hist["50DMA"] = hist["Close"].rolling(50).mean()
    hist["200DMA"] = hist["Close"].rolling(200).mean()

    tech = {
        "Current Price": round(hist["Close"].iloc[-1],2),
        "50DMA": round(hist["50DMA"].iloc[-1],2),
        "200DMA": round(hist["200DMA"].iloc[-1],2),
        "52W High": round(hist["High"].max(),2),
        "52W Low": round(hist["Low"].min(),2),
        "Volume": int(hist["Volume"].iloc[-1])
    }

    info = ticker.info

    fundamentals = {
        "Market Cap": info.get("marketCap"),
        "PE Ratio": info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "Revenue": info.get("totalRevenue"),
        "Profit Margin": info.get("profitMargins"),
        "Dividend Yield": info.get("dividendYield"),
        "Beta": info.get("beta")
    }

    statements = {
        "Income Statement": ticker.financials,
        "Balance Sheet": ticker.balance_sheet,
        "Cashflow": ticker.cashflow
    }

    return tech, fundamentals, statements, hist

# ---------------- NEWS FETCH ----------------
@st.cache_data(ttl=1800)
def get_news(symbol):

    try:
        articles = newsapi.get_everything(
            q=symbol,
            language="en",
            sort_by="publishedAt",
            page_size=5
        )

        news = []

        for article in articles["articles"]:
            news.append(article["title"])

        return news

    except:
        return []

# ---------------- AI ANALYSIS ----------------
def generate_analysis(symbol, tech, fundamentals, statements, news_text):

    prompt = f"""
    You are an equity research analyst.

    Generate a structured research report for {symbol}.

    Technical Data:
    {tech}

    Fundamental Data:
    {fundamentals}

    Financial Statements:
    {statements}

    News:
    {news_text}

    Format:
    1. Technical Outlook
    2. Fundamental View
    3. News Sentiment
    4. Key Risks
    5. Investment Recommendation
    """

    try:

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:

        return f"AI generation failed: {e}"

# ---------------- USER INPUT ----------------
symbol = st.text_input("Enter Stock Symbol", "RELIANCE.NS")

if st.button("Analyze Stock"):

    st.write("Fetching stock data...")

    try:

        tech, fundamentals, statements, hist = get_stock_data(symbol)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Technical Data")
            st.json(tech)

        with col2:
            st.subheader("Fundamental Metrics")
            st.json(fundamentals)

        # ---------------- CHART ----------------
        st.subheader("Price Chart")

        fig, ax = plt.subplots()

        ax.plot(hist.index, hist["Close"], label="Close")
        ax.plot(hist.index, hist["50DMA"], label="50DMA")
        ax.plot(hist.index, hist["200DMA"], label="200DMA")

        ax.legend()

        st.pyplot(fig)

        # ---------------- FINANCIALS ----------------
        st.subheader("Financial Statements")

        for name, df in statements.items():

            st.write(name)

            if df is not None and not df.empty:

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

            st.write("No recent news found")

        news_text = " ".join(news)

        # ---------------- AI ANALYSIS ----------------
        st.write("Generating AI analysis...")

        analysis = generate_analysis(symbol, tech, fundamentals, statements, news_text)

        st.markdown(analysis)

    except Exception as e:

        st.error(f"Error fetching data: {e}")