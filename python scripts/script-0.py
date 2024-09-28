import os
from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from google.oauth2 import service_account
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

# Read data from 'Sheet1' (assuming data starts from row 2)
sheet = service.spreadsheets()
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A2:Z'  # Adjust the range as needed to include all your data columns
).execute()
rows = result.get('values', [])

# Remove duplicates based on column B (index 1)
unique_links = set()
filtered_rows = []
for row in rows:
    link = row[1] if len(row) > 1 else ''  # Get the link from column B
    if link and link not in unique_links:
        unique_links.add(link)
        filtered_rows.append(row)
    else:
        # Log or count duplicates if needed
        logging.info(f"Duplicate link found and removed: {link}")

# Clear existing data in 'Sheet1' (excluding headers)
clear_body = {}
service.spreadsheets().values().clear(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A2:Z',  # Adjust the range as needed
    body=clear_body
).execute()

# Write the filtered data back to 'Sheet1'
update_body = {
    'values': filtered_rows
}
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A2',  # Start writing from A2
    valueInputOption='RAW',
    body=update_body
).execute()

print("Duplicates removed successfully. Data updated in 'Sheet1'.")
