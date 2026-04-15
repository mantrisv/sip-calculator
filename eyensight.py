import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import matplotlib.pyplot as plt
from newsapi import NewsApiClient
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("📊 AI Stock Analyzer")

ALPHA_KEY = st.secrets["ALPHA_VANTAGE_KEY"]

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

newsapi = NewsApiClient(api_key=st.secrets["NEWS_API_KEY"])


# ---------------- TECHNICAL DATA ----------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):

    url = (
        f"https://www.alphavantage.co/query?"
        f"function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_KEY}"
    )

    response = requests.get(url).json()

    if "Time Series (Daily)" not in response:
        raise Exception("Price Data Not Available")

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
        "50 DMA": round(df["50DMA"].iloc[-1], 2),
        "200 DMA": round(df["200DMA"].iloc[-1], 2)
        if not pd.isna(df["200DMA"].iloc[-1]) else "N/A",
        "52W High": round(df["High"].max(), 2),
        "52W Low": round(df["Low"].min(), 2),
        "Volume": int(df["Volume"].iloc[-1])
    }

    return tech, df


# ---------------- FUNDAMENTAL DATA ----------------
@st.cache_data(ttl=1800)
def get_screener_fundamentals(company_code):

    url = f"https://www.screener.in/company/{company_code}/consolidated/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    fundamentals = {}

    ratio_section = soup.find("ul", id="top-ratios")

    if ratio_section:

        ratios = ratio_section.find_all("li")

        for ratio in ratios:

            try:

                name = ratio.find("span", class_="name").text.strip()

                value = ratio.find("span", class_="number").text.strip()

                fundamentals[name] = value

            except:
                continue

    return fundamentals


# ---------------- NEWS ----------------
@st.cache_data(ttl=1800)
def get_news(company_name):

    try:

        articles = newsapi.get_everything(
            q=company_name,
            language="en",
            sort_by="publishedAt",
            page_size=5
        )

        return [x["title"] for x in articles["articles"]]

    except:

        return []


# ---------------- AI ANALYSIS ----------------
def generate_analysis(symbol, tech, fundamentals, news):

    prompt = f"""
    You are a professional equity analyst.

    Analyze this stock:

    Stock Name: {symbol}

    Technical Data:
    {tech}

    Fundamental Data:
    {fundamentals}

    News:
    {news}

    Format:
    1. Technical Outlook
    2. Fundamental View
    3. Key Risks
    4. Investment Recommendation
    """

    try:

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:

        return str(e)


# ---------------- USER INPUT ----------------
symbol = st.text_input(
    "Enter AlphaVantage Symbol (e.g. RELIANCE.BSE)",
    "RELIANCE.BSE"
)

company_code = st.text_input(
    "Enter Screener Code (e.g. RELIANCE)",
    "RELIANCE"
)


# ---------------- MAIN BUTTON ----------------
if st.button("Analyze Stock"):

    try:

        st.write("Fetching Technical Data...")

        tech, df = get_stock_data(symbol)

        st.write("Fetching Fundamental Data...")

        fundamentals = get_screener_fundamentals(company_code)

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Technical Data")

            st.json(tech)

        with col2:

            st.subheader("Fundamental Data")

            st.json(fundamentals)

        # ---------------- CHART ----------------
        st.subheader("Price Chart")

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(df.index, df["Close"], label="Close")
        ax.plot(df.index, df["50DMA"], label="50 DMA")
        ax.plot(df.index, df["200DMA"], label="200 DMA")

        ax.legend()

        st.pyplot(fig)

        # ---------------- NEWS ----------------
        st.write("Fetching News...")

        news = get_news(company_code)

        st.subheader("Latest News")

        if news:

            for n in news:

                st.write("•", n)

        else:

            st.write("No News Found")

        # ---------------- AI REPORT ----------------
        st.write("Generating AI Analysis...")

        analysis = generate_analysis(
            company_code,
            tech,
            fundamentals,
            news
        )

        st.subheader("AI Research Report")

        st.markdown(analysis)

    except Exception as e:

        st.error(str(e))