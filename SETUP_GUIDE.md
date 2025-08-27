# Quick Setup Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install pandas requests matplotlib openpyxl selenium langdetect undetected-chromedriver streamlit wordcloud gspread python-dotenv
```

### 2. Configure Credentials
```bash
# Copy the template
cp .env.example .env

# Edit .env with your values
# Minimum required:
LINKEDIN_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
LINKEDIN_CREDS_PATH=./google_sheets_credentials.json
```

### 3. Set Up Google Sheets
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable "Google Sheets API"
4. Create Service Account → Download JSON credentials
5. Rename to `google_sheets_credentials.json`
6. Share your Google Sheet with service account email

### 4. Test Configuration
```bash
python -c "from config import Config; Config.validate(); print('✅ Ready to go!')"
```

### 5. Run the System
```bash
# Main scraper (GUI)
python "universal parser_wo_semantic_chatgpt.py"

# Job tracking dashboard
streamlit run job_tracker.py

# Analytics dashboard  
streamlit run streamlit_linkedin_scraper.py
```

## 🔧 Optional Setup

### Telegram Notifications
```bash
# Add to .env file:
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Chrome Configuration
```bash
# Add to .env file:
CHROMEDRIVER_PATH=C:/selenium/chromedriver.exe
CHROME_BINARY_PATH=C:/Program Files/Google/Chrome/Application/chrome.exe
CHROME_PROFILE_PATH=C:/selenium/profile
```

## 🆘 Troubleshooting

### "Configuration missing" Error
- Check `.env` file exists and has correct variables
- Verify Google Sheets URL is accessible
- Ensure credentials file path is correct

### "Google Sheets connection failed"
- Verify service account email has access to sheet
- Check credentials file is valid JSON
- Ensure Google Sheets API is enabled

### "No data found"
- Check Google Sheet has data
- Verify sheet URL is correct
- Run both dashboards to compare results

## 📞 Support

- Check `logs/` directory for error details
- See `REFACTORING_PLAN.md` for known issues
- Validate config: `python -c "from config import Config; print(Config.get_all())"`