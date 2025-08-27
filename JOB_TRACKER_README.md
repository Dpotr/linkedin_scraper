# LinkedIn Job Tracker Dashboard v2.4

A streamlined, focused dashboard for tracking job applications with **complete transparency** into the filtering process - no analytics theater, just practical workflow with full visibility.

## Quick Start

```bash
streamlit run job_tracker.py
```

## 🚀 Key Features (v2.4 Enhanced)

### 🎯 **Focus on Job Search Workflow**
- Multi-select filters for companies and skills
- Date range filtering (default: last 30 days)
- Application status tracking (Not Applied, Applied, Interview, Rejected, Offer)
- Priority scoring (visa support + remote work + recency)

### 🔍 **NEW: Complete Transparency**
- 📝 **Matched Keywords Column**: See exactly which terms triggered each job match
- 🎯 **Filter Result Column**: Detailed explanations for why jobs passed/failed (e.g. "missing location: needs remote OR visa")
- ⚙️ **Filter Config Column**: Track which filter settings were used when processing each job
- 🏠📊🔧 **Enhanced Skill Checkboxes**: Visual indicators for Remote/Visa/Anaplan/SAP/Planning with icons
- 📈 **Keyword Analysis Section**: Expandable section showing frequency breakdown of matched terms
- 🔍 **Filter Transparency Panel**: Success/failure rates with detailed reasons

### 📊 **Actionable KPIs**
- **Open Jobs**: Jobs not yet applied to
- **Applied**: Current applications sent
- **Need Follow-up**: Applications >7 days old
- **Response Rate**: % getting interviews/offers

### 💾 **Export & Persistence**
- One-click CSV export of filtered results with transparency data
- Filters preserve selections during session
- 5-minute data caching for performance

### 🔧 **NEW: Sidebar Keyword Reference**
- Quick reference showing current vocabulary used for matching
- Categories: Remote, Visa, Anaplan, SAP, Planning keywords
- Helpful for understanding what triggers job matches

## What's Different from Legacy Dashboard

| Feature | Legacy (`streamlit_linkedin_scraper.py`) | **Enhanced v2.4** (`job_tracker.py`) |
|---------|----------------------------------------|----------------------|
| **Lines of Code** | 406 lines | ~350 lines (enhanced with transparency) |
| **Data Loading** | Loaded twice, no caching | Single load, 5-min cache |
| **Filters** | Single-select dropdowns | Multi-select with clear options |
| **Export** | ❌ None | ✅ CSV with transparency data |
| **Language** | Mixed Russian/English | English only |
| **Credentials** | Hardcoded paths | Secure environment variables + secrets |
| **Visualizations** | 7 complex charts | 3 focused KPIs + transparency analysis |
| **Focus** | Analytics theater | Job application workflow |
| **🆕 Transparency** | ❌ Basic boolean flags only | ✅ **Full filter reasoning & matched keywords** |
| **🆕 Filter Analysis** | ❌ None | ✅ **Keyword frequency & success rates** |
| **🆕 Column Details** | ❌ Simple checkboxes | ✅ **Detailed explanations with icons** |
| **🆕 Sidebar Help** | ❌ None | ✅ **Keyword reference guide** |

## Configuration

### Option 1: Environment Variables (Recommended)
```bash
# Create .env file:
LINKEDIN_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
LINKEDIN_CREDS_PATH=./google_sheets_credentials.json
```

### Option 2: Streamlit Secrets (Legacy)
```toml
# .streamlit/secrets.toml:
sheets_creds_path = "path/to/google_sheets_credentials.json"
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Note**: Environment variables take priority. System maintains backward compatibility.

### Required Columns in Google Sheets:

**Core Job Data:**
- `Company`, `Vacancy Title`, `Job URL`, `Timestamp`

**Filter Results (NEW v2.4):**
- `Stage` - Shows filter result (e.g. "Passed filters", "Filtered (missing location: needs remote OR visa)")
- `Matched key words` - Exact keywords that triggered the match
- `Filter Config` - Settings used when processing the job

**Skills & Categories:**
- `Skills`, `Visa Sponsorship or Relocation`, `Remote`, `Remote Prohibited`
- `Anaplan`, `SAP APO`, `Planning` - Individual skill category flags

**Application Tracking:**
- `Application_Status` (will be added automatically if missing)

**🆕 v2.4 Enhancement:** The dashboard now shows complete transparency about why each job was matched or filtered, making it much easier to understand and optimize your job search strategy.

## Agent Validation Results

✅ **Code-Frustration-Assessor**: LOW RISK (vs CRITICAL for legacy)
✅ **Business-Analyst**: Addresses core job search workflow
✅ **Streamlit-BI-Developer**: Clean, focused implementation

## Usage Tips (Enhanced with v2.4 Transparency)

### 🎯 **Daily Job Search Workflow**
1. **Filter by "Not Applied"** → Review matched keywords to understand why jobs qualified
2. **Check Filter Result column** → Understand which jobs passed/failed and why
3. **Export CSV with transparency data** → Apply to jobs with context
4. **Use Priority column** → Focus on highest-scoring opportunities first

### 🔍 **NEW: Filter Analysis Workflow** 
5. **Open "Filter Transparency" section** → See most common matched keywords
6. **Review keyword frequency** → Understand which terms are most effective
7. **Check filter success rates** → Identify areas for strategy improvement
8. **Use Sidebar Keyword Reference** → Understand current vocabulary being matched

### 📊 **Strategy Optimization**
9. **Monitor Response Rate** → Adjust approach based on performance
10. **Analyze failed filters** → Understand what job types are being missed
11. **Review Filter Config** → See which settings were most effective
12. **Follow-ups**: Check "Need Follow-up" section weekly with matched keywords context

### 💡 **Pro Tips**
- **Keyword Insights**: Look at "Matched key words" to see exactly why jobs qualified
- **Filter Debugging**: Use "Stage" column to understand filtering decisions
- **Strategy Pivoting**: Use filter analysis to adjust your job search focus
- **Context Export**: CSV exports include all transparency data for offline analysis

## Security (v3.0 Improvements)

- ✅ **Environment Variables**: Primary configuration method
- ✅ **Backward Compatible**: Still supports `.streamlit/secrets.toml`
- ✅ **Secure by Default**: All sensitive files gitignored
- ✅ **Clear Error Messages**: Helpful guidance when config missing
- ✅ **Graceful Degradation**: System continues even if optional services fail

---

**Migration**: Replace `streamlit_linkedin_scraper.py` usage with `job_tracker.py` for better workflow.