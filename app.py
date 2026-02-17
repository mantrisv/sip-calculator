import streamlit as st
import cv2
import av
import requests
import gspread
from pyzbar.pyzbar import decode
from google.oauth2.service_account import Credentials
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------

SHEET_ID = "1X67okMAGzu15olxtR8UhRDQam2HmqjWgDsj2fLhhvLc"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1


# -----------------------------
# FUNCTIONS
# -----------------------------

def fetch_book(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    data = response.json()

    if "items" not in data:
        return None

    volume = data["items"][0]["volumeInfo"]

    return {
        "title": volume.get("title", ""),
        "authors": ", ".join(volume.get("authors", [])),
        "publisher": volume.get("publisher", ""),
        "published_date": volume.get("publishedDate", "")
    }


def isbn_exists(isbn):
    records = sheet.get_all_records()
    for row in records:
        if str(row["ISBN"]) == str(isbn):
            return True
    return False


# -----------------------------
# SESSION STATE
# -----------------------------

if "isbn" not in st.session_state:
    st.session_state.isbn = ""


# -----------------------------
# BARCODE SCANNER CLASS
# -----------------------------

class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = decode(img)

        for barcode in barcodes:
            isbn = barcode.data.decode("utf-8")
            st.session_state.isbn = isbn

            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return img


# -----------------------------
# UI
# -----------------------------

st.title("📚 My ISBN Library")
st.markdown("### 📷 Scan Book Barcode")

webrtc_streamer(
    key="scanner",
    video_transformer_factory=BarcodeScanner,
)

isbn_input = st.text_input("Scanned ISBN", value=st.session_state.isbn)

# -----------------------------
# ADD BOOK
# -----------------------------

if st.button("➕ Add Book"):

    if not isbn_input:
        st.warning("Scan or enter ISBN first.")
    else:
        isbn = isbn_input.strip()

        if isbn_exists(isbn):
            st.warning("⚠ Book already exists.")
        else:
            book = fetch_book(isbn)

            if book:
                sheet.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    isbn,
                    book["title"],
                    book["authors"],
                    book["publisher"],
                    book["published_date"],
                    "Not Started",
                    "",
                    ""
                ])

                st.success("✅ Book added successfully!")
                st.session_state.isbn = ""

            else:
                st.error("Book not found.")


# -----------------------------
# LIBRARY
# -----------------------------

st.markdown("## 📖 Library")

records = sheet.get_all_records()

if records:
    st.dataframe(records, use_container_width=True)
else:
    st.info("No books added yet.")
