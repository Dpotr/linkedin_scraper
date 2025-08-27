#!/usr/bin/env python3
"""
LinkedIn Job Tracker - Streamlined Dashboard
Focused on job application workflow, not analytics theater.
"""

import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
import os
from io import BytesIO
from config import Config

# Page config
st.set_page_config(
    page_title="LinkedIn Job Tracker", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration - using environment variables for security
# Create .env file based on .env.example with your actual values

@st.cache_resource
def get_sheets_client():
    """Get cached Google Sheets client with improved error messages."""
    try:
        # Try environment variable first, fall back to secrets for compatibility
        creds_path = Config.CREDS_PATH or st.secrets.get("sheets_creds_path", None)
        if not creds_path:
            st.error("📋 Google Sheets credentials not configured.")
            st.info("To fix: Add LINKEDIN_CREDS_PATH to your .env file")
            return None
        if not os.path.exists(creds_path):
            st.error(f"📁 Credentials file not found: {creds_path}")
            st.info("To fix: Check the file path in your .env file")
            return None
        return gspread.service_account(filename=creds_path)
    except FileNotFoundError as e:
        st.error(f"📁 Configuration file missing: {e}")
        st.info("To fix: Ensure google_sheets_credentials.json exists")
        return None
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)[:100]}...")
        st.info("To fix: Check your internet connection and credentials")
        return None

@st.cache_data(ttl=300, show_spinner="Loading job data...")
def load_jobs(sheet_url):
    """Load and process job data with 5-minute cache"""
    client = get_sheets_client()
    if not client:
        return pd.DataFrame()
    
    try:
        sheet = client.open_by_url(sheet_url)
        df = pd.DataFrame(sheet.sheet1.get_all_records())
        
        if df.empty:
            return df
        
        # Data cleaning and type conversion
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Days_Ago'] = (datetime.now() - df['Timestamp']).dt.days
        
        # Boolean columns
        bool_cols = [
            "Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning",
            "No Relocation Support", "Remote", "Remote Prohibited", "Already Applied"
        ]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().map({"TRUE": True, "FALSE": False}).fillna(False)
        
        # Add application tracking columns if missing
        if 'Application_Status' not in df.columns:
            df['Application_Status'] = 'Not Applied'
        if 'Application_Date' not in df.columns:
            df['Application_Date'] = pd.NaT
        if 'Priority' not in df.columns:
            df['Priority'] = 0
            
        # Calculate priority score
        df['Priority'] = 0
        if 'Visa Sponsorship or Relocation' in df.columns:
            df.loc[df['Visa Sponsorship or Relocation'] == True, 'Priority'] += 50
        if 'Remote' in df.columns:
            df.loc[df['Remote'] == True, 'Priority'] += 30
        df.loc[df['Days_Ago'] <= 7, 'Priority'] += 20
        df.loc[df['Days_Ago'] <= 3, 'Priority'] += 10
        
        # Clean company and vacancy title
        if 'Company' in df.columns:
            df['Company'] = df['Company'].astype(str).str.strip()
        if 'Vacancy Title' in df.columns:
            df['Vacancy Title'] = df['Vacancy Title'].astype(str).str.strip()
            
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def export_to_csv(df):
    """Convert dataframe to CSV for download"""
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    return buffer.getvalue()

def main():
    st.title("📊 LinkedIn Job Tracker")
    st.markdown("Focused on job application workflow - find, filter, export, track.")
    
    # Load data - try environment variable first, fall back to secrets for compatibility
    sheet_url = Config.SHEET_URL or st.secrets.get("sheet_url", None)
    if not sheet_url:
        st.error("📊 Google Sheet URL not configured")
        st.info("To fix: Add LINKEDIN_SHEET_URL to your .env file")
        st.stop()  # Stop execution cleanly
    df = load_jobs(sheet_url)
    
    if df.empty:
        st.warning("📭 No job data found in the Google Sheet")
        st.info("This could mean:\n- The sheet is empty\n- Connection issues\n- Wrong sheet URL")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    days_options = [7, 14, 30, 60, 90, 365]
    days_back = st.sidebar.selectbox(
        "📅 Date Range",
        days_options,
        index=2,  # Default to 30 days
        format_func=lambda x: f"Last {x} days"
    )
    df_filtered = df[df['Days_Ago'] <= days_back] if 'Days_Ago' in df.columns else df
    
    # Company filter (multi-select)
    if 'Company' in df.columns:
        companies = sorted(df['Company'].dropna().unique())
        selected_companies = st.sidebar.multiselect(
            "🏢 Companies",
            options=companies,
            default=[],
            help="Select multiple companies or leave empty for all"
        )
        if selected_companies:
            df_filtered = df_filtered[df_filtered['Company'].isin(selected_companies)]
    
    # Skills filter (multi-select)
    if 'Skills' in df.columns:
        all_skills = set()
        for skills in df['Skills'].dropna():
            all_skills.update([s.strip() for s in str(skills).split(",") if s.strip()])
        skills_list = sorted(all_skills)
        
        selected_skills = st.sidebar.multiselect(
            "🎯 Skills",
            options=skills_list,
            default=[],
            help="Select multiple skills or leave empty for all"
        )
        if selected_skills:
            df_filtered = df_filtered[
                df_filtered['Skills'].apply(
                    lambda x: any(skill in str(x) for skill in selected_skills)
                )
            ]
    
    # Application status filter
    status_options = ['Not Applied', 'Applied', 'Interview', 'Rejected', 'Offer']
    selected_statuses = st.sidebar.multiselect(
        "📝 Application Status",
        options=status_options,
        default=['Not Applied', 'Applied'],
        help="Filter by application status"
    )
    df_filtered = df_filtered[df_filtered['Application_Status'].isin(selected_statuses)]
    
    # Remote work filter
    remote_options = st.sidebar.multiselect(
        "🏠 Remote Work",
        options=['Remote Available', 'Remote Prohibited', 'No Info'],
        default=['Remote Available', 'No Info'],
        help="Filter by remote work availability"
    )
    if 'Remote' in df_filtered.columns and 'Remote Prohibited' in df_filtered.columns:
        remote_filter = pd.Series([False] * len(df_filtered), index=df_filtered.index)
        if 'Remote Available' in remote_options:
            remote_filter |= (df_filtered['Remote'] == True)
        if 'Remote Prohibited' in remote_options:
            remote_filter |= (df_filtered['Remote Prohibited'] == True)
        if 'No Info' in remote_options:
            remote_filter |= ((df_filtered['Remote'] == False) & (df_filtered['Remote Prohibited'] == False))
        df_filtered = df_filtered[remote_filter]
    
    # Sidebar transparency section
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔍 Keyword Matching Info"):
        st.write("**Current Keywords Used:**")
        st.write("🏠 **Remote:** remote, wfh, hybrid, work from home")
        st.write("🛂 **Visa:** h1b sponsor, visa sponsorship, relocation")
        st.write("📊 **Anaplan:** anaplan, hyperion, adaptive insights, fp&a")
        st.write("🔧 **SAP:** sap apo, sap ibp, sap scm")
        st.write("📋 **Planning:** supply planning, mrp, demand planning")
        st.caption("Keywords are automatically matched in job descriptions")
    
    # Key Performance Indicators
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate KPIs
    open_jobs = len(df_filtered[df_filtered['Application_Status'] == 'Not Applied'])
    applied_jobs = len(df_filtered[df_filtered['Application_Status'] == 'Applied'])
    pending_followup = len(df_filtered[
        (df_filtered['Application_Status'] == 'Applied') & 
        (df_filtered['Days_Ago'] > 7)
    ])
    
    total_applied = len(df_filtered[df_filtered['Application_Status'] != 'Not Applied'])
    interviews = len(df_filtered[df_filtered['Application_Status'].isin(['Interview', 'Offer'])])
    response_rate = (interviews / max(1, total_applied)) * 100
    
    # Display KPIs
    col1.metric("🎯 Open Jobs", open_jobs, help="Jobs not yet applied to")
    col2.metric("📤 Applied", applied_jobs, help="Applications sent")
    col3.metric("⏰ Need Follow-up", pending_followup, help="Applied >7 days ago")
    col4.metric("📈 Response Rate", f"{response_rate:.1f}%", help="% getting interviews/offers")
    
    # Action buttons
    st.markdown("---")
    col_export, col_refresh = st.columns([1, 4])
    
    # Export functionality
    if not df_filtered.empty:
        csv_data = export_to_csv(df_filtered)
        col_export.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name=f"linkedin_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Export filtered results to CSV"
        )
    
    # Refresh data
    if col_refresh.button("🔄 Refresh Data", help="Clear cache and reload from Google Sheets"):
        st.cache_data.clear()
        st.rerun()
    
    # Main jobs table
    st.subheader(f"📋 Jobs ({len(df_filtered)} matching filters)")
    
    if df_filtered.empty:
        st.info("No jobs match your current filters. Try adjusting the criteria above.")
        return
    
    # Prepare display columns
    display_cols = ['Company', 'Vacancy Title', 'Priority', 'Days_Ago', 'Application_Status']
    
    # Add relevant columns if they exist - including transparency columns
    optional_cols = [
        'Remote', 'Visa Sponsorship or Relocation', 'Anaplan', 'SAP APO', 'Planning',
        'Skills', 'Matched key words', 'Stage', 'Filter Config'
    ]
    for col in optional_cols:
        if col in df_filtered.columns:
            display_cols.append(col)
    
    # Sort by priority score (highest first)
    df_display = df_filtered[display_cols].sort_values('Priority', ascending=False)
    
    # Format the display
    if 'Job URL' in df_filtered.columns:
        # Create clickable links
        df_display['Apply_Link'] = df_filtered['Job URL'].apply(
            lambda x: f"[Open Job]({x})" if pd.notnull(x) and x else "N/A"
        )
        display_cols.append('Apply_Link')
    
    # Show the table
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Priority": st.column_config.NumberColumn("Priority", help="Auto-calculated priority score"),
            "Days_Ago": st.column_config.NumberColumn("Days Ago", help="Days since job was posted"),
            "Apply_Link": st.column_config.LinkColumn("Job Link", help="Click to open job posting"),
            "Matched key words": st.column_config.TextColumn("Matched Keywords", help="Specific keywords that triggered this job match", width="medium"),
            "Stage": st.column_config.TextColumn("Filter Result", help="Why this job passed or failed filters", width="medium"),
            "Filter Config": st.column_config.TextColumn("Filter Settings", help="Filter configuration used when processing this job", width="large"),
            "Remote": st.column_config.CheckboxColumn("🏠 Remote", help="Remote work available"),
            "Visa Sponsorship or Relocation": st.column_config.CheckboxColumn("🛂 Visa", help="Visa sponsorship or relocation assistance"),
            "Anaplan": st.column_config.CheckboxColumn("📊 Anaplan", help="Anaplan skills mentioned"),
            "SAP APO": st.column_config.CheckboxColumn("🔧 SAP", help="SAP APO/SCM skills mentioned"),
            "Planning": st.column_config.CheckboxColumn("📋 Planning", help="Supply chain planning skills mentioned"),
        }
    )
    
    # Transparency section - show filter analysis
    if 'Matched key words' in df_filtered.columns or 'Stage' in df_filtered.columns:
        with st.expander("🔍 Filter Transparency - See Why Jobs Matched/Failed"):
            if 'Matched key words' in df_filtered.columns:
                st.subheader("Most Common Matched Keywords")
                # Extract and count all matched keywords
                all_keywords = []
                for keywords in df_filtered['Matched key words'].dropna():
                    if str(keywords).strip():
                        all_keywords.extend([kw.strip() for kw in str(keywords).split(',') if kw.strip()])
                
                if all_keywords:
                    from collections import Counter
                    keyword_counts = Counter(all_keywords)
                    col_kw1, col_kw2 = st.columns(2)
                    
                    with col_kw1:
                        st.write("**🏠 Location Keywords:**")
                        location_keywords = [kw for kw, count in keyword_counts.most_common() if any(x in kw.lower() for x in ['remote', 'visa', 'relocation', 'sponsor', 'home', 'hybrid'])]
                        for kw in location_keywords[:10]:
                            st.write(f"• {kw} ({keyword_counts[kw]})")
                    
                    with col_kw2:
                        st.write("**💼 Skills Keywords:**")
                        skill_keywords = [kw for kw, count in keyword_counts.most_common() if any(x in kw.lower() for x in ['anaplan', 'sap', 'planning', 'supply', 'demand', 'mrp', 'erp'])]
                        for kw in skill_keywords[:10]:
                            st.write(f"• {kw} ({keyword_counts[kw]})")
            
            if 'Stage' in df_filtered.columns:
                st.subheader("Filter Results Breakdown")
                stage_counts = df_filtered['Stage'].value_counts()
                col_stage1, col_stage2 = st.columns(2)
                
                with col_stage1:
                    st.write("**✅ Passed Filters:**")
                    passed = stage_counts[stage_counts.index.str.contains('Passed', na=False)]
                    for stage, count in passed.items():
                        st.write(f"• {stage}: {count}")
                
                with col_stage2:
                    st.write("**❌ Failed Filters:**")
                    failed = stage_counts[stage_counts.index.str.contains('Filtered', na=False)]
                    for stage, count in failed.head(5).items():
                        st.write(f"• {stage}: {count}")

    # Footer info
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    
    if 'Timestamp' in df.columns and not df['Timestamp'].isna().all():
        last_update = df['Timestamp'].max()
        col_info1.caption(f"📅 Last data update: {last_update.strftime('%Y-%m-%d %H:%M')}")
    
    col_info2.caption("🔄 Data cached for 5 minutes | Built with Streamlit")
    
    # Quick stats expander
    with st.expander("📊 Quick Statistics"):
        if not df_filtered.empty:
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.write("**Top Companies:**")
                if 'Company' in df_filtered.columns:
                    company_counts = df_filtered['Company'].value_counts().head(5)
                    for company, count in company_counts.items():
                        st.write(f"• {company}: {count} jobs")
            
            with col_stat2:
                st.write("**Application Status Breakdown:**")
                status_counts = df_filtered['Application_Status'].value_counts()
                for status, count in status_counts.items():
                    st.write(f"• {status}: {count} jobs")

if __name__ == "__main__":
    main()