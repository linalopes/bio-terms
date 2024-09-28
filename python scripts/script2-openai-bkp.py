import os
from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from google.oauth2 import service_account
import openai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
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

# Read data from the 'test' sheet (columns H to J)
sheet = service.spreadsheets()
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='test!H2:J'
).execute()
rows = result.get('values', [])

# Categories and keywords
categories = {
    'Bioart': ['bioart', 'art', 'installation'],
    'Biodesign': ['biodesign', 'design', 'product'],
    'Bioarchitecture': ['bioarchitecture', 'architecture', 'building'],
    'Biomimicry': ['biomimetics', 'biomimicry', 'nature'],
    'Synthetic Biology': ['synthetic biology', 'genetic engineering'],
    '3D Printing': ['3d printing', 'additive manufacturing', 'biofabrication'],
    'Parametric Design': ['parametric', 'algorithmic design', 'generative design'],
    'Hardware': ['hardware', 'open hardware', 'electronics'],
    'Biomanufacturing': ['biomanufacturing', 'biofabrication'],
    'Biohacking': ['mindset', 'philosophy', 'hacking']
}

# List to hold updated data
updated_rows = []

for index, row in enumerate(rows):
    language = row[0] if len(row) > 0 else ''
    country = row[1] if len(row) > 1 else ''
    text = row[2] if len(row) > 2 else ''
    
    # Skip processing if language or country is 'Error'
    if language.lower() == 'error' or country.lower() == 'error':
        logging.info(f"Skipping row {index + 2} due to error in language or country detection.")
        updated_rows.append(['Skipped', 'Skipped', 'Skipped', 'Skipped'])
        continue

    if not text:
        updated_rows.append(['No Text', 'No Summary', 'No Tags', 'No Justification'])
        continue

    logging.info(f"Processing row {index + 2}")

    try:
        # Correct 'unknown' language using OpenAI if necessary
        if language.lower() == 'unknown' or not language.strip():
            prompt_lang = f"Detect the language of the following text:\n\n{text}\n\nLanguage:"
            response_lang = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "user", "content": prompt_lang}
                ],
                max_tokens=10,
                temperature=0,
            )
            language = response_lang['choices'][0]['message']['content'].strip()
        
        # Correct 'unknown' country using OpenAI if necessary
        if country.lower() == 'unknown' or not country.strip():
            prompt_country = f"Based on the following text, identify the country or city of origin of the news or the main country it refers to. If it cannot be determined, respond 'Unknown'. Text:\n\n{text}\n\nCountry:"
            response_country = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "user", "content": prompt_country}
                ],
                max_tokens=20,
                temperature=0,
            )
            country = response_country['choices'][0]['message']['content'].strip()

        # Generate a summary and determine industry context
        prompt_summary = f"Provide a concise summary in English of the following text, including the industry context, the main topic, and the objective of the text:\n\n{text}\n\nSummary:"
        response_summary = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "user", "content": prompt_summary}
            ],
            max_tokens=150,
            temperature=0.5,
        )
        summary = response_summary['choices'][0]['message']['content'].strip()

        # Assign tags based on categories
        prompt_tags = f"Based on the following text, assign one or more of these categories: {', '.join(categories.keys())}. Respond only with the category names separated by commas. Text:\n\n{text}\n\nCategories:"
        response_tags = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "user", "content": prompt_tags}
            ],
            max_tokens=50,
            temperature=0,
        )
        tags = response_tags['choices'][0]['message']['content'].strip()

        # Append the data to the list
        updated_rows.append([language, country, summary, tags])

    except Exception as e:
        logging.error(f"Error processing row {index + 2}: {e}")
        updated_rows.append(['Error', 'Error', 'Error', 'Error'])

# Define the range where you want to write the data (starting from column K)
update_range = f'test!K2:N{len(updated_rows) + 1}'

# Prepare the data to write
body = {
    'values': updated_rows
}

# Write data to the spreadsheet
try:
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    print("Data successfully written to the spreadsheet.")
except Exception as e:
    logging.error(f"Error writing data to spreadsheet: {e}")
