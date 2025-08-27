# LinkedIn Automation Setup Guide v2.4

## 🚀 Get Started with Enhanced Filtering in 5 Minutes

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

### 5. Run the Enhanced System
```bash
# 🆕 Main scraper with modular filtering (GUI)
python "universal parser_wo_semantic_chatgpt.py"

# 🔍 Enhanced job tracker with transparency
streamlit run job_tracker.py

# 📊 Legacy analytics dashboard  
streamlit run streamlit_linkedin_scraper.py

# 🧪 Test filter logic (validate all combinations)
python test_filter_logic.py
```

## 🎯 NEW: Configuring Modular Filters (v2.4)

When you run the main scraper, you'll see new filter configuration options:

### Filter Configuration GUI
- ☑ **Accept Remote Jobs** (includes hybrid, wfh, distributed team)
- ☑ **Accept Visa Sponsorship Jobs** (includes h1b sponsor, relocation)
- **Logic**: OR/AND dropdown for location requirements  
- ☑ **Require Technical Skills** (Anaplan/SAP/Planning)
- ☑ **Block jobs that prohibit remote work**

### Common Filter Strategies
```
Remote-only mode:     ☑ Remote, ☐ Visa, ☑ Block onsite-only
Visa-focus mode:      ☐ Remote, ☑ Visa, ☐ Block onsite-only  
Flexible (default):   ☑ Remote, ☑ Visa, OR logic
Skills-optional:      ☑ Location options, ☐ Require skills
```

### Enhanced Vocabulary (55+ New Keywords)
The system now recognizes many more job terms:
- **Remote**: hybrid, wfh, remote-first, distributed team, virtual position
- **Visa**: h1b sponsor, green card sponsor, immigration assistance  
- **Skills**: hyperion, adaptive insights, sap ibp, mrp, erp planning

### Transparency Features
After running scraper, check the job tracker for:
- **Matched Keywords**: See exactly which terms triggered each match
- **Filter Results**: Understand why jobs passed/failed
- **Configuration**: Track which settings were used

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