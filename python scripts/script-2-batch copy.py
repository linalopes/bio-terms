import os
from dotenv import load_dotenv
load_dotenv()

from googleapiclient.discovery import build
from google.oauth2 import service_account
import openai
import time
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

# Parameters
BATCH_SIZE = 20  # Adjust batch size based on OpenAI API rate limits
START_ROW = 2    # Starting row (excluding headers)

# Predefined categories (your tags)
categories = [
    'Bioart',
    'Biodesign',
    'Bioarchitecture',
    'Biomimecry',
    'Synthetic Biology',
    'Bio 3D Printing',
    'Parametric Design',
    'Open Science Hardware',
    'Biomanufacturing',
    'Biohacking',
    'Biomaterial'
]

# Read total number of rows
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheets = sheet_metadata.get('sheets', '')
for s in sheets:
    if s.get("properties", {}).get("title", "") == "Sheet1":
        total_rows = s.get("properties", {}).get("gridProperties", {}).get("rowCount", 0)
        break

# Process data in batches
for batch_start in range(START_ROW, total_rows + 1, BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE - 1, total_rows)
    range_name = f'Sheet1!H{batch_start}:J{batch_end}'  # Read columns H (language), I (country), J (text)

    # Read data for the current batch
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    rows = result.get('values', [])

    # List to hold updated data for this batch
    updated_rows = []

    for index, row in enumerate(rows):
        language = row[0] if len(row) > 0 else ''
        country = row[1] if len(row) > 1 else ''
        text = row[2] if len(row) > 2 else ''

        # Skip rows where text is empty or 'Error'
        if not text or text.lower() == 'error':
            logging.info(f"Skipping row {batch_start + index} due to empty or error in text.")
            updated_rows.append([language, country, 'No Summary', 'No Tags', 'No Justification', 'No Suggested Tags'])
            continue

        logging.info(f"Processing row {batch_start + index}")

        try:
            # Generate a summary
            prompt_summary = f"Provide a concise summary, always in English, of the following text:\n\n{text}\n\nSummary:"
            response_summary = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "user", "content": prompt_summary}
                ],
                max_tokens=150,
                temperature=0.5,
            )
            summary = response_summary['choices'][0]['message']['content'].strip()

            # Assign predefined tags with justifications
            categories_str = ', '.join(categories)
            prompt_predefined_tags = f"From the following text, assign one or more of these categories: {categories_str}. For each assigned category, provide a brief justification. Respond in the format:\nCategory: [category1]\nJustification: [reason]\n...\nText:\n\n{text}\n\nCategories and Justifications:"
            response_predefined_tags = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "user", "content": prompt_predefined_tags}
                ],
                max_tokens=300,
                temperature=0.5,
            )
            predefined_tags_justification = response_predefined_tags['choices'][0]['message']['content'].strip()

            # Parse the response for predefined tags and justifications
            predefined_tags = []
            predefined_justifications = []
            lines = predefined_tags_justification.split('\n')
            current_category = ''
            current_justification = ''
            for line in lines:
                if line.startswith('Category:'):
                    current_category = line.replace('Category:', '').strip()
                    predefined_tags.append(current_category)
                elif line.startswith('Justification:'):
                    current_justification = line.replace('Justification:', '').strip()
                    predefined_justifications.append(f"{current_category}: {current_justification}")

            predefined_tags_str = ', '.join(predefined_tags)
            predefined_justifications_str = '; '.join(predefined_justifications)

            # Get OpenAI's own suggested tags (without justifications)
            prompt_suggested_tags = f"Based on the following text, suggest relevant tags or keywords in English that describe the main topics. Respond with a list of tags in English separated by commas.\n\nText:\n\n{text}\n\nTags:"
            response_suggested_tags = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "user", "content": prompt_suggested_tags}
                ],
                max_tokens=50,
                temperature=0.5,
            )
            suggested_tags = response_suggested_tags['choices'][0]['message']['content'].strip()

            # Append the data to the list
            updated_rows.append([language, country, summary, predefined_tags_str, predefined_justifications_str, suggested_tags])

        except Exception as e:
            logging.error(f"Error processing row {batch_start + index}: {e}")
            updated_rows.append([language, country, 'Error', 'Error', 'Error', 'Error'])

        # Add delay between OpenAI API calls to avoid rate limits
        time.sleep(1)  # Sleep for 1 second

    # Write data back for the current batch
    update_range = f'Sheet1!K{batch_start}:P{batch_end}'
    body = {
        'values': updated_rows
    }
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption='RAW',
        body=body
    ).execute()

    # Optional: Delay between batches to avoid rate limits
    time.sleep(10)  # Sleep for 10 seconds

    print(f"Batch {batch_start}-{batch_end} processed successfully.")
