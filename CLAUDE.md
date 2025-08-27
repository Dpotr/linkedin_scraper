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

**Run the main LinkedIn scraper (with new modular filtering):**
```bash
python "universal parser_wo_semantic_chatgpt.py"
```

**Run the enhanced job tracker (RECOMMENDED):**
```bash
streamlit run job_tracker.py
```

**Run comprehensive filter testing:**
```bash
python test_filter_logic.py
```

**Run the old analytics dashboard (LEGACY):**
```bash
streamlit run streamlit_linkedin_scraper.py
```

**Install dependencies:**
```bash
pip install pandas requests matplotlib openpyxl selenium langdetect undetected-chromedriver sentence-transformers streamlit wordcloud gspread python-dotenv
```

## Architecture Overview

This is a LinkedIn job scraping and analytics automation system with three main components:

### Core Scraper (`universal parser_wo_semantic_chatgpt.py`) - **NEW MODULAR FILTERING**
- **Main entry point**: Tkinter GUI application with configurable filtering options
- **Modular filter system**: GUI checkboxes for Remote/Visa/Skills requirements with AND/OR logic
- **Enhanced vocabulary**: 55+ new keywords across all categories (hybrid, h1b sponsor, sap ibp, mrp, etc.)
- **Transparent logging**: Detailed filter reasons and matched keywords for every job decision
- **Configurable exclusions**: Block remote-prohibited jobs option
- **Multi-stage logging**: Each job goes through stages (Viewed → Filtered → Passed filters → TG message sent) with detailed reasons
- **Output formats**: Saves to Excel files and Google Sheets, sends notifications to Telegram
- **Backwards compatible**: Default settings maintain exact previous behavior
- **Selenium automation**: Uses undetected ChromeDriver with custom Chrome profiles

### Job Tracker Dashboard (`job_tracker.py`) - **ENHANCED WITH TRANSPARENCY**
- **Streamlined interface**: Focused on job application workflow, not analytics theater
- **Full transparency**: Shows matched keywords, filter reasons, and configuration used
- **Enhanced columns**: Anaplan/SAP/Planning checkboxes, detailed filter results
- **Filter analysis**: Keyword frequency analysis and filter success/failure breakdown
- **Key features**: Multi-select filters, date ranges, priority scoring, export to CSV
- **KPIs**: Open jobs, pending follow-ups, response rate tracking
- **Secure config**: Uses `.streamlit/secrets.toml` and environment variables
- **Performance**: Single data load with 5-minute caching, no duplicate requests
- **Data source**: Google Sheets via service account with proper error handling

### Legacy Analytics Dashboard (`streamlit_linkedin_scraper.py`) - DEPRECATED
- **Issues**: 406 lines, duplicate data loading, over-engineered visualizations
- **Problems**: No export, single-select filters, mixed languages, hardcoded credentials
- **Status**: Kept for reference but should use `job_tracker.py` instead

### Support Scripts & Configuration
- `config.py`: **NEW** - Centralized configuration management with environment variables
- `test_filter_logic.py`: **NEW** - Comprehensive test suite for filter validation (backwards compatibility tested)
- `.env.example`: **NEW** - Template for environment variable configuration
- `setup_logging.py`: **NEW** - Logging utilities and configuration
- `clean_google_sheet_job_urls.py`: Utility for cleaning job URL data in Google Sheets
- `archive/`: Contains legacy versions and backup files

## Configuration Files

**Important**: These files contain sensitive data and should never be committed:
- `tg_config.json`: Telegram bot token and chat ID
- `google_sheets_credentials.json`: Google Sheets API credentials
- `companies_usa_remote.xlsx`: Output Excel file with job data
- `.streamlit/secrets.toml`: Streamlit dashboard credentials
- `.env`: Environment variables (optional, use `.env.example` as template)

## ✨ NEW: Modular Filtering System

### Filter Configuration Options (GUI)
The scraper now includes configurable filtering through simple GUI checkboxes:

**Location Requirements:**
- ☑ **Accept Remote Jobs** - Includes remote, hybrid, wfh, distributed team, etc.
- ☑ **Accept Visa Sponsorship Jobs** - Includes h1b sponsor, relocation assistance, etc.
- **Logic**: OR/AND dropdown (OR = either is fine, AND = both required)

**Skills Requirements:**
- ☑ **Require Technical Skills** - Must have Anaplan/SAP/Planning keywords

**Exclusions:**
- ☑ **Block jobs that prohibit remote work** - Filters out "onsite only", "in-office", etc.

### Filter Modes Supported
1. **Remote-only mode**: Uncheck visa, check remote + block onsite-only
2. **Visa-focus mode**: Uncheck remote, check visa only  
3. **Flexible location**: Both checked with OR logic (default)
4. **Strict requirements**: Both checked with AND logic
5. **Skills-optional**: Uncheck skills requirement for broader search

### Enhanced Vocabulary (55+ New Keywords)
- **Remote**: hybrid, wfh, remote-first, distributed team, virtual position, location flexible
- **Visa**: h1b sponsor, green card sponsor, immigration assistance, tn visa
- **Anaplan**: hyperion, adaptive insights, workday adaptive, epm, fp&a
- **SAP**: sap ibp (focused addition per user request)
- **Planning**: mrp, erp planning, cpfr, demand sensing, supply chain optimization

## Key Architecture Patterns

### Job Processing Pipeline
1. **Web scraping**: Selenium automation loads LinkedIn job pages
2. **Content extraction**: Job title, company, description, publish date parsing
3. **Modular keyword matching**: Configurable multi-category filtering with detailed reasoning
4. **Transparent logging**: Each job stage logged with specific filter reasons and matched keywords
5. **Analytics**: Enhanced Streamlit dashboard with full transparency and filter analysis

### Data Flow
- Scraped data → Excel files + Google Sheets (with filter config tracking)
- Google Sheets → Enhanced Streamlit dashboard (with matched keywords visibility)
- Filtered jobs → Telegram notifications with charts
- Filter decisions → Detailed logs with reasons and configurations

### Configuration Management
- **NEW**: Centralized `config.py` with environment variable support
- **NEW**: `.env` file support for sensitive configuration
- **Enhanced GUI**: Modular filter configuration through checkboxes
- **Backwards compatible**: Default settings maintain previous behavior
- **Transparent**: All filter decisions logged with detailed reasoning

## Development Notes

- Uses undetected ChromeDriver to avoid LinkedIn detection
- Implements robust scroll-until-loaded logic for paginated results
- Publish date parsing supports various LinkedIn formats ("N days ago", "Yesterday", etc.)
- **NEW**: All job processing stages logged with detailed filter reasoning
- **NEW**: Comprehensive test suite ensures backwards compatibility (100% tested)
- **NEW**: Modular filter system allows easy customization without code changes
- **NEW**: Filter transparency shows exactly why jobs pass/fail with specific keyword matches
- Remote work filtering is now configurable (can be blocking or non-blocking)

## Quality Assurance

- **Agent-validated**: All changes reviewed by code-frustration-assessor agent
- **Comprehensive testing**: 16 filter combinations tested against 7 job scenarios
- **Backwards compatibility**: Default settings maintain exact previous behavior
- **Production-ready**: Comprehensive error handling and logging
- **User-friendly**: Non-developer can easily configure through GUI checkboxes