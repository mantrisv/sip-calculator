import streamlit as st
import streamlit.components.v1 as components
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------

SHEET_ID = "1X67okMAGzu15olxtR8UhRDQam2HmqjWgDsj2fLhhvLc"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# -----------------------------
# GOOGLE AUTH
# -----------------------------

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
        "published_date": volume.get("publishedDate", ""),
        "thumbnail": volume.get("imageLinks", {}).get("thumbnail", "")
    }


def isbn_exists(isbn):
    records = sheet.get_all_records()
    for row in records:
        if str(row["ISBN"]) == str(isbn):
            return True
    return False


# -----------------------------
# UI
# -----------------------------

st.set_page_config(page_title="My ISBN Library")
st.title("📚 My ISBN Library")
st.markdown("### 📷 Scan Book Barcode")

# Initialize session state
if "isbn_input" not in st.session_state:
    st.session_state.isbn_input = ""

# Scanner
html_code = """
<div id="reader" style="width:300px;"></div>

<script src="https://unpkg.com/html5-qrcode"></script>

<script>
function onScanSuccess(decodedText) {
    const input = window.parent.document.querySelector('input[type="text"]');
    if (input) {
        input.value = decodedText;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }
}

var scanner = new Html5QrcodeScanner(
    "reader",
    { fps: 10, qrbox: 250 }
);

scanner.render(onScanSuccess);
</script>
"""

components.html(html_code, height=400)

# Text Input (bound to session_state)
isbn_input = st.text_input(
    "Scanned ISBN will appear here",
    key="isbn_input"
)

# -----------------------------
# ADD BOOK LOGIC
# -----------------------------

if st.button("➕ Add Book"):

    if not st.session_state.isbn_input:
        st.warning("Scan or enter ISBN first.")
    else:
        isbn = st.session_state.isbn_input.strip()

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

                # Clear input after success
                st.session_state.isbn_input = ""

            else:
                st.error("Book not found in Google Books.")


# -----------------------------
# LIBRARY VIEW
# -----------------------------

st.markdown("## 📖 Library")

records = sheet.get_all_records()

if records:
    st.dataframe(records, use_container_width=True)
else:
    st.info("No books added yet.")
