#!/usr/bin/env python3
"""
LinkedIn CV-Powered Job Assistant - Standalone Application
Sophisticated job matching based on CV analysis and AI recommendations
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from io import BytesIO

# Add modules to path
sys.path.append(os.path.dirname(__file__))

# Import our custom modules
from modules.cv_parser import CVData, parse_uploaded_cv
from modules.recommendation_engine import JobMatch, get_job_recommendations
from components.cv_uploader import render_cv_upload, render_cv_preferences, get_cv_header_stats
from config import Config

# Page configuration
st.set_page_config(
    page_title="🤖 LinkedIn CV Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.job-card {
    background-color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e6e6e6;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.match-score-high { color: #28a745; font-weight: bold; }
.match-score-medium { color: #ffc107; font-weight: bold; }
.match-score-low { color: #dc3545; font-weight: bold; }

.skills-matched { background-color: #d4edda; padding: 0.2rem 0.5rem; border-radius: 0.3rem; margin: 0.2rem; display: inline-block; }
.skills-missing { background-color: #f8d7da; padding: 0.2rem 0.5rem; border-radius: 0.3rem; margin: 0.2rem; display: inline-block; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner="Loading job data...")
def load_jobs_data():
    """Load job data from Google Sheets with caching"""
    try:
        import gspread
        
        # Get configuration
        sheet_url = Config.SHEET_URL or st.secrets.get("sheet_url", None)
        creds_path = Config.CREDS_PATH or st.secrets.get("sheets_creds_path", None)
        
        if not sheet_url or not creds_path:
            st.error("📊 Configuration missing - check .env file")
            return pd.DataFrame()
        
        # Load data
        gc = gspread.service_account(filename=creds_path)
        sheet = gc.open_by_url(sheet_url)
        df = pd.DataFrame(sheet.sheet1.get_all_records())
        
        if df.empty:
            return df
        
        # Data cleaning
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
        
        # Clean text columns
        text_cols = ['Company', 'Vacancy Title', 'Skills']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def render_cv_enhanced_header(cv_data: Optional[CVData], jobs_count: int = 0, jobs_df: pd.DataFrame = None):
    """Render header with CV-enhanced metrics"""
    st.title("🎯 LinkedIn Job Matching Assistant")
    
    # Show data freshness info
    if jobs_df is not None and not jobs_df.empty and 'Timestamp' in jobs_df.columns:
        latest_job = jobs_df['Timestamp'].max()
        if pd.notnull(latest_job):
            st.markdown(f"*Smart keyword matching and scoring based on your CV* | 🔄 Latest job: {latest_job.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.markdown("*Smart keyword matching and scoring based on your CV*")
    else:
        st.markdown("*Smart keyword matching and scoring based on your CV*")
    
    if cv_data:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("CV Completeness", f"{cv_data.completeness_score:.0f}%")
        with col2:
            st.metric("Skills Detected", len(cv_data.skills))
        with col3:
            st.metric("Experience Level", cv_data.experience_level.title())
        with col4:
            if cv_data.years_experience > 0:
                st.metric("Years Experience", cv_data.years_experience)
            else:
                st.metric("Industries", len(cv_data.industries))
        with col5:
            # Show jobs count with freshness indicator
            jobs_today = 0
            if jobs_df is not None and not jobs_df.empty and 'Days_Ago' in jobs_df.columns:
                jobs_today = len(jobs_df[jobs_df['Days_Ago'] <= 1])
            
            if jobs_today > 0:
                st.metric("Jobs Available", jobs_count, delta=f"{jobs_today} new today")
            else:
                st.metric("Jobs Available", jobs_count)
    else:
        # Show basic job stats even without CV
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Jobs", jobs_count)
        with col2:
            if jobs_df is not None and not jobs_df.empty and 'Days_Ago' in jobs_df.columns:
                jobs_today = len(jobs_df[jobs_df['Days_Ago'] <= 1])
                st.metric("New Today", jobs_today)
        with col3:
            if jobs_df is not None and not jobs_df.empty and 'Days_Ago' in jobs_df.columns:
                jobs_week = len(jobs_df[jobs_df['Days_Ago'] <= 7])
                st.metric("This Week", jobs_week)
        
        st.info("👈 Upload your CV in the sidebar to get personalized job recommendations!")

def render_priority_jobs(job_matches: List[JobMatch], cv_data: CVData):
    """Render priority job recommendations"""
    st.header("🎯 Your Priority Job Matches")
    
    if not job_matches:
        st.warning("No job matches found. Try adjusting your preferences or uploading a different CV.")
        return
    
    # Show top 10 matches
    top_matches = job_matches[:10]
    
    for i, match in enumerate(top_matches, 1):
        # Color coding for match score
        if match.match_score >= 80:
            score_class = "match-score-high"
            score_emoji = "🟢"
        elif match.match_score >= 60:
            score_class = "match-score-medium" 
            score_emoji = "🟡"
        else:
            score_class = "match-score-low"
            score_emoji = "🔴"
        
        # Job card container
        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <h4>{score_emoji} #{i} {match.company} - {match.title}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics row
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f'<p class="{score_class}">Match: {match.match_score:.0f}%</p>', unsafe_allow_html=True)
            with col2:
                st.write(f"Skills: {match.skill_match_score:.0f}%")
            with col3:
                st.write(f"Experience: {match.experience_match_score:.0f}%")
            with col4:
                st.write(f"Industry: {match.industry_match_score:.0f}%")
            with col5:
                st.write(f"Location: {match.location_match_score:.0f}%")
            
            # Details in expandable section
            with st.expander(f"📋 Details & Analysis"):
                
                # Match reasons
                st.write("**🎯 Why This Job Matches:**")
                for reason in match.match_reasons:
                    st.write(f"• {reason}")
                
                # Skills analysis
                col_skills1, col_skills2 = st.columns(2)
                
                with col_skills1:
                    if match.matched_skills:
                        st.write("**✅ Skills You Have:**")
                        for skill in match.matched_skills[:10]:
                            st.markdown(f'<span class="skills-matched">{skill}</span>', unsafe_allow_html=True)
                
                with col_skills2:
                    if match.missing_skills:
                        st.write("**📚 Skills to Develop:**")
                        for skill in match.missing_skills[:5]:
                            st.markdown(f'<span class="skills-missing">{skill}</span>', unsafe_allow_html=True)
                
                # Career growth and recommendation
                st.write(f"**🚀 Career Growth:** {match.career_growth_indicator}")
                st.write(f"**💡 Recommendation:** {match.recommendation}")
            
            # Calculation transparency section (separate expander to avoid nesting)
            if match.calculation_details:
                with st.expander("🔍 Detailed Score Breakdown - How This Score Was Calculated"):
                    st.write("**🧮 Final Weighted Calculation:**")
                    st.code(match.calculation_details.weighted_calculation)
                    
                    st.write("**🎯 Skills Analysis:**")
                    st.code(match.calculation_details.skill_calculation)
                    
                    st.write("**💼 Experience Analysis:**")
                    st.code(match.calculation_details.experience_calculation)
                    
                    st.write("**🏭 Industry Analysis:**")
                    st.code(match.calculation_details.industry_calculation)
                    
                    st.write("**🌍 Location Analysis:**")
                    st.code(match.calculation_details.location_calculation)
                    
                    st.write("**⚖️ Weighting System Used:**")
                    weights_text = f"Skills: {match.calculation_details.score_weights['skill']*100}% weight\n"
                    weights_text += f"Experience: {match.calculation_details.score_weights['experience']*100}% weight\n"
                    weights_text += f"Industry: {match.calculation_details.score_weights['industry']*100}% weight\n"
                    weights_text += f"Location: {match.calculation_details.score_weights['location']*100}% weight"
                    st.code(weights_text)
                    
                    st.caption("💡 This shows exactly how your match percentage was calculated - no black box algorithms!")
            else:
                st.info("🔍 Calculation details not available for this job match.")
            
            # Action buttons (use index and unique identifier)
            unique_id = f"{i}_{abs(hash(str(match.company) + str(match.title) + str(match.match_score)))}"
            col_action1, col_action2, col_action3, col_action4 = st.columns(4)
            
            with col_action1:
                if st.button(f"✅ Apply", key=f"apply_{unique_id}", help="Mark as applied"):
                    st.success("Marked as applied!")
            
            with col_action2:
                if st.button(f"⭐ Save", key=f"save_{unique_id}", help="Save for later"):
                    st.info("Saved for later!")
            
            with col_action3:
                if st.button(f"❌ Skip", key=f"skip_{unique_id}", help="Not interested"):
                    st.warning("Skipped")
            
            with col_action4:
                if st.button(f"🔗 View Job", key=f"view_{unique_id}", help="Open job posting"):
                    # This would open the job URL in real implementation
                    st.info("Job link would open here")
            
            st.markdown("---")

def render_application_pipeline(job_matches: List[JobMatch]):
    """Render application pipeline tracking"""
    st.header("📊 Your Application Pipeline")
    
    # Pipeline metrics
    total_jobs = len(job_matches)
    high_priority = len([m for m in job_matches if m.match_score >= 80])
    medium_priority = len([m for m in job_matches if 60 <= m.match_score < 80])
    low_priority = len([m for m in job_matches if m.match_score < 60])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 High Priority", high_priority, help="80%+ match score")
    with col2:
        st.metric("📋 Medium Priority", medium_priority, help="60-79% match score")
    with col3:
        st.metric("📝 Low Priority", low_priority, help="<60% match score")
    with col4:
        st.metric("📊 Total Jobs", total_jobs)
    
    # Pipeline stages (mock data - would be real in production)
    pipeline_data = {
        'Stage': ['To Apply', 'Applied', 'Interview', 'Offer', 'Rejected'],
        'Count': [high_priority, 0, 0, 0, 0],  # Mock numbers
        'This Week': [high_priority, 0, 0, 0, 0]
    }
    
    st.write("**Application Progress:**")
    pipeline_df = pd.DataFrame(pipeline_data)
    st.dataframe(pipeline_df, hide_index=True)

def render_insights_and_analytics(job_matches: List[JobMatch], cv_data: CVData):
    """Render insights and analytics section"""
    st.header("🔍 Insights & Market Analysis")
    
    if not job_matches:
        return
    
    # Skills in demand analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Skills in Demand")
        
        # Collect all job skills
        all_job_skills = []
        for match in job_matches:
            all_job_skills.extend(match.matched_skills + match.missing_skills)
        
        if all_job_skills:
            from collections import Counter
            skill_counts = Counter(all_job_skills).most_common(10)
            
            skills_df = pd.DataFrame(skill_counts, columns=['Skill', 'Frequency'])
            st.dataframe(skills_df, hide_index=True)
        else:
            st.info("No skills data available")
    
    with col2:
        st.subheader("🎯 Your Competitive Advantage")
        
        # Skills you have that are in demand
        cv_skills_lower = [skill.lower() for skill in cv_data.skills]
        competitive_skills = []
        
        for match in job_matches[:20]:  # Top 20 jobs
            for skill in match.matched_skills:
                if skill.lower() in cv_skills_lower:
                    competitive_skills.append(skill)
        
        if competitive_skills:
            from collections import Counter
            competitive_counts = Counter(competitive_skills).most_common(8)
            
            for skill, count in competitive_counts:
                st.write(f"✅ **{skill}** - Found in {count} jobs")
        else:
            st.info("Upload CV to see competitive analysis")
    
    # Match score distribution
    st.subheader("📊 Match Score Distribution")
    
    if job_matches:
        scores = [match.match_score for match in job_matches]
        score_ranges = {
            'Excellent (80-100%)': len([s for s in scores if s >= 80]),
            'Good (60-79%)': len([s for s in scores if 60 <= s < 80]),
            'Fair (40-59%)': len([s for s in scores if 40 <= s < 60]),
            'Poor (<40%)': len([s for s in scores if s < 40])
        }
        
        score_df = pd.DataFrame(list(score_ranges.items()), columns=['Range', 'Count'])
        st.bar_chart(score_df.set_index('Range'))
    else:
        st.info("No data to analyze")

def export_results_to_csv(job_matches: List[JobMatch]) -> bytes:
    """Export job matches to CSV"""
    if not job_matches:
        return b""
    
    # Prepare data for export
    export_data = []
    for match in job_matches:
        export_data.append({
            'Company': match.company,
            'Title': match.title,
            'Match Score': f"{match.match_score:.1f}%",
            'Skills Match': f"{match.skill_match_score:.1f}%",
            'Experience Match': f"{match.experience_match_score:.1f}%",
            'Industry Match': f"{match.industry_match_score:.1f}%",
            'Location Match': f"{match.location_match_score:.1f}%",
            'Matched Skills': ', '.join(match.matched_skills[:10]),
            'Missing Skills': ', '.join(match.missing_skills[:5]),
            'Career Growth': match.career_growth_indicator,
            'Recommendation': match.recommendation,
            'Priority Score': f"{match.priority_score:.1f}",
            'Match Reasons': ' | '.join(match.match_reasons)
        })
    
    df = pd.DataFrame(export_data)
    
    # Convert to CSV
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    return buffer.getvalue()

def main():
    """Main application function"""
    
    # Sidebar - CV Upload and Preferences
    with st.sidebar:
        # Upload CV
        cv_data = render_cv_upload()
        
        # If CV is uploaded, show preferences
        user_preferences = {}
        if cv_data:
            user_preferences = render_cv_preferences(cv_data)
    
    # Load jobs data
    jobs_df = load_jobs_data()
    
    # Header with CV-enhanced metrics
    render_cv_enhanced_header(cv_data, len(jobs_df), jobs_df)
    
    if jobs_df.empty:
        st.error("❌ No job data available. Check your Google Sheets connection.")
        return
    
    # If no CV uploaded, show instructions
    if not cv_data:
        st.markdown("""
        ## 🎯 Welcome to Your Job Matching Assistant!
        
        This system analyzes your CV and matches jobs based on **transparent keyword matching**:
        - **Skills matching** - Direct text comparison against 400+ predefined keywords
        - **Experience level** - Pattern matching for junior/mid/senior/director keywords
        - **Industry alignment** - Simple keyword matching for industry relevance
        - **Location preferences** - Basic filtering for remote/visa requirements
        
        **👈 Start by uploading your CV in the sidebar to get scored job matches!**
        
        ### What You'll Get (No Black Box):
        - 📊 **Transparent match scores** with exact calculation breakdowns
        - 🔍 **Full visibility** into how each percentage was calculated
        - 📈 **Simple weighted scoring** (Skills 40%, Experience 25%, Industry 20%, Location 15%)
        - 📋 **Clear skill gaps** showing exactly what's missing
        - ⚖️ **No hidden algorithms** - everything is explained step by step
        
        ### Supported CV Formats:
        - PDF (.pdf)
        - Microsoft Word (.docx, .doc)
        
        **🔍 Key Feature: Click "Detailed Score Breakdown" on any job to see exactly how the match percentage was calculated!**
        """)
        
        # Show sample data preview
        with st.expander("📊 Preview Available Jobs Data"):
            if not jobs_df.empty:
                preview_cols = ['Company', 'Vacancy Title', 'Remote', 'Visa Sponsorship or Relocation']
                available_cols = [col for col in preview_cols if col in jobs_df.columns]
                st.dataframe(jobs_df[available_cols].head(10), hide_index=True)
            else:
                st.info("No job data loaded")
        
        return
    
    # Get job recommendations based on CV
    with st.spinner("🤖 Analyzing jobs against your CV..."):
        job_matches = get_job_recommendations(jobs_df, cv_data, user_preferences)
    
    if not job_matches:
        st.warning("No matching jobs found. Try adjusting your preferences.")
        return
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Priority Jobs", "📊 Pipeline", "🔍 Insights"])
    
    with tab1:
        render_priority_jobs(job_matches, cv_data)
    
    with tab2:
        render_application_pipeline(job_matches)
    
    with tab3:
        render_insights_and_analytics(job_matches, cv_data)
    
    # Export and Refresh functionality
    st.markdown("---")
    col_export1, col_refresh1, col_info1 = st.columns([1, 1, 3])
    
    with col_export1:
        if job_matches:
            csv_data = export_results_to_csv(job_matches)
            st.download_button(
                label="📥 Export Results",
                data=csv_data,
                file_name=f"cv_job_matches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Export all job matches with CV analysis"
            )
    
    with col_refresh1:
        if st.button("🔄 Refresh Jobs", help="Load new jobs from Google Sheets and re-analyze with current CV"):
            # Clear the job data cache to force reload
            load_jobs_data.clear()
            st.success("✅ Jobs data refreshed! Re-analyzing matches...")
            st.rerun()
    
    with col_info1:
        st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                  f"Found {len(job_matches)} matches | "
                  f"CV completeness: {cv_data.completeness_score:.0f}%")

if __name__ == "__main__":
    main()