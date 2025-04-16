# Python Scripts for Google Sheets Automation

This repository contains Python and Jupyter Notebook scripts used to automate the cleaning and processing of data collected from Google Alerts stored in Google Sheets.

---

## 0-clean-duplicates.ipynb

**Purpose:**
This Jupyter Notebook connects to a Google Spreadsheet, reads the data from a specific sheet (Sheet0), and removes duplicate entries based on a specific column — in this case, the column containing the link (column B). After identifying duplicates, it rewrites the sheet with only unique rows (excluding the header).

**Workflow:**
1. Load `.env` variables including the service account JSON path and spreadsheet ID.
2. Authenticate with the Google Sheets API.
3. Read all rows from `Sheet0` (excluding the header).
4. Identify and remove duplicates using the link column.
5. Clear the existing data (except the header) and write the cleaned version back to the sheet.

**Environment Variables Required:**
Create a `.env` file in the root of your project folder with the following content:

```env
SERVICE_ACCOUNT_FILE=./your-service-account-key.json
SPREADSHEET_ID=your_google_spreadsheet_id
````

**Important:**

- Do not commit your .env or .json credential files. Make sure they are listed in your .gitignore.
- Share your Google Sheet with the service account email to grant access.
