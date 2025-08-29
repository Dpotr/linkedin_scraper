#!/usr/bin/env python3
"""
CV Upload Interface Component
Handles file upload, processing, and display of CV analysis results
"""

import streamlit as st
from typing import Optional
import os
from modules.cv_parser import parse_uploaded_cv, CVData

class CVUploader:
    """CV upload and analysis interface"""
    
    def __init__(self):
        self.session_key = 'cv_data'
        self.file_key = 'uploaded_cv_file'
    
    def render_upload_interface(self) -> Optional[CVData]:
        """Render the CV upload interface and return parsed CV data"""
        
        st.sidebar.header("📄 Upload Your CV")
        
        # File uploader
        uploaded_file = st.sidebar.file_uploader(
            "Choose your CV file",
            type=['pdf', 'docx', 'doc'],
            help="Upload PDF, DOC, or DOCX format",
            key=self.file_key
        )
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = None
        
        # Process uploaded file
        if uploaded_file is not None:
            # Check if this is a new file
            if (not hasattr(st.session_state, 'last_uploaded_file') or 
                st.session_state.last_uploaded_file != uploaded_file.name):
                
                with st.sidebar:
                    st.info("🔄 Processing CV...")
                    progress_bar = st.progress(0)
                    
                    try:
                        # Parse the CV
                        progress_bar.progress(30)
                        cv_data = parse_uploaded_cv(uploaded_file)
                        progress_bar.progress(100)
                        
                        if cv_data:
                            # Store in session state
                            st.session_state[self.session_key] = cv_data
                            st.session_state.last_uploaded_file = uploaded_file.name
                            st.success("✅ CV processed successfully!")
                            
                            # Show quick analysis
                            self.display_cv_summary(cv_data)
                        else:
                            st.error("❌ Failed to process CV")
                            return None
                            
                    except Exception as e:
                        st.error(f"❌ Error processing CV: {str(e)}")
                        return None
                    finally:
                        progress_bar.empty()
            else:
                # File already processed
                cv_data = st.session_state[self.session_key]
                if cv_data:
                    st.sidebar.success("✅ CV loaded")
                    self.display_cv_summary(cv_data)
        
        # Return current CV data
        return st.session_state.get(self.session_key, None)
    
    def display_cv_summary(self, cv_data: CVData):
        """Display CV analysis summary in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("**📊 CV Analysis**")
            
            # Completeness score
            completeness = cv_data.completeness_score
            st.metric("CV Completeness", f"{completeness:.0f}%")
            
            # Experience level
            st.write(f"**Experience:** {cv_data.experience_level.title()}")
            if cv_data.years_experience > 0:
                st.write(f"**Years:** {cv_data.years_experience}")
            
            # Skills count
            st.write(f"**Skills Found:** {len(cv_data.skills)}")
            
            # Industries
            if cv_data.industries:
                st.write(f"**Industries:** {', '.join(cv_data.industries[:2])}")
            
            # Show detailed analysis in expander
            with st.expander("📋 Detailed Analysis"):
                self.display_detailed_analysis(cv_data)
    
    def display_detailed_analysis(self, cv_data: CVData):
        """Display detailed CV analysis"""
        
        # Skills breakdown
        if cv_data.skills:
            st.write("**🎯 Skills Extracted:**")
            skills_display = cv_data.skills[:15]  # Show first 15
            for skill in skills_display:
                st.write(f"• {skill}")
            
            if len(cv_data.skills) > 15:
                st.caption(f"... and {len(cv_data.skills) - 15} more")
        
        # Experience details
        st.write("**💼 Experience Level:**")
        st.write(f"• Level: {cv_data.experience_level.title()}")
        if cv_data.years_experience > 0:
            st.write(f"• Years: {cv_data.years_experience}")
        
        # Industries
        if cv_data.industries:
            st.write("**🏭 Industries:**")
            for industry in cv_data.industries:
                st.write(f"• {industry}")
        
        # Education
        if cv_data.education:
            st.write("**🎓 Education:**")
            for edu in cv_data.education:
                st.write(f"• {edu}")
        
        # Certifications
        if cv_data.certifications:
            st.write("**📜 Certifications:**")
            for cert in cv_data.certifications:
                st.write(f"• {cert}")
        
        # Improvement suggestions
        self.display_improvement_suggestions(cv_data)
    
    def display_improvement_suggestions(self, cv_data: CVData):
        """Display suggestions to improve CV completeness"""
        suggestions = []
        
        # Check what's missing
        if len(cv_data.skills) < 10:
            suggestions.append("Consider adding more specific technical skills")
        
        if not cv_data.certifications:
            suggestions.append("Add professional certifications if you have any")
        
        if not cv_data.education:
            suggestions.append("Include education details")
        
        if cv_data.years_experience == 0:
            suggestions.append("Include specific years of experience")
        
        if not cv_data.industries:
            suggestions.append("Mention specific industries you've worked in")
        
        if suggestions:
            st.write("**💡 Improvement Suggestions:**")
            for suggestion in suggestions[:3]:  # Show top 3
                st.write(f"• {suggestion}")
    
    def render_cv_preferences_interface(self, cv_data: CVData) -> dict:
        """Render interface for CV-based preferences"""
        preferences = {}
        
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Job Preferences")
        
        # Auto-populate from CV or use defaults
        default_remote = True  # Most people prefer remote nowadays
        default_visa = False   # Assume local unless specified
        
        # Remote work preference
        preferences['remote_preference'] = st.sidebar.checkbox(
            "🏠 Prefer Remote Work",
            value=default_remote,
            help="Prioritize remote-friendly positions"
        )
        
        # Visa sponsorship need
        preferences['needs_visa'] = st.sidebar.checkbox(
            "🛂 Need Visa Sponsorship",
            value=default_visa,
            help="Require visa sponsorship or relocation assistance"
        )
        
        # Experience level preference
        experience_options = ['Any', 'Junior', 'Mid-level', 'Senior', 'Director']
        default_experience = cv_data.experience_level.title() if cv_data.experience_level != 'unknown' else 'Any'
        
        preferences['experience_preference'] = st.sidebar.selectbox(
            "💼 Target Experience Level",
            options=experience_options,
            index=experience_options.index(default_experience) if default_experience in experience_options else 0,
            help="Filter jobs by experience level"
        )
        
        # Skills priority
        if cv_data.skills:
            preferences['priority_skills'] = st.sidebar.multiselect(
                "🎯 Priority Skills",
                options=cv_data.skills,
                default=cv_data.skills[:5],  # Default to top 5 skills
                help="Skills to prioritize in job matching"
            )
        else:
            preferences['priority_skills'] = []
        
        # Industry preference
        if cv_data.industries:
            preferences['target_industries'] = st.sidebar.multiselect(
                "🏭 Target Industries",
                options=cv_data.industries + ['Technology', 'Manufacturing', 'Retail', 'Consulting', 'Finance'],
                default=cv_data.industries,
                help="Industries to focus on"
            )
        else:
            preferences['target_industries'] = []
        
        # Salary expectations (optional)
        preferences['min_salary'] = st.sidebar.number_input(
            "💰 Minimum Salary (optional)",
            min_value=0,
            max_value=500000,
            value=0,
            step=5000,
            help="Minimum acceptable salary (0 = no filter)"
        )
        
        # Refresh jobs button in sidebar
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Jobs Data", help="Load newest jobs from scraper and re-analyze"):
            # Import the load function to clear its specific cache
            import sys
            if 'linkedin_assistant' in sys.modules:
                from linkedin_assistant import load_jobs_data
                load_jobs_data.clear()
            else:
                st.cache_data.clear()
            st.sidebar.success("✅ Jobs refreshed!")
            st.rerun()
        
        return preferences
    
    def clear_cv_data(self):
        """Clear CV data from session"""
        if self.session_key in st.session_state:
            del st.session_state[self.session_key]
        if 'last_uploaded_file' in st.session_state:
            del st.session_state['last_uploaded_file']
    
    def get_cv_stats_for_header(self, cv_data: CVData) -> dict:
        """Get CV statistics for display in main header"""
        if not cv_data:
            return {}
        
        return {
            'cv_completeness': cv_data.completeness_score,
            'skills_count': len(cv_data.skills),
            'experience_level': cv_data.experience_level.title(),
            'years_experience': cv_data.years_experience,
            'industries_count': len(cv_data.industries)
        }

# Global CV uploader instance
cv_uploader = CVUploader()

def render_cv_upload() -> Optional[CVData]:
    """Convenience function for rendering CV upload interface"""
    return cv_uploader.render_upload_interface()

def render_cv_preferences(cv_data: CVData) -> dict:
    """Convenience function for rendering CV preferences"""
    return cv_uploader.render_cv_preferences_interface(cv_data)

def get_cv_header_stats(cv_data: CVData) -> dict:
    """Convenience function for getting CV stats for header"""
    return cv_uploader.get_cv_stats_for_header(cv_data)