#!/usr/bin/env python3
"""
CV Parser Module - Extract skills and information from CV files
Supports PDF, DOC, DOCX formats with NLP-based skill extraction
"""

import os
import re
import io
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

# File processing imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    
try:
    from docx import Document
except ImportError:
    Document = None

try:
    import spacy
    # Try to load English model
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = None
except ImportError:
    spacy = None
    nlp = None

@dataclass
class CVData:
    """Structured CV information"""
    raw_text: str
    skills: List[str]
    experience_level: str  # junior, mid, senior, lead, director
    industries: List[str]
    roles: List[str]
    education: List[str]
    certifications: List[str]
    years_experience: int
    completeness_score: float
    
class CVParser:
    """Main CV parsing class"""
    
    # Predefined skill categories for better matching
    SKILL_CATEGORIES = {
        'technical': [
            'anaplan', 'sap', 'sap apo', 'sap ibp', 'sap scm', 'oracle', 'hyperion',
            'power bi', 'tableau', 'excel', 'python', 'r', 'sql', 'vba', 'javascript',
            'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'jenkins'
        ],
        'planning': [
            'supply chain', 'demand planning', 'supply planning', 'inventory management',
            'mrp', 'erp', 'cpfr', 'forecasting', 'procurement', 'logistics',
            'production planning', 'capacity planning', 'master scheduling'
        ],
        'analytics': [
            'data analysis', 'business intelligence', 'reporting', 'dashboard',
            'kpi', 'metrics', 'modeling', 'statistics', 'machine learning',
            'predictive analytics', 'data visualization'
        ],
        'soft_skills': [
            'leadership', 'project management', 'communication', 'teamwork',
            'problem solving', 'analytical thinking', 'stakeholder management',
            'process improvement', 'change management', 'training'
        ]
    }
    
    EXPERIENCE_PATTERNS = {
        'junior': ['intern', 'associate', 'junior', 'entry level', 'graduate', '0-2 years'],
        'mid': ['analyst', 'specialist', 'coordinator', '2-5 years', '3-7 years'],
        'senior': ['senior', 'lead', 'principal', '5+ years', '7+ years', 'expert'],
        'director': ['director', 'manager', 'head of', 'vp', 'vice president', '10+ years']
    }
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc'] if self._check_dependencies() else []
        
    def _check_dependencies(self) -> bool:
        """Check if required libraries are installed"""
        missing = []
        if PyPDF2 is None:
            missing.append('PyPDF2')
        if Document is None:
            missing.append('python-docx')
        if nlp is None:
            missing.append('spacy (en_core_web_sm model)')
            
        if missing:
            st.error(f"❌ Missing dependencies: {', '.join(missing)}")
            st.info("Run: pip install PyPDF2 python-docx spacy && python -m spacy download en_core_web_sm")
            return False
        return True
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        if PyPDF2 is None:
            return ""
            
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"PDF extraction error: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        if Document is None:
            return ""
            
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            st.error(f"DOCX extraction error: {str(e)}")
            return ""
    
    def parse_skills(self, text: str) -> List[str]:
        """Extract skills from CV text using keyword matching and NLP"""
        text_lower = text.lower()
        found_skills = []
        
        # Extract skills from predefined categories
        for category, skills in self.SKILL_CATEGORIES.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill.title())
        
        # Use spaCy for additional entity extraction if available
        if nlp:
            doc = nlp(text)
            # Look for technology/tool entities
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN'] and 
                    len(token.text) > 2 and 
                    token.text.lower() not in ['years', 'experience', 'work', 'company']):
                    # Simple heuristic for potential skills
                    if any(keyword in token.text.lower() for keyword in ['soft', 'plan', 'manage', 'analy']):
                        found_skills.append(token.text.title())
        
        # Remove duplicates and sort
        return sorted(list(set(found_skills)))
    
    def extract_experience_level(self, text: str) -> Tuple[str, int]:
        """Determine experience level and years from CV text"""
        text_lower = text.lower()
        years_experience = 0
        experience_level = 'junior'
        
        # Look for explicit years mentions
        year_patterns = [
            r'(\d+)\+?\s*years?\s*of\s*experience',
            r'(\d+)\+?\s*years?\s*experience',
            r'experience:\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                years_experience = max(years_experience, int(matches[0]))
        
        # Classify based on keywords and years
        for level, keywords in self.EXPERIENCE_PATTERNS.items():
            if any(keyword in text_lower for keyword in keywords):
                if level == 'director':
                    experience_level = 'director'
                elif level == 'senior' and experience_level != 'director':
                    experience_level = 'senior'
                elif level == 'mid' and experience_level not in ['senior', 'director']:
                    experience_level = 'mid'
        
        # Override with years if we found them
        if years_experience >= 10:
            experience_level = 'director'
        elif years_experience >= 7:
            experience_level = 'senior'
        elif years_experience >= 3:
            experience_level = 'mid'
        elif years_experience < 3 and years_experience > 0:
            experience_level = 'junior'
            
        return experience_level, years_experience
    
    def identify_industries(self, text: str) -> List[str]:
        """Identify industries mentioned in CV"""
        text_lower = text.lower()
        industries = []
        
        industry_keywords = {
            'supply_chain': ['supply chain', 'logistics', 'procurement', 'distribution'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'plant'],
            'retail': ['retail', 'consumer goods', 'fmcg', 'cpg'],
            'technology': ['technology', 'software', 'tech', 'it', 'digital'],
            'consulting': ['consulting', 'advisory', 'consultant'],
            'finance': ['finance', 'banking', 'investment', 'financial'],
            'healthcare': ['healthcare', 'pharmaceutical', 'medical', 'health']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                industries.append(industry.replace('_', ' ').title())
                
        return industries
    
    def parse_education(self, text: str) -> List[str]:
        """Extract education information"""
        education = []
        
        degree_patterns = [
            r'\b(bachelor|master|phd|doctorate|mba|degree)\b.*?in\s+([^\n,\.]+)',
            r'\b(bs|ms|ba|ma|phd|mba)\b\s+([^\n,\.]+)',
            r'(university|college)\s+of\s+([^\n,\.]+)'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if isinstance(match, tuple):
                    education.append(' '.join(match).title().strip())
                else:
                    education.append(match.title().strip())
        
        return list(set(education))
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications and professional qualifications"""
        certifications = []
        
        cert_keywords = [
            'pmp', 'scor', 'cpim', 'cscp', 'cltd', 'apics', 'six sigma',
            'lean', 'prince2', 'itil', 'aws certified', 'azure certified',
            'google certified', 'tableau certified', 'sap certified'
        ]
        
        text_lower = text.lower()
        for cert in cert_keywords:
            if cert in text_lower:
                certifications.append(cert.upper())
                
        return certifications
    
    def calculate_cv_completeness_score(self, cv_data: CVData) -> float:
        """Calculate how complete the CV data is (0-100%)"""
        score = 0
        max_score = 10
        
        # Skills (weight: 3)
        if cv_data.skills:
            score += min(3, len(cv_data.skills) / 5 * 3)
        
        # Experience level (weight: 2)
        if cv_data.experience_level != 'unknown':
            score += 2
            
        # Years of experience (weight: 1)
        if cv_data.years_experience > 0:
            score += 1
            
        # Industries (weight: 1)
        if cv_data.industries:
            score += 1
            
        # Education (weight: 1)
        if cv_data.education:
            score += 1
            
        # Certifications (weight: 1)
        if cv_data.certifications:
            score += 1
            
        # Text length (weight: 1)
        if len(cv_data.raw_text) > 500:
            score += 1
            
        return (score / max_score) * 100
    
    def parse_cv_file(self, uploaded_file) -> Optional[CVData]:
        """Main method to parse uploaded CV file"""
        if not self.supported_formats:
            return None
            
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in self.supported_formats:
            st.error(f"❌ Unsupported file format: {file_extension}")
            st.info(f"Supported formats: {', '.join(self.supported_formats)}")
            return None
        
        # Read file bytes
        file_bytes = uploaded_file.read()
        
        # Extract text based on file type
        if file_extension == '.pdf':
            raw_text = self.extract_text_from_pdf(file_bytes)
        elif file_extension in ['.docx', '.doc']:
            raw_text = self.extract_text_from_docx(file_bytes)
        else:
            return None
        
        if not raw_text.strip():
            st.error("❌ Could not extract text from file")
            return None
        
        # Parse extracted information
        skills = self.parse_skills(raw_text)
        experience_level, years_experience = self.extract_experience_level(raw_text)
        industries = self.identify_industries(raw_text)
        education = self.parse_education(raw_text)
        certifications = self.extract_certifications(raw_text)
        
        # Create CV data object
        cv_data = CVData(
            raw_text=raw_text,
            skills=skills,
            experience_level=experience_level,
            industries=industries,
            roles=[],  # Could be extracted later
            education=education,
            certifications=certifications,
            years_experience=years_experience,
            completeness_score=0  # Will be calculated below
        )
        
        # Calculate completeness score
        cv_data.completeness_score = self.calculate_cv_completeness_score(cv_data)
        
        return cv_data

# Global parser instance
cv_parser = CVParser()

def parse_uploaded_cv(uploaded_file) -> Optional[CVData]:
    """Convenience function for parsing uploaded CV"""
    return cv_parser.parse_cv_file(uploaded_file)