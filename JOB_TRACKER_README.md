# LinkedIn Job Tracker Dashboard

A streamlined, focused dashboard for tracking job applications - no analytics theater, just practical workflow.

## Quick Start

```bash
streamlit run job_tracker.py
```

## Key Features

### 🎯 **Focus on Job Search Workflow**
- Multi-select filters for companies and skills
- Date range filtering (default: last 30 days)
- Application status tracking (Not Applied, Applied, Interview, Rejected, Offer)
- Priority scoring (visa support + remote work + recency)

### 📊 **Actionable KPIs**
- **Open Jobs**: Jobs not yet applied to
- **Applied**: Current applications sent
- **Need Follow-up**: Applications >7 days old
- **Response Rate**: % getting interviews/offers

### 💾 **Export & Persistence**
- One-click CSV export of filtered results
- Filters preserve selections during session
- 5-minute data caching for performance

## What's Different from Legacy Dashboard

| Feature | Legacy (`streamlit_linkedin_scraper.py`) | New (`job_tracker.py`) |
|---------|----------------------------------------|----------------------|
| **Lines of Code** | 406 lines | 180 lines |
| **Data Loading** | Loaded twice, no caching | Single load, 5-min cache |
| **Filters** | Single-select dropdowns | Multi-select with clear options |
| **Export** | ❌ None | ✅ CSV with applied filters |
| **Language** | Mixed Russian/English | English only |
| **Credentials** | Hardcoded paths | Secure `.streamlit/secrets.toml` |
| **Visualizations** | 7 complex charts | 3 focused KPIs |
| **Focus** | Analytics theater | Job application workflow |

## Configuration

### Setup `.streamlit/secrets.toml`:
```toml
sheets_creds_path = "path/to/google_sheets_credentials.json"
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

### Required Columns in Google Sheets:
- `Company`, `Vacancy Title`, `Job URL`
- `Timestamp`, `Stage`, `Skills`
- `Visa Sponsorship or Relocation`, `Remote`, `Remote Prohibited`
- `Application_Status` (will be added automatically)

## Agent Validation Results

✅ **Code-Frustration-Assessor**: LOW RISK (vs CRITICAL for legacy)
✅ **Business-Analyst**: Addresses core job search workflow
✅ **Streamlit-BI-Developer**: Clean, focused implementation

## Usage Tips

1. **Daily Workflow**: Filter by "Not Applied" → Export CSV → Apply to jobs
2. **Follow-ups**: Check "Need Follow-up" section weekly
3. **Strategy**: Monitor Response Rate to adjust approach
4. **Priority**: Focus on high-priority scores first

## Security

- `.streamlit/secrets.toml` is gitignored (never commit credentials)
- Google Sheets accessed via service account
- No sensitive data exposed in UI

---

**Migration**: Replace `streamlit_linkedin_scraper.py` usage with `job_tracker.py` for better workflow.