import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from newsapi import NewsApiClient
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])


# ---------------- TECHNICAL DATA ----------------
@st.cache_data(ttl=600)
def get_stock_data(ticker):

    ticker = ticker.upper()

    possible_symbols = [
        f"{ticker}.NS",
        f"{ticker}.BO"
    ]

    hist = None

    for sym in possible_symbols:

        try:

            stock = yf.Ticker(sym)

            hist = stock.history(period="1y")

            if not hist.empty:
                break

        except:
            continue

    if hist is None or hist.empty:
        raise Exception("Ticker not found")

    hist["50DMA"] = hist["Close"].rolling(50).mean()
    hist["200DMA"] = hist["Close"].rolling(200).mean()

    tech = {
        "Current Price": round(hist["Close"].iloc[-1], 2),
        "50 DMA": round(hist["50DMA"].iloc[-1], 2),
        "200 DMA": round(hist["200DMA"].iloc[-1], 2)
        if not pd.isna(hist["200DMA"].iloc[-1]) else "N/A",
        "52W High": round(hist["High"].max(), 2),
        "52W Low": round(hist["Low"].min(), 2),
        "Volume": int(hist["Volume"].iloc[-1])
    }

    return tech, hist


# ---------------- FUNDAMENTALS ----------------
@st.cache_data(ttl=1800)
def get_screener_fundamentals(ticker):

    ticker = ticker.upper()

    url = f"https://www.screener.in/company/{ticker}/consolidated/"

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
def get_news(ticker):

    try:

        articles = newsapi.get_everything(
            q=ticker,
            language="en",
            sort_by="publishedAt",
            page_size=5
        )

        return [x["title"] for x in articles["articles"]]

    except:
        return []


# ---------------- AI ----------------
def generate_analysis(ticker, tech, fundamentals, news):

    prompt = f"""
    Analyze stock:

    {ticker}

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
ticker = st.text_input(
    "Enter Ticker Symbol",
    "RELIANCE"
)


if st.button("Analyze Stock"):

    try:

        tech, hist = get_stock_data(ticker)

        fundamentals = get_screener_fundamentals(ticker)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Technical Data")
            st.json(tech)

        with col2:
            st.subheader("Fundamental Data")
            st.json(fundamentals)

        fig, ax = plt.subplots()

        ax.plot(hist.index, hist["Close"], label="Close")
        ax.plot(hist.index, hist["50DMA"], label="50 DMA")
        ax.plot(hist.index, hist["200DMA"], label="200 DMA")

        ax.legend()

        st.pyplot(fig)

        news = get_news(ticker)

        for n in news:
            st.write("•", n)

        analysis = generate_analysis(
            ticker,
            tech,
            fundamentals,
            news
        )

        st.markdown(analysis)

    except Exception as e:

        st.error(str(e))