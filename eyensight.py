import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from newsapi import NewsApiClient

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

ALPHA_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])


# ---------------- FETCH STOCK DATA ----------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):

    # DAILY PRICE DATA
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_KEY}"

    response = requests.get(url).json()

    if "Time Series (Daily)" not in response:
        raise Exception("Invalid Symbol / API Limit Reached")

    ts = response["Time Series (Daily)"]

    df = pd.DataFrame(ts).T
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    })

    df = df.astype(float)

    df.index = pd.to_datetime(df.index)

    df = df.sort_index()

    df["50DMA"] = df["Close"].rolling(50).mean()
    df["200DMA"] = df["Close"].rolling(200).mean()

    tech = {
        "Current Price": round(df["Close"].iloc[-1], 2),
        "50DMA": round(df["50DMA"].iloc[-1], 2),
        "200DMA": round(df["200DMA"].iloc[-1], 2),
        "52W High": round(df["High"].max(), 2),
        "52W Low": round(df["Low"].min(), 2),
        "Volume": int(df["Volume"].iloc[-1])
    }

    # FUNDAMENTALS
    overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"

    overview = requests.get(overview_url).json()

    fundamentals = {
        "Market Cap": overview.get("MarketCapitalization", "N/A"),
        "PE Ratio": overview.get("PERatio", "N/A"),
        "EPS": overview.get("EPS", "N/A"),
        "Dividend Yield": overview.get("DividendYield", "N/A"),
        "Beta": overview.get("Beta", "N/A")
    }

    return tech, fundamentals, df


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

        return [x["title"] for x in articles["articles"]]

    except:
        return []


# ---------------- AI REPORT ----------------
def generate_analysis(symbol, tech, fundamentals, news):

    prompt = f"""
    Analyze stock {symbol}

    Technicals:
    {tech}

    Fundamentals:
    {fundamentals}

    News:
    {news}

    Give:
    1. Technical Outlook
    2. Fundamental View
    3. Risks
    4. Investment Recommendation
    """

    try:
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:

        return str(e)


# ---------------- UI ----------------
symbol = st.text_input("Enter Stock Symbol", "RELIANCE.BSE")

if st.button("Analyze Stock"):

    try:

        st.write("Fetching stock data...")

        tech, fundamentals, df = get_stock_data(symbol)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Technical Data")
            st.json(tech)

        with col2:
            st.subheader("Fundamentals")
            st.json(fundamentals)

        st.subheader("Price Chart")

        fig, ax = plt.subplots()

        ax.plot(df.index, df["Close"], label="Close")
        ax.plot(df.index, df["50DMA"], label="50DMA")
        ax.plot(df.index, df["200DMA"], label="200DMA")

        ax.legend()

        st.pyplot(fig)

        news = get_news(symbol)

        st.subheader("Latest News")

        for n in news:
            st.write("•", n)

        st.subheader("AI Analysis")

        analysis = generate_analysis(symbol, tech, fundamentals, news)

        st.markdown(analysis)

    except Exception as e:

        st.error(f"Error: {e}")