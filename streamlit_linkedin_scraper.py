import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from wordcloud import WordCloud
import itertools
from collections import Counter

st.set_page_config(page_title="LinkedIn Job Scraper", layout="centered")
st.title("LinkedIn Job Scraper (Streamlit)")

# --- Настройки Google Sheets ---
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/173Zb-CkHxamDlQ3q7aFD-1Ay3nk6W7hrEq2aD6y4VJ4/edit?usp=sharing"
GOOGLE_SHEETS_CREDENTIALS = "C:/Users/potre/OneDrive/LinkedIn_Automation/google_sheets_credentials.json"

def read_google_sheet(sheet_url=GOOGLE_SHEETS_URL, credentials=GOOGLE_SHEETS_CREDENTIALS):
    gc = gspread.service_account(filename=credentials)
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.sheet1
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- UI настройки (спойлер) ---
with st.expander("Настройки (только для справки)", expanded=False):
    st.markdown("""
    **Параметры текущей конфигурации:**
    - **Google Sheets URL:** `{}`
    - **Google Sheets Credentials:** `{}`
    - **Файл Excel:** `{}`
    - **Telegram Chat ID:** `{}`
    - **Telegram Bot Token:** `{}`
    - **ChromeDriver Path:** `{}`
    - **Chrome Profile Path:** `{}`
    - **Chrome Binary Location:** `{}`
    - **Ключевые слова (Visa/Relocation):** `{}`
    - **Ключевые слова (Anaplan):** `{}`
    - **Ключевые слова (SAP):** `{}`
    - **Ключевые слова (Planning):** `{}`
    - **No Relocation:** `{}`
    - **Remote:** `{}`
    """.format(
        GOOGLE_SHEETS_URL,
        GOOGLE_SHEETS_CREDENTIALS,
        "C:/Users/potre/OneDrive/LinkedIn_Automation/companies_usa_remote.xlsx",
        "[скрыто]",
        "[скрыто]",
        "C:/selenium/chromedriver.exe",
        "C:/Users/potre/SeleniumProfileNew",
        "C:/Program Files/Google/Chrome Beta/Application/chrome.exe",
        "...",
        "...",
        "...",
        "...",
        "...",
        "..."
    ))

# --- Основная таблица ---
st.markdown("---")
st.header("Актуальные результаты из Google Sheets")
try:
    df = read_google_sheet()

    # --- Фильтры для интерактивной аналитики с кнопками Select/Deselect All ---
    st.sidebar.header("Фильтры для аналитики")
    all_companies = sorted(df['Company'].dropna().unique())
    all_vacancies = sorted(df['Vacancy Title'].dropna().unique())
    all_skills = sorted(set(itertools.chain.from_iterable([s.strip() for s in str(skills).split(",") if s.strip()] for skills in df['Skills'].dropna())))

    # Кнопки Select/Deselect All для компаний
    col1, col2 = st.sidebar.columns([1,1])
    if 'company_filter' not in st.session_state:
        st.session_state['company_filter'] = all_companies
    if col1.button("Select All Companies"):
        st.session_state['company_filter'] = all_companies
    if col2.button("Deselect All Companies"):
        st.session_state['company_filter'] = []
    company_filter = st.sidebar.multiselect("Фильтр по компаниям", options=all_companies, default=st.session_state['company_filter'], key='company_filter')

    # Кнопки Select/Deselect All для вакансий
    col3, col4 = st.sidebar.columns([1,1])
    if 'vacancy_filter' not in st.session_state:
        st.session_state['vacancy_filter'] = all_vacancies
    if col3.button("Select All Vacancies"):
        st.session_state['vacancy_filter'] = all_vacancies
    if col4.button("Deselect All Vacancies"):
        st.session_state['vacancy_filter'] = []
    vacancy_filter = st.sidebar.multiselect("Фильтр по вакансиям", options=all_vacancies, default=st.session_state['vacancy_filter'], key='vacancy_filter')

    # Кнопки Select/Deselect All для навыков
    col5, col6 = st.sidebar.columns([1,1])
    if 'skill_filter' not in st.session_state:
        st.session_state['skill_filter'] = []
    if col5.button("Select All Skills"):
        st.session_state['skill_filter'] = all_skills
    if col6.button("Deselect All Skills"):
        st.session_state['skill_filter'] = []
    skill_filter = st.sidebar.multiselect("Фильтр по навыкам (Skills)", options=all_skills, default=st.session_state['skill_filter'], key='skill_filter')

    filtered_df = df[
        df['Company'].isin(company_filter)
        & df['Vacancy Title'].isin(vacancy_filter)
    ]
    if skill_filter:
        filtered_df = filtered_df[filtered_df['Skills'].apply(lambda x: any(skill in str(x) for skill in skill_filter))]

    # --- User-friendly таблица ---
    st.dataframe(filtered_df, use_container_width=True, height=420, hide_index=True)
    # --- Bar chart по критериям ---
    st.subheader("Bar chart по критериям (True/False)")
    bool_cols = [col for col in filtered_df.columns if filtered_df[col].dtype == 'bool']
    if bool_cols and filtered_df[bool_cols].sum().sum() > 0:
        st.bar_chart(filtered_df[bool_cols].sum())
    else:
        st.info("Нет данных для построения bar chart по критериям.")
    # --- Pie chart по компаниям ---
    st.subheader("Распределение вакансий по компаниям (Pie chart)")
    if 'Company' in filtered_df.columns and not filtered_df['Company'].isnull().all():
        company_counts = filtered_df['Company'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(company_counts, labels=company_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)
    else:
        st.info("Нет данных для построения pie chart по компаниям.")
    # --- График по времени (количество вакансий по дням) ---
    st.subheader("Вакансии по дням (Time Series)")
    if 'Timestamp' in filtered_df.columns:
        filtered_df['Date'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce').dt.date
        daily_counts = filtered_df.groupby('Date').size()
        if not daily_counts.empty:
            st.line_chart(daily_counts)
        else:
            st.info("Нет данных для построения графика по дням.")
    # --- Heatmap по критериям и компаниям ---
    st.subheader("Heatmap: компании vs критерии")
    if bool_cols and 'Company' in filtered_df.columns and not filtered_df['Company'].isnull().all():
        heatmap_data = filtered_df.groupby('Company')[bool_cols].sum()
        if not heatmap_data.empty and heatmap_data.values.sum() > 0:
            fig2, ax2 = plt.subplots(figsize=(8, max(3, len(heatmap_data)//2)))
            sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='Blues', ax=ax2)
            st.pyplot(fig2)
        else:
            st.info("Нет данных для построения heatmap по критериям и компаниям.")
    else:
        st.info("Нет данных для построения heatmap по критериям и компаниям.")
    # --- Heatmap топ навыков: что ищут компании (skills) ---
    st.subheader("Heatmap: топ навыков по компаниям (skills)")
    if 'Skills' in filtered_df.columns and 'Company' in filtered_df.columns:
        from collections import Counter
        import itertools
        # Собираем все skills (разделены запятыми)
        all_skills = list(itertools.chain.from_iterable(
            [s.strip() for s in str(skills).split(",") if s.strip()] for skills in filtered_df['Skills'].dropna()
        ))
        most_common_skills = [w for w, _ in Counter(all_skills).most_common(10)]
        skill_matrix = pd.DataFrame(0, index=filtered_df['Company'].unique(), columns=most_common_skills)
        for _, row in filtered_df.iterrows():
            company = row['Company']
            skills = [s.strip() for s in str(row.get('Skills', '')).split(",") if s.strip()]
            for skill in most_common_skills:
                if skill in skills:
                    skill_matrix.at[company, skill] += 1
        if not skill_matrix.empty and skill_matrix.values.sum() > 0:
            fig3, ax3 = plt.subplots(figsize=(10, max(3, len(skill_matrix)//2)))
            sns.heatmap(skill_matrix, annot=True, fmt='d', cmap='YlGnBu', ax=ax3)
            st.pyplot(fig3)
        else:
            st.info("Нет данных для построения heatmap по навыкам.")
    else:
        st.info("Нет данных для построения heatmap по навыкам.")
    # --- Heatmap топ навыков: что ищут компании, которые НЕ попали (пример: нет совпадения по критериям) ---
    st.subheader("Heatmap: топ навыков (компании без совпадения по критериям)")
    if 'Skills' in filtered_df.columns and 'Company' in filtered_df.columns and bool_cols:
        # Компании, у которых нет True ни по одному критерию
        companies_no_match = filtered_df.groupby('Company')[bool_cols].sum().sum(axis=1)
        companies_no_match = companies_no_match[companies_no_match == 0].index.tolist()
        if companies_no_match:
            all_skills = list(itertools.chain.from_iterable(
                [s.strip() for s in str(row.get('Skills', '')).split(",") if s.strip()]
                for _, row in filtered_df[filtered_df['Company'].isin(companies_no_match)].iterrows()
            ))
            most_common_skills = [w for w, _ in Counter(all_skills).most_common(10)]
            skill_matrix = pd.DataFrame(0, index=companies_no_match, columns=most_common_skills)
            for _, row in filtered_df[filtered_df['Company'].isin(companies_no_match)].iterrows():
                company = row['Company']
                skills = [s.strip() for s in str(row.get('Skills', '')).split(",") if s.strip()]
                for skill in most_common_skills:
                    if skill in skills:
                        skill_matrix.at[company, skill] += 1
            if not skill_matrix.empty and skill_matrix.values.sum() > 0:
                fig4, ax4 = plt.subplots(figsize=(10, max(3, len(skill_matrix)//2)))
                sns.heatmap(skill_matrix, annot=True, fmt='d', cmap='Oranges', ax=ax4)
                st.pyplot(fig4)
            else:
                st.info("Нет данных для построения heatmap по навыкам для компаний без совпадений.")
        else:
            st.info("Нет компаний без совпадений по критериям.")
    else:
        st.info("Нет данных для построения heatmap по навыкам для компаний без совпадений.")
    # --- Tag Cloud по навыкам (Skills) ---
    st.subheader("Облако навыков (Skills Tag Cloud)")
    if 'Skills' in filtered_df.columns:
        import itertools
        from collections import Counter
        from wordcloud import WordCloud
        all_skills = list(itertools.chain.from_iterable(
            [s.strip() for s in str(skills).split(",") if s.strip()] for skills in filtered_df['Skills'].dropna()
        ))
        skill_counts = Counter(all_skills)
        if skill_counts:
            wc = WordCloud(width=900, height=400, background_color='white', colormap='viridis',
                           max_words=100, prefer_horizontal=1.0, collocations=False).generate_from_frequencies(skill_counts)
            fig_wc, ax_wc = plt.subplots(figsize=(12, 5))
            ax_wc.imshow(wc, interpolation='bilinear')
            ax_wc.axis('off')
            st.pyplot(fig_wc)
        else:
            st.info("Нет данных для построения облака навыков.")
    else:
        st.info("Нет данных для построения облака навыков.")
except Exception as e:
    st.error(f"Ошибка при чтении Google Sheets: {e}")
