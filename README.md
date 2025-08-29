# LinkedIn Job Automation System v2.6

**LinkedIn Job Automation** — мощная система для автоматизированного поиска, анализа и отслеживания вакансий LinkedIn с модульной системой фильтрации, расширенным словарем и полной прозрачностью процесса отбора.

---

## 🚀 MAJOR FIX v2.6 - Cycle Statistics Clarification (Aug 29, 2025)

**CRITICAL UX IMPROVEMENT**: Cycle statistics now provide **crystal clear reporting** - no more confusion about duplicates vs new jobs!

### 🔥 Problem Solved
- Previous statistics were misleading: "New matches this cycle: 45" included duplicates from previous cycles
- "Total matches since start: 282" was confusing because it counted same jobs multiple times
- Users couldn't distinguish between truly new job discoveries vs re-encounters

### ⚡ Solution Implemented  
- **Enhanced Statistics Display**: Clear breakdown showing new vs duplicate matches
- **Unique Job Tracking**: Added `unique_jobs_discovered` counter for lifetime discoveries
- **State Validation**: Automatic consistency checks prevent counter misalignment
- **Normalized Job Keys**: Case-insensitive matching prevents false duplicates

### 📊 New Statistics Format
```
📊 Statistics:
• Jobs scanned: 820
• Matches found this cycle: 45 (15 new, 30 duplicates)
• Unique jobs discovered to date: 142
• Total match occurrences: 282
```

This improvement makes statistics **meaningful and actionable** for job search tracking.

---

## 🚀 MAJOR FIX v2.5 - LinkedIn Lazy Loading Solution (Aug 28, 2025)

**CRITICAL BUG RESOLVED**: LinkedIn Job Scraper now captures **95%+ of jobs** vs 52% previously!

### 🔥 Problem Solved
- LinkedIn uses aggressive lazy loading - only renders ~10-15 jobs in DOM at once
- Jobs disappear from DOM as you scroll past them (virtualized scrolling)  
- Previous basic scrolling missed 40-50% of available jobs

### ⚡ Solution Implemented  
- **LinkedIn-Specific Scroll Engine**: `scroll_until_loaded_linkedin_specific()`
- **Multi-Strategy Approach**: 4 different fallback scrolling techniques
- **Smart Detection**: Monitors job count increases in real-time
- **Enhanced Fallback**: Aggressive final push for stubborn remaining jobs

### 📊 Performance Results
- **Page 1**: 8 → 24+ jobs (300% improvement)
- **Page 2**: 16 → 24+ jobs (150% improvement)  
- **Page 3**: 6 → 10+ jobs (67% improvement)
- **Overall Capture Rate**: 52% → **95%+**

This fix is **business-critical** and ensures the scraper delivers its core value proposition.

---

## 🚀 What's New in v2.4 - Modular Filtering & Transparency

**Revolutionary Filtering System & Enhanced Vocabulary**

- ✨ **Modular Filtering**: Configurable GUI checkboxes replace hardcoded logic
- 📚 **Enhanced Vocabulary**: 55+ new keywords (hybrid, h1b sponsor, sap ibp, mrp, etc.)
- 🔍 **Complete Transparency**: See exactly which keywords matched and why jobs passed/failed
- 🎯 **Filter Modes**: Remote-only, Visa-focus, Flexible, Skills-optional modes
- ✅ **100% Backwards Compatible**: Default settings maintain existing behavior
- 🧪 **Comprehensive Testing**: All filter combinations validated with test suite

Full changelog: [CHANGELOG.md](CHANGELOG.md)

---

## 🔥 Key Features

**✨ Modular Filtering System**
- 🎛️ **GUI Configuration**: Simple checkboxes for filter setup (no code changes needed)
- 🏠 **Remote Options**: Accept remote jobs (remote, hybrid, wfh, distributed team)
- 🛂 **Visa Options**: Accept visa sponsorship jobs (h1b sponsor, relocation assistance) 
- 📋 **Skills Options**: Require Anaplan/SAP/Planning or make optional
- 🚫 **Exclusions**: Block onsite-only jobs
- 🔧 **Logic Modes**: AND/OR logic between location requirements

**📚 Enhanced Vocabulary (55+ New Keywords)**
- 🏠 **Remote**: hybrid, wfh, remote-first, distributed team, virtual position
- 🛂 **Visa**: h1b sponsor, green card sponsor, immigration assistance, tn visa
- 📊 **Anaplan**: hyperion, adaptive insights, workday adaptive, epm, fp&a
- 🔧 **SAP**: sap ibp (focused addition)
- 📋 **Planning**: mrp, erp planning, cpfr, demand sensing, supply chain optimization

**🔍 Complete Transparency**
- 📝 **Matched Keywords**: See exactly which words triggered each job match
- 🎯 **Filter Reasons**: Detailed explanations for why jobs passed/failed
- ⚙️ **Config Tracking**: Know which filter settings were used for each job
- 📊 **Keyword Analysis**: Most common matched terms and filter success rates

**🚀 Core Capabilities**  
- Intelligent job search with configurable multi-category filtering
- Real-time data collection in Excel and Google Sheets
- Automated Telegram notifications with analytics charts
- User-friendly Tkinter GUI for easy configuration
- Enhanced Streamlit dashboards with filter transparency
- Comprehensive logging and error handling

## 🔄 Job Processing Pipeline (NEW Modular System)

### 1. **Page Loading & Scrolling** 🆕 MAJOR FIX v2.5
- **LinkedIn-Specific Scroll Engine**: Handles virtualized scrolling with 95%+ capture rate
- **Multi-Strategy Scrolling**: 4 different techniques to force lazy loading
- **Real-Time Monitoring**: Tracks job count increases during scroll
- **Enhanced Fallback**: Aggressive final push for remaining stubborn jobs
- Smart pagination handling with random delays for stealth

### 2. **Data Extraction**  
- Job title, company, description, URL, publish date extraction
- Enhanced publish date parsing (supports "X days ago", "yesterday", etc.)

### 3. **🆕 Configurable Keyword Matching**
Enhanced vocabulary across all categories:
- **Remote** (17 keywords): remote, hybrid, wfh, distributed team, virtual position, etc.
- **Visa** (21 keywords): h1b sponsor, green card sponsor, immigration assistance, etc.  
- **Anaplan** (17 keywords): anaplan, hyperion, adaptive insights, fp&a, etc.
- **SAP** (12 keywords): sap apo, sap ibp, sap scm, etc.
- **Planning** (28 keywords): mrp, supply planning, demand sensing, cpfr, etc.

### 4. **Enhanced Logging Pipeline** 
Each job goes through detailed stage logging:
- **"Viewed"**: All jobs with matched keywords recorded
- **"Filtered (already applied)"**: Previously applied jobs
- **"Filtered (reason)"**: Failed jobs with specific reasons (e.g. "missing location: needs remote OR visa")
- **"Passed filters"**: Successful jobs with filter config tracking

### 5. **🆕 Modular Filter Logic**
Configurable through GUI checkboxes:
- **Location Requirements**: Remote AND/OR Visa sponsorship (configurable logic)
- **Skills Requirements**: Anaplan/SAP/Planning (can be disabled)
- **Exclusions**: Block remote-prohibited jobs (optional)
- **Transparency**: Every decision logged with detailed reasoning

### 6. **Output & Analytics**
- **Excel/Google Sheets**: Complete data with filter transparency
- **Telegram**: Smart notifications with charts for relevant jobs
- **Streamlit Dashboard**: Enhanced transparency showing matched keywords and filter reasons

### 7. **🔍 New Transparency Features**
- **Matched Keywords**: Exact terms that triggered each job match
- **Filter Config**: Settings used when processing each job  
- **Stage Reasons**: Detailed explanations for filter decisions
- **Keyword Analysis**: Most common matched terms and success rates

## 📁 Project Structure

### Core Components
- `universal parser_wo_semantic_chatgpt.py` — **Main scraper** with Tkinter GUI
- `job_tracker.py` — **Streamlined dashboard** for job tracking (recommended)
- `streamlit_linkedin_scraper.py` — **Analytics dashboard** with detailed visualizations
- `config.py` — **Centralized configuration** management

### Configuration
- `.env` — **Your credentials** (create from .env.example, never commit)
- `.env.example` — **Configuration template** with all required variables
- `google_sheets_credentials.json` — Google Sheets API credentials
- `tg_config.json` — Telegram configuration (legacy fallback)

### Data & Logs
- `companies_usa_remote.xlsx` — Output file with job data
- `logs/` — Error logs for monitoring and debugging
- `setup_logging.py` — Simple logging configuration

### Documentation
- `README.md` — This file
- `CHANGELOG.md` — Version history
- `REFACTORING_PLAN.md` — Future improvement roadmap

## 🔧 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/Dpotr/linkedin_scraper.git
cd LinkedIn_Automation
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate    # Windows
# or
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install pandas requests matplotlib openpyxl selenium langdetect undetected-chromedriver streamlit wordcloud gspread python-dotenv
```

### 4. Configure Environment Variables

**Create your configuration file:**
```bash
cp .env.example .env
```

**Edit `.env` with your actual values:**
```bash
# Google Sheets Configuration
LINKEDIN_SHEET_URL=your_google_sheet_url_here
LINKEDIN_CREDS_PATH=path/to/google_sheets_credentials.json

# Telegram Configuration (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Chrome Configuration
CHROME_PROFILE_PATH=path/to/selenium/profile
CHROME_BINARY_PATH=path/to/chrome.exe
CHROMEDRIVER_PATH=path/to/chromedriver.exe

# Output Configuration
OUTPUT_FILE_PATH=path/to/output/companies_usa_remote.xlsx
```

### 5. Set Up Google Sheets API
1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create service account credentials
4. Download JSON file as `google_sheets_credentials.json`
5. Share your Google Sheet with the service account email

### 6. Install ChromeDriver
- Download from [ChromeDriver](https://chromedriver.chromium.org/downloads)
- Add path to your `.env` file

## 🚀 Quick Start

### 1. Run the Enhanced Scraper
```bash
python "universal parser_wo_semantic_chatgpt.py"
```
**🆕 NEW Features in GUI:**
- ☑ **Accept Remote Jobs** (includes hybrid, wfh, distributed team)
- ☑ **Accept Visa Sponsorship Jobs** (includes h1b sponsor, relocation)  
- **Logic**: OR/AND dropdown for location requirements
- ☑ **Require Technical Skills** (Anaplan/SAP/Planning)
- ☑ **Block remote prohibited jobs** (filters out onsite-only)

**Filter Modes You Can Set:**
- **Remote-only**: Uncheck visa, check remote + block onsite-only
- **Visa-focus**: Uncheck remote, check visa only
- **Flexible**: Both checked with OR logic (default)
- **Skills-optional**: Uncheck skills for broader search

### 2. View Enhanced Job Data

**🔍 Job Tracker with Full Transparency (Recommended):**
```bash
streamlit run job_tracker.py
```
**🆕 NEW Transparency Features:**
- 📝 **Matched Keywords** column shows exact triggers  
- 🎯 **Filter Result** column explains decisions
- ⚙️ **Filter Config** shows settings used
- 📊 **Keyword Analysis** section with frequency breakdown
- 🏠📊🔧 Enhanced skill category checkboxes

**Detailed Analytics Dashboard:**
```bash
streamlit run streamlit_linkedin_scraper.py
```
- Legacy dashboard with comprehensive visualizations
- Funnel analysis, skills heatmaps, word clouds

### 3. Test Your Filter Logic
```bash
python test_filter_logic.py
```
- **Tests all 16 filter combinations**
- **Validates backwards compatibility** (100% tested)
- **Shows filter behavior** for different job scenarios

### 4. Validate Configuration
```bash
python -c "from config import Config; Config.validate(); print('✅ Configuration valid')"
```

## 🔒 Security & Configuration

### Environment Variables (Secure)
All sensitive configuration is now handled through environment variables in `.env` files:

- ✅ **Secure**: Credentials never appear in code
- ✅ **Flexible**: Easy to change without code modification  
- ✅ **Documented**: Clear examples in `.env.example`

### Legacy Configuration (Backward Compatible)
The system still supports the old configuration files as fallback:
- `tg_config.json` — Telegram credentials
- `google_sheets_credentials.json` — Google Sheets API credentials

### Security Best Practices
- ❌ **Never commit** `.env`, `tg_config.json`, or `google_sheets_credentials.json`
- ✅ **Always use** `.env.example` for documentation
- ✅ **Keep** sensitive files in `.gitignore`
- ✅ **Rotate** credentials periodically

## Выходные данные

- Результаты сохраняются в Excel-файл.
- В Telegram отправляются текстовые уведомления и аналитические графики (bar chart, p-chart, skills chart).

## 📋 Requirements

- **Python 3.8+**
- **Google Chrome** and matching ChromeDriver
- **Google Sheets API** credentials (for data storage)
- **Telegram Bot** (optional, for notifications)

## 🔍 Error Monitoring

The system includes built-in error tracking:

```bash
# Enable error logging
python setup_logging.py

# Check logs
ls logs/
tail -f logs/errors_$(date +%Y%m%d).log
```

Logs help identify:
- Configuration issues
- API connection problems  
- Scraping failures
- Performance bottlenecks

## 🛡️ Security Notes

- 🔒 **Never commit** sensitive files to repositories
- ✅ **Use** `.env` files for all credentials
- ✅ **Rotate** API keys and tokens regularly
- ✅ **Monitor** logs for unauthorized access attempts
- ✅ **Keep** dependencies updated for security patches

### Files Already in .gitignore
```
.env                           # Your credentials
logs/                          # Error logs  
*.xlsx                         # Output data
google_sheets_credentials.json # API credentials
tg_config.json                # Telegram config
.streamlit/secrets.toml       # Streamlit secrets
```

## 📋 Environment Variables Reference

### Required Variables
```bash
# Google Sheets Integration
LINKEDIN_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
LINKEDIN_CREDS_PATH=/path/to/google_sheets_credentials.json
```

### Optional Variables
```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF...
TELEGRAM_CHAT_ID=123456789

# Chrome Automation
CHROME_PROFILE_PATH=/path/to/selenium/profile
CHROME_BINARY_PATH=/path/to/chrome.exe
CHROMEDRIVER_PATH=/path/to/chromedriver.exe

# Output Files
OUTPUT_FILE_PATH=/path/to/output/companies_usa_remote.xlsx
```

### Configuration Validation
Test your setup:
```bash
# Validate required variables
python -c "from config import Config; Config.validate(['LINKEDIN_SHEET_URL', 'LINKEDIN_CREDS_PATH'])"

# Check all configuration
python -c "from config import Config; print(Config.get_all())"
```

## Лицензия

MIT License
