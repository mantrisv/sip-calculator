import streamlit as st
import requests
import gspread
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image

# -------------------------------
# CONFIG
# -------------------------------

SHEET_URL = "https://docs.google.com/spreadsheets/d/1X67okMAGzu15olxtR8UhRDQam2HmqjWgDsj2fLhhvLc/edit?gid=0#gid=0"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1


# -------------------------------
# FETCH BOOK
# -------------------------------

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
        "published_date": volume.get("publishedDate", ""),
        "thumbnail": volume.get("imageLinks", {}).get("thumbnail", "")
    }


# -------------------------------
# CHECK DUPLICATE
# -------------------------------

def isbn_exists(isbn):
    records = sheet.get_all_records()
    for row in records:
        if str(row["ISBN"]) == str(isbn):
            return True
    return False


# -------------------------------
# UI
# -------------------------------

st.title("📚 Mobile ISBN Scanner Library")

image = st.camera_input("Scan Book Barcode")

if image is not None:
    img = Image.open(image)
    img_np = np.array(img)

    barcodes = decode(img_np)

    if barcodes:
        isbn = barcodes[0].data.decode("utf-8")
        st.success(f"Detected ISBN: {isbn}")

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

                st.success("✅ Book added!")

                if book["thumbnail"]:
                    st.image(book["thumbnail"], width=150)

                st.write("**Title:**", book["title"])
                st.write("**Authors:**", book["authors"])
                st.write("**Publisher:**", book["publisher"])
                st.write("**Published:**", book["published_date"])
            else:
                st.error("Book not found in Google Books.")
    else:
        st.error("No barcode detected. Try again.")


# -------------------------------
# SHOW LIBRARY
# -------------------------------

st.subheader("📖 My Library")
records = sheet.get_all_records()

if records:
    st.dataframe(records)
else:
    st.info("Library empty.")
