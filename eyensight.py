import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from newsapi import NewsApiClient

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

TWELVE_KEY = st.secrets["TWELVE_DATA_KEY"]

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])


# ---------------- PRICE FETCH ----------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):

    tickers = [
        f"{symbol}:NSE",
        f"{symbol}:BSE"
    ]

    data = None

    for ticker in tickers:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={ticker}"
            f"&interval=1day"
            f"&outputsize=250"
            f"&apikey={TWELVE_KEY}"
        )

        response = requests.get(url).json()

        if "values" in response:

            data = response["values"]

            break

    if not data:
        raise Exception("Stock not found in NSE/BSE")

    df = pd.DataFrame(data)

    df = df.astype({
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float
    })

    df["datetime"] = pd.to_datetime(df["datetime"])

    df = df.sort_values("datetime")

    df["50DMA"] = df["close"].rolling(50).mean()
    df["200DMA"] = df["close"].rolling(200).mean()

    tech = {
        "Current Price": round(df["close"].iloc[-1], 2),
        "50 DMA": round(df["50DMA"].iloc[-1], 2),
        "200 DMA": round(df["200DMA"].iloc[-1], 2)
        if not pd.isna(df["200DMA"].iloc[-1]) else "N/A",
        "52W High": round(df["high"].max(), 2),
        "52W Low": round(df["low"].min(), 2),
        "Volume": int(df["volume"].iloc[-1])
    }

    return tech, df


# ---------------- FUNDAMENTALS ----------------
@st.cache_data(ttl=1800)
def get_screener_fundamentals(symbol):

    url = f"https://www.screener.in/company/{symbol}/consolidated/"

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    soup = BeautifulSoup(response.text, "html.parser")

    fundamentals = {}

    ratio_section = soup.find("ul", id="top-ratios")

    if ratio_section:

        for ratio in ratio_section.find_all("li"):

            try:

                name = ratio.find("span", class_="name").text.strip()

                value = ratio.find("span", class_="number").text.strip()

                fundamentals[name] = value

            except:
                continue

    return fundamentals


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


# ---------------- AI ----------------
def generate_analysis(symbol, tech, fundamentals, news):

    prompt = f"""
    Analyze stock {symbol}

    Technical Data:
    {tech}

    Fundamental Data:
    {fundamentals}

    News:
    {news}

    Give:
    1. Technical Outlook
    2. Fundamental Analysis
    3. Risks
    4. Recommendation
    """

    response = model.generate_content(prompt)

    return response.text


# ---------------- UI ----------------
symbol = st.text_input("Enter Stock Symbol", "RELIANCE")


if st.button("Analyze Stock"):

    try:

        st.write("Fetching Price Data...")

        tech, df = get_stock_data(symbol.upper())

        st.write("Fetching Fundamentals...")

        fundamentals = get_screener_fundamentals(symbol.upper())

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Technical Data")
            st.json(tech)

        with col2:
            st.subheader("Fundamental Data")
            st.json(fundamentals)

        st.subheader("Price Chart")

        fig, ax = plt.subplots()

        ax.plot(df["datetime"], df["close"], label="Close")
        ax.plot(df["datetime"], df["50DMA"], label="50 DMA")
        ax.plot(df["datetime"], df["200DMA"], label="200 DMA")

        ax.legend()

        st.pyplot(fig)

        news = get_news(symbol)

        for n in news:
            st.write("•", n)

        analysis = generate_analysis(
            symbol,
            tech,
            fundamentals,
            news
        )

        st.markdown(analysis)

    except Exception as e:

        st.error(str(e))