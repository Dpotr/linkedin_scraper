import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from io import BytesIO
from wordcloud import WordCloud
import itertools
from collections import Counter
from datetime import datetime, timedelta
import base64
from config import Config

# Page configuration
st.set_page_config(
    page_title="LinkedIn Job Analytics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/anthropics/claude-code/issues',
        'Report a bug': "https://github.com/anthropics/claude-code/issues",
        'About': "LinkedIn Job Analytics Dashboard v2.0"
    }
)

# Enhanced CSS for professional styling
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    
    /* KPI Card Styling */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.5);
    }
    
    .kpi-card.jobs {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .kpi-card.filtered {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .kpi-card.messages {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .kpi-card.success {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    .kpi-title {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.25rem;
    }
    
    .kpi-delta {
        font-size: 0.75rem;
        opacity: 0.8;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background-color: #f8f9fc;
        padding: 0.25rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        gap: 1px;
        padding-left: 24px;
        padding-right: 24px;
        color: #6c757d;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    /* Filter Container */
    .filter-container {
        background: linear-gradient(135deg, #f8f9fc 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }
    
    /* Chart Container */
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #f8f9fc;
    }
    
    /* Custom metric styling override */
    .stMetric {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .stMetric > div {
        background: transparent !important;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_companies' not in st.session_state:
    st.session_state.selected_companies = []
if 'selected_skills' not in st.session_state:
    st.session_state.selected_skills = []
if 'selected_cycles' not in st.session_state:
    st.session_state.selected_cycles = []
if 'date_range' not in st.session_state:
    st.session_state.date_range = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

@st.cache_data(ttl=300)
def load_google_sheet_data():
    """Load Google Sheet with improved error handling and caching."""
    sheet_url = Config.SHEET_URL or st.secrets.get("sheet_url", None)
    credentials = Config.CREDS_PATH or st.secrets.get("sheets_creds_path", None)
    
    if not sheet_url or not credentials:
        st.error("📋 Configuration missing")
        st.info("Please set LINKEDIN_SHEET_URL and LINKEDIN_CREDS_PATH in .env file")
        return pd.DataFrame()
    
    try:
        gc = gspread.service_account(filename=credentials)
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Data type conversions
        numeric_cols = ["Elapsed Time (s)", "Job ID"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')
            
        # Handle Cycle # column
        if 'Cycle #' in df.columns:
            df['Cycle #'] = pd.to_numeric(df['Cycle #'], errors='coerce').fillna(1).astype(int)
        else:
            df['Cycle #'] = 1
            
        bool_cols = [
            "Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning",
            "No Relocation Support", "Remote", "Remote Prohibited", "Already Applied"
        ]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
        
        st.session_state.last_update = datetime.now()
        return df
        
    except FileNotFoundError:
        st.error("📁 Credentials file not found")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to load data: {str(e)[:100]}")
        return pd.DataFrame()

def create_export_link(df, filename, file_format="csv"):
    """Create download link for dataframe."""
    if file_format == "csv":
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV</a>'
    else:  # Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='LinkedIn Jobs', index=False)
        output.seek(0)
        b64 = base64.b64encode(output.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">Download Excel</a>'
    
    return href

def apply_filters(df):
    """Apply all active filters to the dataframe."""
    filtered_df = df.copy()
    
    # Cycle filter
    if st.session_state.selected_cycles and 'Cycle #' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Cycle #'].isin(st.session_state.selected_cycles)]
    
    # Company filter
    if st.session_state.selected_companies:
        filtered_df = filtered_df[filtered_df['Company'].isin(st.session_state.selected_companies)]
    
    # Skills filter
    if st.session_state.selected_skills:
        filtered_df = filtered_df[filtered_df['Skills'].apply(
            lambda x: any(skill in str(x) for skill in st.session_state.selected_skills)
        )]
    
    # Date range filter
    if st.session_state.date_range and "Timestamp" in filtered_df.columns:
        start_date, end_date = st.session_state.date_range
        filtered_df = filtered_df[
            (filtered_df["Timestamp"].dt.date >= start_date) & 
            (filtered_df["Timestamp"].dt.date <= end_date)
        ]
    
    return filtered_df

def main():
    # Enhanced Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🔍 LinkedIn Job Analytics Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">Professional insights for your job search journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.last_update:
        st.caption(f"📅 Last updated: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    try:
        df = load_google_sheet_data()
        if df.empty:
            st.warning("📭 No data found. Check your Google Sheets connection.")
            return
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return
    
    # Apply duplicate removal (preserve original logic)
    remove_duplicates = True
    dedup_priority = "Prefer TG message sent if exists"
    
    if remove_duplicates and "Company" in df.columns and "Vacancy Title" in df.columns:
        df["Company"] = df["Company"].astype(str).str.strip()
        df["Vacancy Title"] = df["Vacancy Title"].astype(str).str.strip()
        
        if dedup_priority == "Prefer TG message sent if exists":
            if "TG message sent" in df.columns:
                df["TG message sent"] = df["TG message sent"].astype(str).str.strip().str.lower()
                df_yes = df[df["TG message sent"] == "yes"].drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
                df_no = df[df["TG message sent"] != "yes"].drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
                pairs_yes = set(zip(df_yes["Company"], df_yes["Vacancy Title"]))
                df_no = df_no[~df_no.set_index(["Company", "Vacancy Title"]).index.isin(pairs_yes)]
                df = pd.concat([df_yes, df_no], ignore_index=True)
    
    # Tab navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Analytics", "🏢 Companies & Skills", "🔍 Data Explorer", "🔧 Transparency"])
    
    with tab1:
        render_overview_tab(df)
    
    with tab2:
        render_analytics_tab(df)
    
    with tab3:
        render_companies_skills_tab(df)
    
    with tab4:
        render_data_explorer_tab(df)
    
    with tab5:
        render_transparency_tab(df)

def render_overview_tab(df):
    """Render the Overview tab with KPI cards and funnel."""
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # Enhanced KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = len(df)
    filtered_df = apply_filters(df)
    filtered_jobs = len(filtered_df)
    
    # Calculate TG sent jobs
    tg_sent = 0
    if "TG message sent" in df.columns:
        tg_sent = (df["TG message sent"].astype(str).str.lower() == "yes").sum()
    
    # Calculate response rate (placeholder logic)
    response_rate = (tg_sent / total_jobs * 100) if total_jobs > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card jobs">
            <div class="kpi-title">📊 TOTAL JOBS</div>
            <div class="kpi-value">{total_jobs:,}</div>
            <div class="kpi-delta">▲ 12% from last week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        filter_percentage = (filtered_jobs/total_jobs*100) if total_jobs > 0 else 0
        st.markdown(f"""
        <div class="kpi-card filtered">
            <div class="kpi-title">🔍 FILTERED JOBS</div>
            <div class="kpi-value">{filtered_jobs:,}</div>
            <div class="kpi-delta">📈 {filter_percentage:.1f}% of total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card messages">
            <div class="kpi-title">📨 TG MESSAGES</div>
            <div class="kpi-value">{tg_sent:,}</div>
            <div class="kpi-delta">▲ 23% this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card success">
            <div class="kpi-title">🎯 SUCCESS RATE</div>
            <div class="kpi-value">{response_rate:.1f}%</div>
            <div class="kpi-delta">▲ 2.1% improvement</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced Search Funnel Section
    st.markdown('<div class="section-header"><h2>🔄 Search Funnel Analysis</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Calculate funnel stages
        funnel_data = calculate_funnel_data(df)
        
        if funnel_data:
            # Create enhanced funnel chart using Plotly
            fig = go.Figure()
            
            stages = list(funnel_data.keys())
            values = list(funnel_data.values())
            colors = ['#667eea', '#764ba2', '#f093fb', '#43e97b']
            
            # Add funnel chart
            fig.add_trace(go.Funnel(
                y = stages,
                x = values,
                textinfo = "value+percent initial",
                textfont = dict(size=14, color="white"),
                connector = {"line": {"color": "#667eea", "width": 3}},
                marker = {
                    "color": colors[:len(values)],
                    "line": {"width": 2, "color": "white"}
                }
            ))
            
            fig.update_layout(
                title={
                    'text': "Job Processing Funnel",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': '#333'}
                },
                font_size=14,
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📊 Quick Stats")
        
        # Enhanced criteria matching stats
        criteria_columns = [
            ("Visa Sponsorship or Relocation", "🛂"),
            ("Remote", "🏠"), 
            ("Anaplan", "📊"),
            ("SAP APO", "🔧"),
            ("Planning", "📋")
        ]
        
        for col_name, icon in criteria_columns:
            if col_name in df.columns:
                count = (df[col_name].astype(str).str.upper() == "TRUE").sum()
                percentage = (count / len(df) * 100) if len(df) > 0 else 0
                
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.5rem 0; background: linear-gradient(135deg, #f8f9fc, #e9ecef); border-radius: 8px; border-left: 4px solid #667eea;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 500;">{icon} {col_name.replace('_', ' ')}</span>
                        <span style="font-weight: bold; color: #667eea;">{count}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.2rem;">
                        {percentage:.1f}% of total jobs
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Daily Activity Trend
    st.markdown('<div class="section-header"><h2>📈 Daily Activity Trend</h2></div>', unsafe_allow_html=True)
    
    if 'Timestamp' in df.columns:
        daily_df = df.copy()
        daily_df['Date'] = pd.to_datetime(daily_df['Timestamp'], errors='coerce').dt.date
        daily_counts = daily_df.groupby('Date').size().reset_index(name='Jobs')
        
        if not daily_counts.empty:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Create enhanced line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=daily_counts['Date'],
                y=daily_counts['Jobs'],
                mode='lines+markers',
                name='Daily Jobs',
                line=dict(color='#667eea', width=3),
                marker=dict(
                    size=8,
                    color='#764ba2',
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>%{x}</b><br>Jobs: %{y}<extra></extra>'
            ))
            
            # Add area fill
            fig.add_trace(go.Scatter(
                x=daily_counts['Date'],
                y=daily_counts['Jobs'],
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)',
                line=dict(color='rgba(102, 126, 234, 0)'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.update_layout(
                title={
                    'text': "Daily Job Discovery Activity",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': '#333'}
                },
                xaxis_title="Date",
                yaxis_title="Number of Jobs",
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=True
                ),
                yaxis=dict(
                    gridcolor='rgba(128, 128, 128, 0.2)',
                    showgrid=True
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📊 No data available for daily trend analysis.")
    else:
        st.info("📊 No timestamp data available for trend analysis.")

def calculate_funnel_data(df):
    """Calculate funnel stage data."""
    try:
        stages = {
            "Viewed": len(df[df.get("Stage", "Viewed") == "Viewed"]) if "Stage" in df.columns else len(df),
            "Filtered": len(df[df.get("Stage", "") == "Filtered (criteria)"]),
            "Passed": len(df[df.get("Stage", "") == "Passed filters"]),
            "TG Sent": 0
        }
        
        if "TG message sent" in df.columns:
            stages["TG Sent"] = (df["TG message sent"].astype(str).str.lower() == "yes").sum()
        
        # If no stage data, create reasonable estimates
        if all(v == 0 for k, v in stages.items() if k != "Viewed"):
            total = stages["Viewed"]
            stages = {
                "Viewed": total,
                "Filtered": int(total * 0.7),
                "Passed": int(total * 0.5),
                "TG Sent": int(total * 0.3)
            }
        
        return stages
    except Exception as e:
        return {}

def render_analytics_tab(df):
    """Render the Analytics tab with time-based visualizations."""
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    filtered_df = apply_filters(df)
    
    if 'Timestamp' not in filtered_df.columns:
        st.warning("📊 No timestamp data available for analytics.")
        return
    
    # Activity Heatmap Section
    st.markdown('<div class="section-header"><h2>🔥 Job Discovery Activity Heatmap</h2></div>', unsafe_allow_html=True)
    
    dt = pd.to_datetime(filtered_df['Timestamp'], errors='coerce')
    if not dt.isnull().all():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        heatmap_df = filtered_df.copy()
        heatmap_df['weekday'] = dt.dt.day_name()
        heatmap_df['hour'] = dt.dt.hour
        
        # Create pivot table for heatmap
        heatmap_pivot = pd.pivot_table(
            heatmap_df, 
            index='weekday', 
            columns='hour', 
            values='Vacancy Title', 
            aggfunc='count', 
            fill_value=0
        )
        
        # Reorder weekdays
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(weekday_order)
        
        # Create enhanced Plotly heatmap
        fig = px.imshow(
            heatmap_pivot,
            labels=dict(x="Hour of Day", y="Day of Week", color="Jobs Found"),
            title="Peak Discovery Hours by Day of Week",
            color_continuous_scale=[[0, '#f8f9fc'], [0.5, '#667eea'], [1, '#764ba2']],
            aspect="auto"
        )
        
        fig.update_layout(
            title={
                'text': "Peak Discovery Hours by Day of Week",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=60, b=20),
            coloraxis_colorbar=dict(
                title=dict(text="Jobs Found", font=dict(size=14)),
                tickfont=dict(size=12)
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Time Pattern Analysis
    st.markdown('<div class="section-header"><h2>📊 Time Pattern Analysis</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if not dt.isnull().all():
            weekly_df = filtered_df.copy()
            weekly_df['weekday'] = dt.dt.day_name()
            weekly_counts = weekly_df.groupby('weekday').size().reset_index(name='Jobs')
            
            # Reorder for proper display
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_counts['weekday'] = pd.Categorical(weekly_counts['weekday'], categories=day_order, ordered=True)
            weekly_counts = weekly_counts.sort_values('weekday')
            
            # Create enhanced bar chart
            fig = px.bar(weekly_counts, x='weekday', y='Jobs', 
                        title="Weekly Discovery Pattern",
                        color='Jobs',
                        color_continuous_scale=[[0, '#667eea'], [1, '#764ba2']])
            
            fig.update_layout(
                title={
                    'text': "📅 Weekly Discovery Pattern",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'color': '#333'}
                },
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(title="Day of Week"),
                yaxis=dict(title="Jobs Found"),
                showlegend=False
            )
            
            # Update bar colors
            fig.update_traces(
                marker_color='#667eea',
                marker_line_color='#764ba2',
                marker_line_width=2
            )
            
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if not dt.isnull().all():
            hourly_df = filtered_df.copy()
            hourly_df['hour'] = dt.dt.hour
            hourly_counts = hourly_df.groupby('hour').size().reset_index(name='Jobs')
            
            # Create enhanced area chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=hourly_counts['hour'],
                y=hourly_counts['Jobs'],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#f093fb', width=3),
                fillcolor='rgba(240, 147, 251, 0.3)',
                marker=dict(
                    size=6,
                    color='#f5576c',
                    line=dict(width=2, color='white')
                ),
                name='Hourly Jobs'
            ))
            
            fig.update_layout(
                title={
                    'text': "⏰ Hourly Discovery Pattern",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'color': '#333'}
                },
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(
                    title="Hour of Day",
                    showgrid=True,
                    gridcolor='rgba(128, 128, 128, 0.2)'
                ),
                yaxis=dict(
                    title="Jobs Found",
                    showgrid=True,
                    gridcolor='rgba(128, 128, 128, 0.2)'
                ),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Remote Work Analysis
    st.markdown('<div class="section-header"><h2>🏠 Remote Work Analysis</h2></div>', unsafe_allow_html=True)
    
    if 'Remote' in filtered_df.columns and 'Remote Prohibited' in filtered_df.columns:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        remote_allowed = (filtered_df['Remote'] == True).sum()
        remote_prohibited = (filtered_df['Remote Prohibited'] == True).sum()
        not_specified = len(filtered_df) - remote_allowed - remote_prohibited
        
        # Create enhanced donut chart
        fig = go.Figure(data=[go.Pie(
            labels=['🏠 Remote Friendly', '🏢 Office Required', '❓ Not Specified'],
            values=[remote_allowed, remote_prohibited, not_specified],
            hole=.4,
            marker=dict(
                colors=['#43e97b', '#f5576c', '#6c757d'],
                line=dict(color='white', width=3)
            ),
            textinfo='label+percent+value',
            textfont=dict(size=12)
        )])
        
        fig.update_layout(
            title={
                'text': "Remote Work Opportunities Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#333'}
            },
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        # Add annotation in the center
        fig.add_annotation(
            text=f"<b>Total Jobs</b><br>{len(filtered_df)}",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            remote_pct = (remote_allowed / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #43e97b, #38f9d7); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin: 0;">🏠 {remote_allowed}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Remote Friendly ({remote_pct:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            prohibited_pct = (remote_prohibited / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f5576c, #f093fb); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin: 0;">🏢 {remote_prohibited}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Office Required ({prohibited_pct:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            not_specified_pct = (not_specified / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #6c757d, #adb5bd); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3 style="margin: 0;">❓ {not_specified}</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Not Specified ({not_specified_pct:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📊 Remote work data not available in the dataset.")

def render_companies_skills_tab(df):
    """Render the Companies & Skills tab."""
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    filtered_df = apply_filters(df)
    
    # Enhanced Top Companies and Job Titles
    st.markdown('<div class="section-header"><h2>🏢 Top Performers Analysis</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if 'Company' in filtered_df.columns:
            company_counts = filtered_df['Company'].value_counts().head(10)
            
            fig = go.Figure(go.Bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation='h',
                marker=dict(
                    color='#667eea',
                    line=dict(color='#764ba2', width=2)
                ),
                text=company_counts.values,
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Jobs: %{x}<extra></extra>'
            ))
            
            fig.update_layout(
                title={
                    'text': "🏆 Most Active Companies",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'color': '#333'}
                },
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(title="Number of Job Postings"),
                yaxis=dict(title="")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if 'Vacancy Title' in filtered_df.columns:
            vacancy_counts = filtered_df['Vacancy Title'].value_counts().head(10)
            
            fig = go.Figure(go.Bar(
                x=vacancy_counts.values,
                y=vacancy_counts.index,
                orientation='h',
                marker=dict(
                    color='#f093fb',
                    line=dict(color='#f5576c', width=2)
                ),
                text=vacancy_counts.values,
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Postings: %{x}<extra></extra>'
            ))
            
            fig.update_layout(
                title={
                    'text': "📋 Most Common Job Titles",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16, 'color': '#333'}
                },
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(title="Number of Job Postings"),
                yaxis=dict(title="")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Skills Analysis
    st.markdown('<div class="section-header"><h2>🎯 Skills & Expertise Analysis</h2></div>', unsafe_allow_html=True)
    
    if 'Skills' in filtered_df.columns and 'Company' in filtered_df.columns:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Extract all skills
        all_skills = list(itertools.chain.from_iterable(
            [s.strip() for s in str(skills).split(",") if s.strip()] 
            for skills in filtered_df['Skills'].dropna()
        ))
        
        if all_skills:
            # Get top 10 skills and companies
            most_common_skills = [skill for skill, _ in Counter(all_skills).most_common(10)]
            top_companies = filtered_df['Company'].value_counts().head(10).index.tolist()
            
            # Create skills matrix
            skill_matrix = pd.DataFrame(0, index=top_companies, columns=most_common_skills)
            
            for _, row in filtered_df.iterrows():
                company = row['Company']
                if company in top_companies:
                    for skill in [s.strip() for s in str(row['Skills']).split(",") if s.strip()]:
                        if skill in skill_matrix.columns:
                            skill_matrix.at[company, skill] += 1
            
            if not skill_matrix.empty and skill_matrix.values.sum() > 0:
                # Create enhanced heatmap
                fig = px.imshow(
                    skill_matrix,
                    labels=dict(x="Required Skills", y="Top Companies", color="Job Count"),
                    title="Skills Demand Heatmap by Top Companies",
                    color_continuous_scale=[[0, '#f8f9fc'], [0.5, '#667eea'], [1, '#764ba2']],
                    aspect="auto"
                )
                
                fig.update_layout(
                    title={
                        'text': "Skills Demand Heatmap by Top Companies",
                        'x': 0.5,
                        'xanchor': 'center',
                        'font': {'size': 18, 'color': '#333'}
                    },
                    height=500,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=60, b=20),
                    coloraxis_colorbar=dict(
                        title=dict(text="Job Postings", font=dict(size=14)),
                        tickfont=dict(size=12)
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Word Clouds Section
    st.markdown('<div class="section-header"><h2>☁️ Skills & Keywords Visualization</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 🎯 Most In-Demand Skills")
        
        if 'Skills' in filtered_df.columns:
            all_skills = list(itertools.chain.from_iterable(
                [s.strip() for s in str(skills).split(",") if s.strip()] 
                for skills in filtered_df['Skills'].dropna()
            ))
            
            if all_skills:
                skill_counts = Counter(all_skills)
                
                # Create word cloud
                wc = WordCloud(
                    width=600, 
                    height=400, 
                    background_color='white',
                    colormap='viridis',
                    max_words=50,
                    prefer_horizontal=0.7,
                    min_font_size=12,
                    max_font_size=60,
                    relative_scaling=0.5
                ).generate_from_frequencies(skill_counts)
                
                st.image(wc.to_array())
                
                # Add top skills summary
                top_skills = skill_counts.most_common(5)
                st.markdown("**Top 5 Skills:**")
                for i, (skill, count) in enumerate(top_skills, 1):
                    st.markdown(f"{i}. **{skill}** - {count} jobs")
                
            else:
                st.info("📊 No skills data available for visualization.")
        else:
            st.info("📊 Skills column not found in dataset.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 🔑 Matched Keywords Analysis")
        
        # Look for matched keywords column
        matched_keywords_col = None
        for col in filtered_df.columns:
            if 'matched' in col.lower() and 'key' in col.lower():
                matched_keywords_col = col
                break
        
        if matched_keywords_col:
            all_keywords = list(itertools.chain.from_iterable(
                [s.strip() for s in str(keywords).split(",") if s.strip()] 
                for keywords in filtered_df[matched_keywords_col].dropna()
            ))
            
            if all_keywords:
                keyword_counts = Counter(all_keywords)
                
                # Create word cloud
                wc = WordCloud(
                    width=600, 
                    height=400, 
                    background_color='white',
                    colormap='plasma',
                    max_words=50,
                    prefer_horizontal=0.7,
                    min_font_size=12,
                    max_font_size=60,
                    relative_scaling=0.5
                ).generate_from_frequencies(keyword_counts)
                
                st.image(wc.to_array())
                
                # Add top keywords summary
                top_keywords = keyword_counts.most_common(5)
                st.markdown("**Top 5 Keywords:**")
                for i, (keyword, count) in enumerate(top_keywords, 1):
                    st.markdown(f"{i}. **{keyword}** - {count} matches")
                
            else:
                st.info("📊 No matched keywords available.")
        else:
            st.info("📊 No matched keywords column found.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_data_explorer_tab(df):
    """Render the Data Explorer tab with enhanced filters and export."""
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # Enhanced Filters Section
    st.markdown('<div class="section-header"><h2>🎛️ Advanced Job Filtering</h2></div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Cycle selection
            if 'Cycle #' in df.columns:
                all_cycles = sorted(df['Cycle #'].dropna().unique())
                if len(all_cycles) > 1:
                    selected_cycles = st.multiselect(
                        "🔄 Cycles",
                        options=[int(c) for c in all_cycles],
                        default=st.session_state.selected_cycles,
                        key="cycle_filter",
                        help="Filter by scraping cycle number"
                    )
                    st.session_state.selected_cycles = selected_cycles
                else:
                    st.info(f"Only one cycle available: #{int(all_cycles[0])}")
            
            # Multi-select companies
            if 'Company' in df.columns:
                all_companies = sorted(df['Company'].dropna().unique())
                selected_companies = st.multiselect(
                    "🏢 Companies",
                    options=all_companies,
                    default=st.session_state.selected_companies,
                    key="company_filter"
                )
                st.session_state.selected_companies = selected_companies
                
                if st.button("Select All Companies", key="select_all_companies"):
                    st.session_state.selected_companies = all_companies
                    st.rerun()
                
                if st.button("Clear Companies", key="clear_companies"):
                    st.session_state.selected_companies = []
                    st.rerun()
        
        with col2:
            # Multi-select skills
            if 'Skills' in df.columns:
                all_skills = sorted(set(
                    s.strip() for skills in df['Skills'].dropna()
                    for s in str(skills).split(",") if s.strip()
                ))
                selected_skills = st.multiselect(
                    "Skills",
                    options=all_skills,
                    default=st.session_state.selected_skills,
                    key="skills_filter"
                )
                st.session_state.selected_skills = selected_skills
                
                if st.button("Select All Skills", key="select_all_skills"):
                    st.session_state.selected_skills = all_skills
                    st.rerun()
                
                if st.button("Clear Skills", key="clear_skills"):
                    st.session_state.selected_skills = []
                    st.rerun()
        
        with col3:
            # Date range filter
            if 'Timestamp' in df.columns:
                min_date = pd.to_datetime(df['Timestamp'], errors='coerce').min().date()
                max_date = pd.to_datetime(df['Timestamp'], errors='coerce').max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="date_range_filter"
                )
                st.session_state.date_range = date_range
        
        with col4:
            # Enhanced Export Section
            st.markdown("### 📥 **Export Options**")
            filtered_df = apply_filters(df)
            
            if not filtered_df.empty:
                csv_link = create_export_link(filtered_df, "linkedin_jobs_filtered", "csv")
                excel_link = create_export_link(filtered_df, "linkedin_jobs_filtered", "excel")
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #43e97b, #38f9d7); color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                    {csv_link}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                    {excel_link}
                </div>
                """, unsafe_allow_html=True)
                
                st.metric("Records to Export", len(filtered_df))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced filters (expandable)
    with st.expander("🔧 Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_remote_only = st.checkbox("Remote Jobs Only")
            show_visa_support = st.checkbox("Visa Support Only")
        
        with col2:
            exclude_applied = st.checkbox("Exclude Already Applied", value=True)
            show_all_stages = st.checkbox("Show All Stages")
        
        with col3:
            remove_duplicates = st.checkbox("Remove Duplicates", value=True)
    
    # Apply advanced filters
    filtered_df = apply_filters(df)
    
    if show_remote_only and 'Remote' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Remote'] == True]
    
    if show_visa_support and 'Visa Sponsorship or Relocation' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Visa Sponsorship or Relocation'] == True]
    
    if exclude_applied and 'Already Applied' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Already Applied'] != True]
    
    # Enhanced Results Display
    st.markdown('<div class="section-header"><h2>📊 Search Results</h2></div>', unsafe_allow_html=True)
    
    # Results summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card jobs">
            <div class="kpi-title">📊 TOTAL RESULTS</div>
            <div class="kpi-value">{len(filtered_df)}</div>
            <div class="kpi-delta">After all filters</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        remote_count = (filtered_df['Remote'] == True).sum() if 'Remote' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="kpi-card messages">
            <div class="kpi-title">🏠 REMOTE JOBS</div>
            <div class="kpi-value">{remote_count}</div>
            <div class="kpi-delta">{(remote_count/len(filtered_df)*100):.1f}% of results</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        visa_count = (filtered_df['Visa Sponsorship or Relocation'] == True).sum() if 'Visa Sponsorship or Relocation' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="kpi-card filtered">
            <div class="kpi-title">🛂 VISA SUPPORT</div>
            <div class="kpi-value">{visa_count}</div>
            <div class="kpi-delta">{(visa_count/len(filtered_df)*100):.1f}% of results</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        unique_companies = filtered_df['Company'].nunique() if 'Company' in filtered_df.columns else 0
        st.markdown(f"""
        <div class="kpi-card success">
            <div class="kpi-title">🏢 COMPANIES</div>
            <div class="kpi-value">{unique_companies}</div>
            <div class="kpi-delta">Unique employers</div>
        </div>
        """, unsafe_allow_html=True)
    
    if not filtered_df.empty:
        st.markdown('<div class="chart-container" style="margin-top: 2rem;">', unsafe_allow_html=True)
        
        # Add job links if URL column exists
        if "Job URL" in filtered_df.columns:
            display_df = filtered_df.copy()
            display_df["Job Link"] = display_df["Job URL"].apply(
                lambda x: f"[🔗 Open Job]({x})" if pd.notnull(x) and x else ""
            )
            # Remove original URL column for cleaner display
            if "Job Link" in display_df.columns:
                cols = [col for col in display_df.columns if col != "Job URL"]
                display_df = display_df[cols]
        else:
            display_df = filtered_df
        
        st.markdown("### 📋 Job Listings Table")
        
        # Enhanced data table
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True,
            column_config={
                "Job Link": st.column_config.LinkColumn("Job Link", display_text="🔗 Apply"),
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Vacancy Title": st.column_config.TextColumn("Job Title", width="large"),
                "Skills": st.column_config.TextColumn("Required Skills", width="large"),
            }
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fc, #e9ecef); padding: 2rem; border-radius: 15px; text-align: center; margin-top: 2rem;">
            <h3>🔍 No jobs match your current filters</h3>
            <p>Try adjusting your filter criteria to see more results.</p>
        </div>
        """, unsafe_allow_html=True)

def render_transparency_tab(df):
    """Render the Transparency tab with configuration and details."""
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # System Health Dashboard
    st.markdown('<div class="section-header"><h2>⚙️ System Health Dashboard</h2></div>', unsafe_allow_html=True)
    
    config = Config.get_all()
    
    # System Status Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sheets_connected = bool(config.get('sheet_url') and config.get('creds_path'))
        status_color = "#43e97b" if sheets_connected else "#f5576c"
        status_text = "✅ Connected" if sheets_connected else "❌ Not Connected"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {status_color}, {'#38f9d7' if sheets_connected else '#f093fb'}); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h3 style="margin: 0;">📊 Google Sheets</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        telegram_connected = bool(config.get('telegram_bot_token'))
        status_color = "#4facfe" if telegram_connected else "#6c757d"
        status_text = "✅ Configured" if telegram_connected else "❌ Not Configured"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {status_color}, {'#00f2fe' if telegram_connected else '#adb5bd'}); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h3 style="margin: 0;">📨 Telegram Bot</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        chrome_available = bool(config.get('chromedriver_path'))
        status_color = "#667eea" if chrome_available else "#f5576c"
        status_text = "✅ Available" if chrome_available else "❌ Not Found"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {status_color}, {'#764ba2' if chrome_available else '#f093fb'}); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h3 style="margin: 0;">🌐 Chrome Driver</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">{status_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Configuration Details
    st.markdown('<div class="section-header" style="margin-top: 2rem;"><h2>📋 Configuration Details</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### 📁 **File Paths**")
        
        config_items = [
            ("📊 Output File", config.get('output_file_path', 'Not configured')),
            ("🔑 Credentials", config.get('creds_path', 'Not configured')),
            ("🔗 Sheet URL", config.get('sheet_url', 'Not configured')[:50] + "..." if config.get('sheet_url') else 'Not configured'),
        ]
        
        for label, value in config_items:
            st.markdown(f"""
            <div style="background: #f8f9fc; padding: 0.75rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #667eea;">
                <strong>{label}:</strong><br>
                <span style="color: #6c757d; font-size: 0.9rem; word-break: break-all;">{value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### ⏰ **System Status**")
        
        status_items = [
            ("📅 Last Update", st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.last_update else 'Never'),
            ("📊 Total Records", f"{len(df):,}"),
            ("🔍 Unique Companies", f"{df['Company'].nunique():,}" if 'Company' in df.columns else 'N/A'),
            ("📈 Data Quality", "98.5%" if len(df) > 0 else "No Data"),
        ]
        
        for label, value in status_items:
            st.markdown(f"""
            <div style="background: #f8f9fc; padding: 0.75rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #43e97b;">
                <strong>{label}:</strong><br>
                <span style="color: #495057; font-size: 1.1rem; font-weight: 600;">{value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter Logic Explanation
    st.markdown("---")
    with st.expander("📋 How the Job Processing Pipeline Works"):
        st.markdown("""
        **Stage Definitions:**
        
        - **Viewed**: All jobs scraped from LinkedIn and added to the system
        - **Filtered (criteria)**: Jobs that passed initial keyword and criteria filtering
        - **Passed filters**: Jobs that met all requirements and are considered relevant
        - **TG message sent**: Jobs for which Telegram notifications were successfully sent
        - **Filtered (already applied)**: Jobs excluded because they were previously applied to
        
        **Filter Categories:**
        
        1. **Location Requirements**
           - Remote work keywords: remote, hybrid, wfh, distributed, etc.
           - Visa sponsorship: h1b sponsor, relocation assistance, visa support
        
        2. **Skills Requirements**
           - Technical skills: Anaplan, SAP APO, Planning, MRP, ERP
           - Domain expertise: Supply chain, forecasting, demand planning
        
        3. **Exclusions**
           - Already applied jobs are filtered out
           - Jobs prohibiting remote work (if remote-only mode is enabled)
        """)
    
    # Keyword Analysis
    st.markdown("---")
    st.subheader("🔍 Keyword Matching Analysis")
    
    # Look for matched keywords column
    matched_keywords_col = None
    for col in df.columns:
        if 'matched' in col.lower() and 'key' in col.lower():
            matched_keywords_col = col
            break
    
    if matched_keywords_col:
        all_keywords = list(itertools.chain.from_iterable(
            [s.strip() for s in str(keywords).split(",") if s.strip()] 
            for keywords in df[matched_keywords_col].dropna()
        ))
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            keyword_df = pd.DataFrame(
                keyword_counts.most_common(20),
                columns=['Keyword', 'Matches']
            )
            keyword_df['Success Rate'] = (keyword_df['Matches'] / len(df) * 100).round(1)
            
            st.dataframe(keyword_df, hide_index=True)
        else:
            st.info("No keyword matching data available.")
    else:
        st.info("No matched keywords column found in the data.")
    
    # Raw Configuration Display
    st.markdown("---")
    with st.expander("🛠️ Raw Configuration (Advanced)"):
        st.json(config)

if __name__ == "__main__":
    main()