import os
from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests
from bs4 import BeautifulSoup
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Path to your service account key file
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
# ID of your spreadsheet
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Read data from the 'test' sheet
sheet = service.spreadsheets()
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='test!B2:B'
).execute()
rows = result.get('values', [])

# Function to identify country from webpage metadata
def get_country_from_metadata(soup):
    # Attempt to find country in meta tags
    country = 'Unknown'  # Default value
    # List of possible meta tag attributes that might contain country information
    meta_tags = [
        {'name': 'geo.country'},
        {'property': 'og:country-name'},
        {'name': 'country'},
        {'name': 'dcterms.coverage'},
        {'name': 'ICBM'},
        {'name': 'geo.position'},
        {'name': 'geo.placename'},
    ]
    for tag_attrs in meta_tags:
        meta = soup.find('meta', attrs=tag_attrs)
        if meta and 'content' in meta.attrs:
            country = meta['content'].strip()
            break
    return country

# List to hold updated data
updated_rows = []

for index, row in enumerate(rows):
    url = row[0] if len(row) > 0 else ''
    
    if not url:
        updated_rows.append(['No URL', 'No Language', 'No Country', 'No Text'])
        continue

    logging.info(f"Processing row {index + 2}")

    # Ensure the URL has a scheme
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url

    try:
         # Define headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/98.0.4758.102 Safari/537.36'
    }
        # Fetch the webpage content with headers
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        # Limit text length if needed (e.g., to avoid excessively large cells)
        max_text_length = 25000  # Adjust as needed
        text_to_store = text[:max_text_length]

        # Detect language using langdetect
        if text_to_store.strip():
            try:
                language = detect(text_to_store)
            except LangDetectException:
                language = 'unknown'
        else:
            language = 'unknown'

        # Identify country from metadata
        country = get_country_from_metadata(soup)

        # Append the data to the list
        updated_rows.append([language, country, text_to_store])

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error for URL {url}: {e}")
        updated_rows.append(['Error', 'Error', 'Error'])
    except Exception as e:
        logging.error(f"Error processing row {index + 2}: {e}")
        updated_rows.append(['Error', 'Error', 'Error'])

# Define the range where you want to write the data (starting from column H)
update_range = f'test!H2:J{len(updated_rows) + 1}'

# Prepare the data to write
body = {
    'values': updated_rows
}

# Write data to the spreadsheet
result = sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=update_range,
    valueInputOption='RAW',
    body=body
).execute()

print("Data successfully written to the spreadsheet.")
