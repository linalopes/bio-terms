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

---

## 1-url-language-country-analyzer.ipynb

**Purpose:**
This Jupyter Notebook analyzes rows from the cleaned Google Spreadsheet (`Sheet0`) that are tagged with the word `"bioart"` in the `wordAlert` column. For each row, it extracts content from the linked URL, detects the language, and attempts to infer the country from the webpage metadata. The results are written back into the same spreadsheet, in new columns.

**Workflow:**
1. Load `.env` variables and authenticate with the Google Sheets API.
2. Read all rows from `Sheet0` and filter for those where `wordAlert == "bioart"`.
3. For each link in the filtered set:
   - Fetch and parse the web page.
   - Extract main visible text.
   - Detect the language using `langdetect`.
   - Attempt to extract country from meta tags (e.g., `og:country-name`, `geo.country`, etc.).
4. Write the results to columns G, H, and I in the original `Sheet0`, preserving row alignment.
5. To avoid exceeding Google API quotas, results are written in batches of 200 rows.
6. A status summary is generated to show the percentage of successfully processed entries.

**Columns updated:**

| Column | Field              |
|--------|--------------------|
| G      | Detected Language  |
| H      | Detected Country   |
| I      | Extracted Text     |

**API Quota Handling:**
To comply with Google Sheets API limits (`Write requests per minute per user`), the update operation is performed in **chunked batches**, not line-by-line. This ensures robust and reliable performance for large datasets.

**Processing Summary Output:**
At the end of the notebook, a breakdown is provided to show what percentage of rows were successfully processed (`OK`) and how many failed (`ERROR`), due to blocked access or invalid content.

---

## 2-semantic-analysis-openai.ipynb

**Purpose:**
This Jupyter Notebook performs semantic analysis on previously extracted text data from Google Alerts. It focuses specifically on rows in `Sheet0` where `wordAlert == "bioart"`. For each relevant row, it uses the OpenAI API to generate:

- A clean and complete **language** label (fallback if missing)
- A corrected or inferred **country**
- A 1–2 sentence **summary** of the article
- A **semantic universe** representing topics, domains, or themes
- A list of **keywords** related to the content

**Workflow:**
1. Load `.env` variables and authenticate with both Google Sheets and OpenAI API.
2. Read all rows from `Sheet0`, filtering only entries where `wordAlert == "bioart"`.
3. For each filtered row:
   - Use existing `detected-language` and `detected-country` values if available.
   - If language is coded (e.g., `"de"`), it is translated to full name (e.g., `"German"`).
   - If country is `"unknown"` or missing, OpenAI is prompted to infer it.
   - OpenAI is always used to generate: summary, semantic universe, and keywords.
4. To stay within OpenAI token limits, long texts are truncated before analysis.
5. All results are written back to the original `Sheet0` in columns J through N.

**Columns updated:**

| Column | Field             |
|--------|-------------------|
| J      | Language (final)  |
| K      | Country (final)   |
| L      | Summary           |
| M      | Semantics         |
| N      | Keywords          |

**OpenAI Integration Notes:**
- Uses the new `openai>=1.0.0` interface.
- All API responses are requested in structured **JSON** format to improve reliability and parsing.
- Token length of input text is controlled to avoid exceeding model context limits.
- You can switch models by changing `model="gpt-3.5-turbo"` to another supported OpenAI model.

**Environment Variables Required:**

In addition to the variables used in previous notebooks, you must also include:

```env
OPENAI_API_KEY=your_openai_api_key
```

**Important:**

- You are responsible for OpenAI API usage costs. Monitor your usage if you run batch operations.
- Responses are cached in the sheet to avoid unnecessary re-analysis.
