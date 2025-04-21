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

    # --- Галочка: удалять дубликаты вакансий ---
    remove_duplicates = st.sidebar.checkbox("Remove vacancies duplicates (by Company + Vacancy Title)", value=True)
    dedup_priority = None
    if remove_duplicates:
        dedup_priority = st.sidebar.selectbox(
            "If duplicates: which to keep?",
            ["First event (any stage)", "Prefer TG message sent if exists"]
        )

    filtered_df = df[
        df['Company'].isin(company_filter)
        & df['Vacancy Title'].isin(vacancy_filter)
    ]
    if skill_filter:
        filtered_df = filtered_df[filtered_df['Skills'].apply(lambda x: any(skill in str(x) for skill in skill_filter))]

    if remove_duplicates and "Company" in filtered_df.columns and "Vacancy Title" in filtered_df.columns:
        if dedup_priority == "First event (any stage)":
            filtered_df = filtered_df.drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
        elif dedup_priority == "Prefer TG message sent if exists":
            if "TG message sent" in filtered_df.columns:
                # Привести к строке и сравнивать строго с 'yes'
                filtered_df["_tg_sent_sort"] = filtered_df["TG message sent"].astype(str).str.strip().str.lower() == "yes"
                filtered_df = (
                    filtered_df.sort_values(
                        by=["Company", "Vacancy Title", "_tg_sent_sort"],
                        ascending=[True, True, False]
                    )
                    .drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
                    .drop(columns=["_tg_sent_sort"])
                )
            else:
                filtered_df = filtered_df.drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")

    # --- LIVE ПРОГРЕСС ---
    st.sidebar.markdown("---")
    st.sidebar.header("Live-прогресс поиска")
    total_jobs = len(df)
    filtered_jobs = len(filtered_df)
    st.sidebar.metric("Всего вакансий", total_jobs)
    st.sidebar.metric("Вакансий после фильтров", filtered_jobs)
    st.sidebar.progress(filtered_jobs / total_jobs if total_jobs else 0)

    # --- Воронка поиска (Funnel) ---
    st.subheader("Воронка поиска (Funnel)")
    funnel_data = {
        "Найдено": [len(df)],
        "После фильтров": [len(filtered_df)],
        # Можно добавить этапы, если есть логи отправки в Telegram/Sheets
    }
    funnel_df = pd.DataFrame(funnel_data)
    st.bar_chart(funnel_df.T)

    # --- FUNNEL: REAL PROGRESS FROM MAIN SHEET ---
    import gspread
    st.subheader("Search Funnel (All Stages)")
    funnel_counts = {}
    try:
        gc = gspread.service_account(filename=st.secrets["google_sheets_credentials"])
        sh = gc.open_by_url(st.secrets["google_sheets_url"])
        ws = sh.sheet1
        log_df = pd.DataFrame(ws.get_all_records())
        for stage in ["Viewed", "Filtered (already applied)", "Filtered (criteria)", "Passed filters"]:
            funnel_counts[stage] = (log_df["Stage"] == stage).sum()
        funnel_df = pd.DataFrame(list(funnel_counts.items()), columns=["Stage", "Count"])
        st.bar_chart(funnel_df.set_index("Stage"))
    except Exception as e:
        st.info(f"Unable to load funnel from main sheet: {e}")

    # --- Filter main data for all analytics by Stage ---
    filtered_df = df[df.get("Stage", "Passed filters") == "Passed filters"] if "Stage" in df.columns else df

    # --- Heatmap активности по времени ---
    st.subheader("Активность по времени (день/час)")
    if 'Timestamp' in df.columns:
        dt = pd.to_datetime(df['Timestamp'], errors='coerce')
        if not dt.isnull().all():
            df['weekday'] = dt.dt.day_name()
            df['hour'] = dt.dt.hour
            heatmap_time = pd.pivot_table(df, index='weekday', columns='hour', values='Vacancy Title', aggfunc='count', fill_value=0)
            import seaborn as sns
            fig_time, ax_time = plt.subplots(figsize=(12, 4))
            sns.heatmap(heatmap_time, cmap='YlOrRd', ax=ax_time)
            ax_time.set_title('Heatmap: Активность по дням и часам')
            st.pyplot(fig_time)
        else:
            st.info("Нет данных для построения heatmap активности.")
    else:
        st.info("Нет данных для построения heatmap активности.")

    # --- Топ компаний и вакансий ---
    st.subheader("Топ компаний и вакансий")
    if 'Company' in filtered_df.columns:
        st.write("**Топ-10 компаний:**")
        st.dataframe(filtered_df['Company'].value_counts().head(10).reset_index().rename(columns={'index': 'Компания', 'Company': 'Вакансий'}), hide_index=True)
    if 'Vacancy Title' in filtered_df.columns:
        st.write("**Топ-10 вакансий:**")
        st.dataframe(filtered_df['Vacancy Title'].value_counts().head(10).reset_index().rename(columns={'index': 'Вакансия', 'Vacancy Title': 'Частота'}), hide_index=True)

    # --- Отсеивание по фильтрам ---
    st.subheader("Статистика по фильтрам")
    filter_stats = {}
    for col in ['Relocation', 'Remote', 'Experience', 'Skills']:
        if col in df.columns:
            total = df[col].notnull().sum()
            filtered = filtered_df[col].notnull().sum()
            filter_stats[col] = [total-filtered, filtered]
    if filter_stats:
        filter_stats_df = pd.DataFrame(filter_stats, index=['Отсеяно', 'Пропущено'])
        st.bar_chart(filter_stats_df)
    else:
        st.info("Нет данных для статистики по фильтрам.")

    # --- Мониторинг ошибок ---
    st.subheader("Мониторинг ошибок")
    if 'Error' in df.columns:
        st.write("Последние ошибки:")
        st.dataframe(df[['Timestamp', 'Error']].dropna().tail(10), hide_index=True)
        st.write(f"Всего ошибок: {df['Error'].notnull().sum()}")
    else:
        st.info("Нет данных по ошибкам.")

    # --- География вакансий (если есть) ---
    if 'Location' in df.columns:
        st.subheader("География вакансий")
        geo_counts = df['Location'].value_counts().head(20).reset_index().rename(columns={'index': 'Место', 'Location': 'Вакансий'})
        st.dataframe(geo_counts, hide_index=True)
        # Можно добавить map, если есть координаты

    # --- Сравнение с предыдущими периодами ---
    st.subheader("Динамика по сравнению с прошлым периодом")
    if 'Date' in filtered_df.columns:
        last_week = filtered_df[filtered_df['Date'] >= (pd.Timestamp.now().date() - pd.Timedelta(days=7))]
        prev_week = filtered_df[(filtered_df['Date'] < (pd.Timestamp.now().date() - pd.Timedelta(days=7))) & (filtered_df['Date'] >= (pd.Timestamp.now().date() - pd.Timedelta(days=14)))]
        st.metric("Вакансий за последнюю неделю", len(last_week), delta=len(last_week)-len(prev_week))

    # --- User-friendly таблица ---
    st.dataframe(filtered_df, use_container_width=True, height=420, hide_index=True)

    # --- Pie chart по компаниям ---
    if 'Company' in filtered_df.columns and not filtered_df['Company'].isnull().all():
        company_counts = filtered_df['Company'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(company_counts, labels=company_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.subheader("Распределение вакансий по компаниям")
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
    else:
        st.info("Нет данных для построения графика по дням.")

    # --- Heatmap: топ навыков по компаниям (skills) ---
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
