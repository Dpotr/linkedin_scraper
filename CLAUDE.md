# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**🤖 Agent-Validated Infrastructure**: All deployment and control mechanisms have been validated by the code-frustration-assessor to prevent common development frustration patterns.

### AVAILABLE AGENTS ###

**name: code-frustration-assessor**
**description**: Use this agent when you need to evaluate code implementations, feature additions, or technical solutions to identify potential frustration patterns before they waste development time. Examples: <example>Context: User has just implemented a complex ensemble forecasting method and wants to validate it before integration. user: 'I've created a weighted ensemble method that combines 5 different forecasting approaches with dynamic weight adjustment based on recent performance. Here's the implementation...' assistant: 'Let me use the code-frustration-assessor agent to evaluate this implementation for potential frustration patterns before we proceed with integration.' </example> <example>Context: User is considering a technical solution to improve forecast accuracy. user: 'I'm thinking of adding outlier detection with statistical capping at the 95th percentile to improve our MAPE scores' assistant: 'Before we implement this, let me use the code-frustration-assessor agent to assess whether this approach addresses the root problem or might fall into common frustration patterns.' </example> <example>Context: User has completed a feature and claims it's ready for production. user: 'The new rolling feature extraction is complete and tested. All unit tests pass.' assistant: 'Let me use the code-frustration-assessor agent to evaluate this implementation against the 10 frustration patterns to ensure it will deliver actual business value.' </example>



**IMPORTANT AGENT USAGE RULES**:
**RULE #1**: ALWAYS use the code-frustration-assessor for general feature evaluation. That agent provide critical validation that prevents wasted development time and trading losses.
**RULE #2**: At the end of EVERY todo list, include a task to validate with the appropriate agent. This ensures quality control at each development checkpoint.
**RULE #3**: When an agent provides recommendations, create a new todo list incorporating their feedback before proceeding with implementation.
**RULE #4**: If an agent response includes "IMPORTANT: USE THIS AGENT AGAIN NEXT TIME", make note to use that agent for similar future tasks.


## Common Commands

**Run the main LinkedIn scraper:**
```bash
python "universal parser_wo_semantic_chatgpt.py"
```

**Run the NEW streamlined job tracker (RECOMMENDED):**
```bash
streamlit run job_tracker.py
```

**Run the old analytics dashboard (LEGACY):**
```bash
streamlit run streamlit_linkedin_scraper.py
```

**Clean Google Sheets job URLs:**
```bash
python clean_google_sheet_job_urls.py
```

**Install dependencies (if requirements.txt exists):**
```bash
pip install pandas requests matplotlib openpyxl selenium langdetect undetected-chromedriver sentence-transformers streamlit wordcloud gspread
```

## Architecture Overview

This is a LinkedIn job scraping and analytics automation system with three main components:

### Core Scraper (`universal parser_wo_semantic_chatgpt.py`)
- **Main entry point**: Tkinter GUI application for LinkedIn job scraping
- **Keywords matching system**: Uses predefined keyword lists (KEYWORDS_VISA, KEYWORDS_ANAPLAN, KEYWORDS_SAP, KEYWORDS_PLANNING) to filter relevant jobs
- **Multi-stage logging**: Each job goes through stages (Viewed → Filtered → Passed filters → TG message sent) with separate logging for each stage
- **Output formats**: Saves to Excel files and Google Sheets, sends notifications to Telegram
- **Remote work filtering**: Special handling for "Remote Prohibited" flags - jobs are marked but not filtered out completely
- **Selenium automation**: Uses undetected ChromeDriver with custom Chrome profiles

### Job Tracker Dashboard (`job_tracker.py`) - RECOMMENDED
- **Streamlined interface**: Focused on job application workflow, not analytics theater
- **Key features**: Multi-select filters, date ranges, priority scoring, export to CSV
- **KPIs**: Open jobs, pending follow-ups, response rate tracking
- **Secure config**: Uses `.streamlit/secrets.toml` for credentials (never commit this file)
- **Performance**: Single data load with 5-minute caching, no duplicate requests
- **Data source**: Google Sheets via service account with proper error handling

### Legacy Analytics Dashboard (`streamlit_linkedin_scraper.py`) - DEPRECATED
- **Issues**: 406 lines, duplicate data loading, over-engineered visualizations
- **Problems**: No export, single-select filters, mixed languages, hardcoded credentials
- **Status**: Kept for reference but should use `job_tracker.py` instead

### Support Scripts
- `clean_google_sheet_job_urls.py`: Utility for cleaning job URL data in Google Sheets
- `archive/`: Contains legacy versions and backup files

## Configuration Files

**Important**: These files contain sensitive data and should never be committed:
- `tg_config.json`: Telegram bot token and chat ID
- `google_sheets_credentials.json`: Google Sheets API credentials
- `companies_usa_remote.xlsx`: Output Excel file with job data

## Key Architecture Patterns

### Job Processing Pipeline
1. **Web scraping**: Selenium automation loads LinkedIn job pages
2. **Content extraction**: Job title, company, description, publish date parsing
3. **Keyword matching**: Multi-category keyword filtering with boolean flags
4. **Stage logging**: Each job stage logged separately in output
5. **Analytics**: Streamlit dashboard provides visualization and filtering

### Data Flow
- Scraped data → Excel files + Google Sheets
- Google Sheets → Streamlit dashboard
- Filtered jobs → Telegram notifications with charts

### Configuration Management
- Default values defined in main script (paths, credentials)
- Tkinter GUI allows runtime configuration override
- Keyword lists are configurable through the interface

## Development Notes

- Uses undetected ChromeDriver to avoid LinkedIn detection
- Implements robust scroll-until-loaded logic for paginated results
- Publish date parsing supports various LinkedIn formats ("N days ago", "Yesterday", etc.)
- All job processing stages are logged transparently for debugging
- Remote work filtering is non-blocking (jobs marked but not excluded)