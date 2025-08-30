LinkedIn Automation Launch Scripts v2.8
========================================

Professional-grade launch infrastructure for LinkedIn job automation suite.
Features enterprise-level error handling, dependency validation, and portability.

🚀 NEW in v2.8: Cycle Tracking Support
- All dashboards now support cycle-based filtering
- Track job discovery patterns across scraping runs
- Enhanced analytics with New/Duplicates metrics

Available Scripts:
-----------------

🔧 MAIN TOOLS:
1. run_scraper.bat
   - Launches the main LinkedIn job scraper
   - Opens GUI with configurable filtering options
   - Now tracks cycle numbers for historical analysis
   - Saves results to Excel and Google Sheets

📊 ANALYTICS DASHBOARDS:
2. run_fresh_dashboard.bat  ⭐ RECOMMENDED
   - Launches the Fresh UI Analytics Dashboard
   - Modern tab-based design with interactive charts
   - 🔄 NEW: Cycle multiselect filter in advanced options
   - Best choice for comprehensive data analysis

3. run_job_tracker.bat
   - Launches the Job Tracker Dashboard  
   - Workflow-focused with filter transparency
   - 🔄 NEW: Cycle selectbox filter + New/Duplicates KPI
   - Shows matched keywords and application tracking
   - Optimized for job application management

4. run_linkedin_assistant.bat
   - Launches the LinkedIn Assistant Dashboard
   - Specialized LinkedIn automation features
   - 🔄 NEW: Cycle tracking support

5. run_legacy_analytics.bat  (DEPRECATED)
   - Launches the old analytics dashboard
   - 🔄 NEW: Basic cycle filtering with Russian labels
   - Kept for compatibility, use Fresh Dashboard instead

🔄 Cycle Tracking Features:
--------------------------
- Filter jobs by specific scraping cycles
- Track scraper performance over time
- Understand job discovery patterns
- Clear new vs duplicate job metrics
- Historical analysis capabilities

⚙️ How to Use:
--------------
Simply double-click any .bat file to launch the corresponding tool.

🛡️ ENTERPRISE-GRADE FEATURES:
- Dynamic path resolution (works from any location)
- Comprehensive dependency validation
- Clear error messages with troubleshooting steps
- Automatic directory navigation
- Cross-environment compatibility

The scripts will automatically:
✅ Navigate to the correct project folder
✅ Check Python installation and version
✅ Verify Streamlit availability (for dashboards)
✅ Confirm required script files exist
✅ Display helpful error messages if issues found
✅ Start the application with proper error handling

For dashboards, your browser will open automatically at http://localhost:8501

📋 Requirements:
---------------
- Python 3.7+ with required packages installed
- Streamlit (for dashboards): pip install streamlit
- Chrome browser (for scraper functionality)
- Active internet connection
- Google Sheets credentials configured (for data access)

🔧 Troubleshooting:
------------------
If a script fails, it will show clear error messages explaining:
❌ Missing Python installation → Install Python from python.org
❌ Missing Streamlit package → Run: pip install streamlit
❌ Missing script files → Check project directory structure
❌ Path issues → Scripts show current working directory for debugging
❌ Permission errors → Run as administrator if needed

🚀 Professional Features:
------------------------
- No hard-coded paths (portable across installations)
- Comprehensive error handling and user guidance
- Compatible with different Python installations
- Works regardless of current working directory
- Enterprise-ready deployment infrastructure

📈 Performance Notes:
--------------------
- Dashboard data is cached for 5 minutes for optimal performance
- Cycle filtering operations are optimized for large datasets
- Multiple dashboards can run simultaneously on different ports
- Background processes are properly managed

For additional support or feature requests, check the project documentation.