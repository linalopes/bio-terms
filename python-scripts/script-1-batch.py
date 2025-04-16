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
import time

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

# Parameters
BATCH_SIZE = 50  # Adjust based on your rate limits and needs
START_ROW = 880    # Starting row (excluding headers)

# Read total number of rows in 'Sheet1'
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheets = sheet_metadata.get('sheets', '')
for s in sheets:
    if s.get("properties", {}).get("title", "") == "Sheet1":
        total_rows = s.get("properties", {}).get("gridProperties", {}).get("rowCount", 0)
        break
else:
    logging.error("Sheet 'Sheet1' not found.")
    total_rows = START_ROW - 1  # Set total_rows to avoid processing if sheet not found

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

# Process data in batches
for batch_start in range(START_ROW, total_rows + 1, BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE - 1, total_rows)
    range_name = f'Sheet1!B{batch_start}:B{batch_end}'  # Reading only column B (URLs)
    
    # Read data for the current batch
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    rows = result.get('values', [])

    if not rows:
        logging.info(f"No data found in rows {batch_start} to {batch_end}.")
        continue

    updated_rows = []

    for index, row in enumerate(rows):
        actual_row = batch_start + index  # The actual row number in the sheet
        url = row[0] if len(row) > 0 else ''
        
        if not url:
            updated_rows.append(['No URL', 'No Language', 'No Country', 'No Text'])
            continue

        logging.info(f"Processing row {actual_row}")

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

            # Limit text length if needed
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
            logging.error(f"Error processing row {actual_row}: {e}")
            updated_rows.append(['Error', 'Error', 'Error'])

        # Optional: Delay between requests to avoid overloading servers
        # time.sleep(0.1)  # Adjust the delay as needed

    # Write data back for the current batch
    update_range = f'Sheet1!H{batch_start}:J{batch_start + len(updated_rows) - 1}'

    # Prepare the data to write
    body = {
        'values': updated_rows
    }

    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=update_range,
            valueInputOption='RAW',
            body=body
        ).execute()
        logging.info(f"Batch {batch_start}-{batch_end} processed successfully.")
    except Exception as e:
        logging.error(f"Error writing data to spreadsheet for batch {batch_start}-{batch_end}: {e}")

    # Optional: Delay between batches to respect rate limits
    time.sleep(5)  # Adjust the delay as needed

print("All batches processed.")
