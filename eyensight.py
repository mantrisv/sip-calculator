import streamlit as st
import yfinance as yf
from newsapi import NewsApiClient
import google.generativeai as genai
from datetime import datetime, timedelta

# -----------------------------
# API KEYS
# -----------------------------

NEWS_API_KEY = "fc7c24a7e555442cb54c67dbf1f403da"
GEMINI_API_KEY = "AIzaSyAP2_ayCFgZfhWVkMlJOxn9BcEuv-0PqSI"

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")


# -----------------------------
# STREAMLIT UI
# -----------------------------

st.title("📊 AI Stock Analyzer")

symbol = st.text_input(
    "Enter Stock Symbol",
    placeholder="Example: AAPL or RELIANCE.NS"
)


# -----------------------------
# STOCK DATA
# -----------------------------

def get_stock_data(symbol):

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="1y")

    if hist.empty:
        return None, None, None

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

    technical = {
        "Current Price": round(hist["Close"].iloc[-1],2),
        "50DMA": round(hist["Close"].rolling(50).mean().iloc[-1],2),
        "200DMA": round(hist["Close"].rolling(200).mean().iloc[-1],2),
        "52W High": round(hist["High"].max(),2),
        "52W Low": round(hist["Low"].min(),2),
        "Volume": int(hist["Volume"].iloc[-1])
    }

    financials = ticker.financials
    balance = ticker.balance_sheet
    cashflow = ticker.cashflow

    statements = {
        "Income Statement": financials.head().to_string(),
        "Balance Sheet": balance.head().to_string(),
        "Cashflow": cashflow.head().to_string()
    }

    return technical, fundamentals, statements, hist


# -----------------------------
# NEWS
# -----------------------------

def get_stock_news(company):

    try:

        query = company.replace(".NS","")

        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        news = newsapi.get_everything(
            q=query,
            from_param=from_date,
            language="en",
            sort_by="relevancy",
            page_size=5
        )

        articles = news["articles"]

        news_text = ""

        for a in articles:
            news_text += f"{a['title']} - {a.get('description','')}\n"

        return articles, news_text

    except:
        return [], ""


# -----------------------------
# GEMINI ANALYSIS
# -----------------------------

def generate_analysis(symbol, tech, fundamentals, statements, news):

    prompt = f"""
You are a professional equity research analyst.

Company: {symbol}

Technical Data:
{tech}

Fundamental Metrics:
{fundamentals}

Financial Statements:
{statements}

Recent News:
{news}

Provide analysis covering:

1 Technical Outlook
2 Fundamental View
3 News Sentiment
4 Key Risks
5 Investment Recommendation
"""

    response = model.generate_content(prompt)

    return response.text


# -----------------------------
# MAIN BUTTON
# -----------------------------

if st.button("Analyze"):

    if symbol:

        st.write("Fetching stock data...")

        tech, fundamentals, statements, hist = get_stock_data(symbol)

        if tech is None:
            st.error("Invalid ticker symbol")
            st.stop()

        # -----------------
        # TECHNICAL DATA
        # -----------------

        st.subheader("Technical Data")

        st.json(tech)

        st.line_chart(hist["Close"])

        # -----------------
        # FUNDAMENTALS
        # -----------------

        st.subheader("Fundamental Metrics")

        st.json(fundamentals)

        # -----------------
        # FINANCIAL STATEMENTS
        # -----------------

        st.subheader("Financial Statements")

        st.text("Income Statement")
        st.text(statements["Income Statement"])

        st.text("Balance Sheet")
        st.text(statements["Balance Sheet"])

        st.text("Cashflow")
        st.text(statements["Cashflow"])

        # -----------------
        # NEWS
        # -----------------

        st.write("Fetching news...")

        articles, news_text = get_stock_news(symbol)

        st.subheader("Latest News")

        if articles:

            for a in articles:
                st.markdown(f"### {a['title']}")
                st.write(a.get("description",""))
                st.write(a["url"])

        else:
            st.write("No recent news found")

        # -----------------
        # GEMINI
        # -----------------

        st.write("Generating AI analysis...")

        analysis = generate_analysis(symbol, tech, fundamentals, statements, news_text)

        st.subheader("AI Analysis")

        st.write(analysis)