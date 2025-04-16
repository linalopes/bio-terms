# extractGoogleAlerts.js

This Google Apps Script automates the extraction of **Google Alerts emails** from your Gmail inbox and stores structured data into a **Google Spreadsheet**.

It searches for emails based on predefined search terms (e.g., `"bioart"`, `"biohacking"`) and extracts the **title**, **description**, **link**, **source**, and **date** from the email content.

---

## ✨ What It Does

- Searches Gmail for emails matching:
  `subject:"Google Alert - [term]"`
- Parses the HTML body of each alert email
- Extracts:
  - `term` (search term)
  - `real URL` (resolved link)
  - `date`
  - `source` (domain)
  - `title` and `description`
- Appends the data as new rows in a target Google Sheet
- Labels and archives the processed emails


## 📋 Example Search Terms Used

```javascript
const searchTerms = ['biodesign', 'bioart', 'biohacking', '3D bioprinting'];
```
---

## 📁 How to Set Up (Google Apps Script)
1. Go to https://script.google.com/
2. Click “New project”
3. Replace the default Code.gs with your extractGoogleAlerts.js script
4. Save the project and give it a name

## 📈 Google Sheet Setup
1. Create a new Google Sheet
2. Note its ID from the URL:
`https://docs.google.com/spreadsheets/d/🟢SPREADSHEET_ID🟢/edit`

3. Replace the spreadsheetId in the script:
```javascript
const spreadsheetId = '🟢your-sheet-id-here🟢';
```

4. Use or create a sheet/tab named Sheet0

## 🏷 Gmail Label Setup
The script labels processed alerts to avoid reprocessing.
```javascript
const labelName = "Google Alerts - terms";
```
You don’t need to create this label manually — the script will create it if it doesn't exist.


## ⚙️ Permissions
When running the script for the first time:
- You'll be prompted to authorize access to Gmail and Sheets
- Approve the necessary scopes


## 🔁 Optional: Run Automatically
You can set a trigger to run the script daily:

1. In the Script Editor, go to Triggers (⏰ clock icon)
2. Click “+ Add Trigger”
3. Select:
  - Function to run: extractAllGoogleAlertsData
  - Event source: Time-driven
  - Choose a frequency (e.g. daily)
