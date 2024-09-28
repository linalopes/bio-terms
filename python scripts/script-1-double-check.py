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
START_ROW = 2    # Starting row (excluding headers)

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
    range_name = f'Sheet1!B{batch_start}:J{batch_end}'  # Read columns B to J
    
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
    rows_to_update = []
    for index, row in enumerate(rows):
        actual_row = batch_start + index  # The actual row number in the sheet
        url = row[0] if len(row) > 0 else ''        # Column B: URL
        language = row[6] if len(row) > 6 else ''   # Column H: Language
        country = row[7] if len(row) > 7 else ''    # Column I: Country
        text = row[8] if len(row) > 8 else ''       # Column J: Extracted Text

        # Check if text is 'Error', 'unknown', or empty
        if text.lower() in ['error', 'unknown', ''] or not text.strip():
            logging.info(f"Reprocessing row {actual_row} due to missing or invalid text.")
            if not url:
                logging.warning(f"No URL found in row {actual_row}. Skipping.")
                continue

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
                max_text_length = 10000  # Adjust as needed
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

                # Prepare the updated data for this row
                updated_row = [language, country, text_to_store]

            except requests.exceptions.RequestException as e:
                logging.error(f"HTTP error for URL {url}: {e}")
                updated_row = ['Error', 'Error', 'Error']
            except Exception as e:
                logging.error(f"Error processing row {actual_row}: {e}")
                updated_row = ['Error', 'Error', 'Error']

            # Keep track of which rows need to be updated and their new data
            updated_rows.append(updated_row)
            rows_to_update.append(actual_row)
        else:
            # No action needed for this row
            continue

        # Optional: Delay between requests to avoid overloading servers
        # time.sleep(0.1)  # Adjust the delay as needed

    # Write updated data back to the spreadsheet for the affected rows
    if updated_rows:
        data = []
        for row_num, updated_row in zip(rows_to_update, updated_rows):
            data.append({
                'range': f'Sheet1!H{row_num}:J{row_num}',
                'values': [updated_row]
            })

        body = {
            'valueInputOption': 'RAW',
            'data': data
        }

        try:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            logging.info(f"Rows {rows_to_update} updated successfully.")
        except Exception as e:
            logging.error(f"Error writing data to spreadsheet for rows {rows_to_update}: {e}")

    # Optional: Delay between batches to respect rate limits
    time.sleep(5)  # Adjust the delay as needed

print("Double-check process completed.")
