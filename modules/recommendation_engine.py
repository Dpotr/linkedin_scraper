#!/usr/bin/env python3
"""
CV-Powered Recommendation Engine
Matches jobs against CV data to provide personalized recommendations
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Try to import advanced matching libraries
try:
    from sentence_transformers import SentenceTransformer
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    semantic_model = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    sklearn_available = True
except ImportError:
    sklearn_available = False

try:
    from fuzzywuzzy import fuzz
    fuzzy_available = True
except ImportError:
    fuzzy_available = False

from .cv_parser import CVData

@dataclass
class CalculationDetails:
    """Detailed breakdown of how scores were calculated"""
    # Skills calculation
    total_job_skills: int
    matched_skills_count: int
    skill_calculation: str
    
    # Experience calculation  
    cv_experience_level: str
    job_experience_level: str
    experience_calculation: str
    
    # Industry calculation
    cv_industries: List[str]
    job_industry_keywords: List[str]
    industry_calculation: str
    
    # Location calculation
    remote_preference: bool
    job_remote: bool
    visa_needed: bool
    job_visa: bool
    location_calculation: str
    
    # Final weighted calculation
    score_weights: Dict[str, float]
    weighted_calculation: str

@dataclass
class JobMatch:
    """Job matching result with detailed scoring"""
    job_id: str
    company: str
    title: str
    match_score: float
    skill_match_score: float
    experience_match_score: float
    industry_match_score: float
    location_match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    match_reasons: List[str]
    skill_gaps: List[str]
    career_growth_indicator: str
    recommendation: str
    priority_score: float
    calculation_details: Optional[CalculationDetails] = None  # NEW: Detailed calculations

class RecommendationEngine:
    """Main recommendation engine class"""
    
    def __init__(self):
        self.semantic_enabled = semantic_model is not None
        self.sklearn_enabled = sklearn_available
        self.fuzzy_enabled = fuzzy_available
        
        # Skill synonyms for better matching
        self.skill_synonyms = {
            'anaplan': ['anaplan', 'adaptive insights', 'hyperion', 'epm'],
            'sap': ['sap apo', 'sap ibp', 'sap scm', 'sap pp', 'sap mm'],
            'planning': ['demand planning', 'supply planning', 'production planning', 'capacity planning'],
            'excel': ['microsoft excel', 'excel', 'vba', 'pivot tables', 'macros'],
            'python': ['python', 'pandas', 'numpy', 'jupyter'],
            'sql': ['sql', 'mysql', 'postgresql', 'oracle', 'sql server'],
            'power_bi': ['power bi', 'powerbi', 'dax', 'power query'],
            'tableau': ['tableau', 'tableau desktop', 'tableau server']
        }
        
        # Industry alignment patterns
        self.industry_patterns = {
            'supply_chain': ['supply chain', 'logistics', 'procurement', 'distribution'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'automotive'],
            'retail': ['retail', 'consumer goods', 'fmcg', 'cpg', 'e-commerce'],
            'technology': ['technology', 'software', 'tech', 'saas', 'digital'],
            'consulting': ['consulting', 'advisory', 'deloitte', 'mckinsey', 'pwc'],
            'finance': ['finance', 'banking', 'investment', 'financial services']
        }
        
        # Experience level mapping
        self.experience_levels = {
            'junior': ['junior', 'associate', 'analyst', 'coordinator', 'entry level'],
            'mid': ['senior analyst', 'specialist', 'manager', 'lead'],
            'senior': ['senior', 'principal', 'director', 'head of'],
            'director': ['director', 'vp', 'vice president', 'chief', 'executive']
        }
    
    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize and expand skills using synonyms"""
        normalized = set()
        
        for skill in skills:
            skill_lower = skill.lower()
            normalized.add(skill_lower)
            
            # Add synonyms
            for category, synonyms in self.skill_synonyms.items():
                if skill_lower in synonyms:
                    normalized.update(synonyms)
                    
        return list(normalized)
    
    def extract_job_skills(self, job_description: str) -> List[str]:
        """Extract skills from job description"""
        if not job_description:
            return []
            
        job_desc_lower = job_description.lower()
        found_skills = []
        
        # Extract skills from all synonym categories
        for category, synonyms in self.skill_synonyms.items():
            for synonym in synonyms:
                if synonym.lower() in job_desc_lower:
                    found_skills.append(synonym.lower())
                    
        return list(set(found_skills))
    
    def calculate_skill_match(self, cv_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str], List[str], str]:
        """Calculate skill match score with matched and missing skills and detailed calculation"""
        if not job_skills:
            calculation = "No skills required by job → 0% match"
            return 0.0, [], [], calculation
        
        cv_skills_norm = self.normalize_skills(cv_skills)
        job_skills_norm = self.normalize_skills(job_skills)
        
        matched_skills = []
        missing_skills = []
        
        # Direct matching
        direct_matches = 0
        for job_skill in job_skills_norm:
            if job_skill in cv_skills_norm:
                matched_skills.append(job_skill)
                direct_matches += 1
            else:
                missing_skills.append(job_skill)
        
        # Fuzzy matching for partial matches if available
        fuzzy_matches = 0
        if self.fuzzy_enabled and cv_skills_norm:
            for job_skill in list(missing_skills):
                best_match = max(cv_skills_norm, key=lambda cv_skill: fuzz.ratio(job_skill, cv_skill))
                similarity = fuzz.ratio(job_skill, best_match)
                if similarity > 75:
                    matched_skills.append(f"{job_skill} (~{best_match})")
                    missing_skills.remove(job_skill)
                    fuzzy_matches += 1
        
        # Calculate score
        if not job_skills_norm:
            calculation = "No skills to match → 0%"
            return 0.0, matched_skills, missing_skills, calculation
            
        match_score = len(matched_skills) / len(job_skills_norm) * 100
        
        # Create detailed calculation explanation
        total_skills = len(job_skills_norm)
        total_matches = len(matched_skills)
        
        calculation = f"Skills Match: {total_matches}/{total_skills} = {match_score:.1f}%\n"
        calculation += f"→ Direct matches: {direct_matches}\n"
        if fuzzy_matches > 0:
            calculation += f"→ Similar skills: {fuzzy_matches}\n"
        calculation += f"→ Missing skills: {len(missing_skills)}"
        
        return match_score, matched_skills, missing_skills, calculation
    
    def calculate_experience_match(self, cv_experience: str, cv_years: int, job_description: str) -> Tuple[float, str, str]:
        """Calculate experience level match with detailed calculation"""
        job_desc_lower = job_description.lower()
        
        # Extract required experience from job description
        required_years_patterns = [
            r'(\d+)\+?\s*years?\s*of\s*experience',
            r'(\d+)\+?\s*years?\s*experience',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?'
        ]
        
        required_years = 0
        for pattern in required_years_patterns:
            matches = re.findall(pattern, job_desc_lower)
            if matches:
                required_years = max(required_years, int(matches[0]))
        
        # Check experience level keywords
        required_level = 'mid'  # default
        detected_keywords = []
        for level, keywords in self.experience_levels.items():
            matching_keywords = [kw for kw in keywords if kw in job_desc_lower]
            if matching_keywords:
                required_level = level
                detected_keywords = matching_keywords
                break
        
        # Calculate match score
        level_hierarchy = {'junior': 1, 'mid': 2, 'senior': 3, 'director': 4}
        cv_level_score = level_hierarchy.get(cv_experience, 2)
        required_level_score = level_hierarchy.get(required_level, 2)
        
        # Build calculation explanation
        calculation = f"Experience Match Calculation:\n"
        calculation += f"→ Your level: {cv_experience} (score: {cv_level_score})\n"
        calculation += f"→ Job requires: {required_level} (score: {required_level_score})\n"
        
        if required_years > 0:
            calculation += f"→ Required years: {required_years}+\n"
        if detected_keywords:
            calculation += f"→ Keywords found: {', '.join(detected_keywords[:3])}\n"
        
        # Perfect match
        if cv_level_score == required_level_score:
            calculation += f"→ Perfect match: 100%"
            return 100.0, required_level, calculation
        
        # Overqualified (slight penalty)
        if cv_level_score > required_level_score:
            penalty = (cv_level_score - required_level_score) * 10
            score = max(70.0, 100.0 - penalty)
            calculation += f"→ Overqualified penalty: -{penalty}% = {score:.1f}%"
            return score, required_level, calculation
        
        # Underqualified (larger penalty)
        if cv_level_score < required_level_score:
            penalty = (required_level_score - cv_level_score) * 25
            score = max(20.0, 100.0 - penalty)
            calculation += f"→ Underqualified penalty: -{penalty}% = {score:.1f}%"
            return score, required_level, calculation
        
        calculation += f"→ Default moderate match: 60%"
        return 60.0, required_level, calculation  # default moderate match
    
    def calculate_industry_match(self, cv_industries: List[str], job_description: str, company: str) -> float:
        """Calculate industry alignment score"""
        if not cv_industries:
            return 50.0  # neutral if no industry info
        
        text_to_check = f"{job_description} {company}".lower()
        
        # Direct industry matching
        cv_industries_lower = [ind.lower() for ind in cv_industries]
        direct_matches = 0
        
        for industry, keywords in self.industry_patterns.items():
            if industry.replace('_', ' ') in cv_industries_lower:
                if any(keyword in text_to_check for keyword in keywords):
                    direct_matches += 1
        
        if direct_matches > 0:
            return min(100.0, 80.0 + direct_matches * 10)
        
        # Partial matching
        for cv_industry in cv_industries_lower:
            if cv_industry in text_to_check:
                return 70.0
        
        return 40.0  # low match if no industry alignment
    
    def calculate_location_match(self, job_data: Dict, user_preferences: Dict) -> float:
        """Calculate location preferences match"""
        score = 50.0  # neutral base
        
        # Remote work preference
        prefers_remote = user_preferences.get('remote_preference', True)
        job_remote = job_data.get('Remote', False)
        job_remote_prohibited = job_data.get('Remote Prohibited', False)
        
        if prefers_remote and job_remote and not job_remote_prohibited:
            score += 30
        elif prefers_remote and job_remote_prohibited:
            score -= 20
        elif not prefers_remote and not job_remote:
            score += 10
        
        # Visa sponsorship
        needs_visa = user_preferences.get('needs_visa', False)
        job_visa = job_data.get('Visa Sponsorship or Relocation', False)
        
        if needs_visa and job_visa:
            score += 20
        elif needs_visa and not job_visa:
            score -= 30
        elif not needs_visa:
            score += 5  # slight bonus for not needing visa
        
        return min(100.0, max(0.0, score))
    
    def generate_match_reasons(self, job_match: JobMatch, cv_data: CVData) -> List[str]:
        """Generate human-readable reasons for the match"""
        reasons = []
        
        # Skill match reasons
        if job_match.skill_match_score > 80:
            reasons.append(f"Strong skills match ({len(job_match.matched_skills)} skills aligned)")
        elif job_match.skill_match_score > 60:
            reasons.append(f"Good skills match with some gaps")
        elif job_match.skill_match_score > 30:
            reasons.append(f"Partial skills match - learning opportunity")
        else:
            reasons.append(f"Limited skills match - significant training needed")
        
        # Experience match reasons
        if job_match.experience_match_score > 90:
            reasons.append(f"Perfect experience level match")
        elif job_match.experience_match_score > 70:
            reasons.append(f"Good experience level fit")
        elif job_match.experience_match_score < 50:
            reasons.append(f"Experience level mismatch")
        
        # Industry match reasons
        if job_match.industry_match_score > 80:
            reasons.append(f"Strong industry alignment")
        elif job_match.industry_match_score < 50:
            reasons.append(f"Different industry - career pivot opportunity")
        
        # Location reasons
        if job_match.location_match_score > 80:
            reasons.append(f"Excellent location/work arrangement fit")
        elif job_match.location_match_score < 40:
            reasons.append(f"Location/work arrangement may not be ideal")
        
        return reasons
    
    def determine_career_growth(self, cv_experience: str, job_description: str) -> str:
        """Determine if job represents career growth"""
        job_desc_lower = job_description.lower()
        
        # Check for senior roles
        senior_indicators = ['senior', 'lead', 'principal', 'manager', 'director', 'head of']
        has_senior_role = any(indicator in job_desc_lower for indicator in senior_indicators)
        
        if cv_experience == 'junior' and has_senior_role:
            return "🚀 Career advancement opportunity"
        elif cv_experience == 'mid' and any(ind in job_desc_lower for ind in ['director', 'head of', 'vp']):
            return "📈 Leadership growth path"
        elif cv_experience == 'senior' and any(ind in job_desc_lower for ind in ['vp', 'chief', 'executive']):
            return "🎯 Executive level promotion"
        elif has_senior_role:
            return "➡️ Lateral move with growth potential"
        else:
            return "📊 Skill development focus"
    
    def calculate_priority_score(self, match_score: float, days_ago: int, company_reputation: str = "unknown") -> float:
        """Calculate overall priority score for job"""
        priority = match_score
        
        # Freshness bonus (jobs posted recently get higher priority)
        if days_ago <= 1:
            priority += 15
        elif days_ago <= 3:
            priority += 10
        elif days_ago <= 7:
            priority += 5
        elif days_ago > 30:
            priority -= 10
        
        # Company reputation bonus (if we had reputation data)
        # This could be enhanced with company size, glassdoor ratings, etc.
        
        return min(100.0, max(0.0, priority))
    
    def match_job_to_cv(self, job_data: Dict, cv_data: CVData, user_preferences: Dict = None) -> JobMatch:
        """Main method to match a job against CV data"""
        if user_preferences is None:
            user_preferences = {}
        
        # Extract job information
        job_id = str(job_data.get('Job ID', ''))
        company = job_data.get('Company', '')
        title = job_data.get('Vacancy Title', '')
        description = job_data.get('Job Description', '') or job_data.get('Skills', '')
        days_ago = job_data.get('Days_Ago', 30)
        
        # Extract skills from job
        job_skills = self.extract_job_skills(description)
        
        # Calculate component scores with detailed calculations
        skill_score, matched_skills, missing_skills, skill_calc = self.calculate_skill_match(cv_data.skills, job_skills)
        experience_score, job_exp_level, exp_calc = self.calculate_experience_match(cv_data.experience_level, cv_data.years_experience, description)
        industry_score = self.calculate_industry_match(cv_data.industries, description, company)
        location_score = self.calculate_location_match(job_data, user_preferences)
        
        # Calculate overall match score (weighted average)
        weights = {'skill': 0.4, 'experience': 0.25, 'industry': 0.2, 'location': 0.15}
        overall_score = (
            skill_score * weights['skill'] +
            experience_score * weights['experience'] +
            industry_score * weights['industry'] +
            location_score * weights['location']
        )
        
        # Create detailed weighted calculation explanation
        weighted_calc = f"Final Score Calculation (Weighted Average):\n"
        weighted_calc += f"→ Skills: {skill_score:.1f}% × {weights['skill']} = {skill_score * weights['skill']:.1f}\n"
        weighted_calc += f"→ Experience: {experience_score:.1f}% × {weights['experience']} = {experience_score * weights['experience']:.1f}\n"
        weighted_calc += f"→ Industry: {industry_score:.1f}% × {weights['industry']} = {industry_score * weights['industry']:.1f}\n"
        weighted_calc += f"→ Location: {location_score:.1f}% × {weights['location']} = {location_score * weights['location']:.1f}\n"
        weighted_calc += f"→ Total: {overall_score:.1f}%"
        
        # Create detailed calculation breakdown
        calculation_details = CalculationDetails(
            total_job_skills=len(job_skills),
            matched_skills_count=len(matched_skills),
            skill_calculation=skill_calc,
            cv_experience_level=cv_data.experience_level,
            job_experience_level=job_exp_level,
            experience_calculation=exp_calc,
            cv_industries=cv_data.industries,
            job_industry_keywords=[],  # Would be populated by industry analysis
            industry_calculation=f"Industry match: {industry_score:.1f}% (based on CV industries vs job/company keywords)",
            remote_preference=user_preferences.get('remote_preference', False),
            job_remote=job_data.get('Remote', False),
            visa_needed=user_preferences.get('needs_visa', False),
            job_visa=job_data.get('Visa Sponsorship or Relocation', False),
            location_calculation=f"Location match: {location_score:.1f}% (remote/visa preferences vs job requirements)",
            score_weights=weights,
            weighted_calculation=weighted_calc
        )
        
        # Create job match object
        job_match = JobMatch(
            job_id=job_id,
            company=company,
            title=title,
            match_score=overall_score,
            skill_match_score=skill_score,
            experience_match_score=experience_score,
            industry_match_score=industry_score,
            location_match_score=location_score,
            matched_skills=matched_skills[:10],  # Limit for display
            missing_skills=missing_skills[:5],   # Limit for display
            match_reasons=[],  # Will be filled below
            skill_gaps=missing_skills[:3],       # Top 3 gaps
            career_growth_indicator=self.determine_career_growth(cv_data.experience_level, description),
            recommendation="",  # Will be filled below
            priority_score=0,   # Will be calculated below
            calculation_details=calculation_details  # NEW: Detailed calculations
        )
        
        # Generate reasons and recommendations
        job_match.match_reasons = self.generate_match_reasons(job_match, cv_data)
        job_match.recommendation = self.generate_recommendation(job_match)
        job_match.priority_score = self.calculate_priority_score(overall_score, days_ago)
        
        return job_match
    
    def generate_recommendation(self, job_match: JobMatch) -> str:
        """Generate actionable recommendation"""
        if job_match.match_score >= 85:
            return "🎯 Excellent match - Apply immediately"
        elif job_match.match_score >= 70:
            return "✅ Strong match - Priority application"
        elif job_match.match_score >= 55:
            return "📝 Good match - Consider applying"
        elif job_match.match_score >= 40:
            return "🤔 Moderate match - Review skill gaps"
        else:
            return "❌ Poor match - Focus on skill development"
    
    def rank_jobs_for_cv(self, jobs_df: pd.DataFrame, cv_data: CVData, user_preferences: Dict = None) -> List[JobMatch]:
        """Rank all jobs for a given CV"""
        if jobs_df.empty:
            return []
        
        job_matches = []
        
        for idx, job_row in jobs_df.iterrows():
            job_dict = job_row.to_dict()
            match = self.match_job_to_cv(job_dict, cv_data, user_preferences)
            job_matches.append(match)
        
        # Sort by priority score (highest first)
        job_matches.sort(key=lambda x: x.priority_score, reverse=True)
        
        return job_matches

# Global recommendation engine instance
recommendation_engine = RecommendationEngine()

def get_job_recommendations(jobs_df: pd.DataFrame, cv_data: CVData, user_preferences: Dict = None) -> List[JobMatch]:
    """Convenience function for getting job recommendations"""
    return recommendation_engine.rank_jobs_for_cv(jobs_df, cv_data, user_preferences)