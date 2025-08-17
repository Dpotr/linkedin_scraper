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
    # === ФИКС: приведение типов для всех потенциально проблемных колонок ===
    for col in ["Elapsed Time (s)", "Job ID"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')
    bool_cols = [
        "Visa Sponsorship or Relocation",
        "Anaplan",
        "SAP APO",
        "Planning",
        "No Relocation Support",
        "Remote",
        "Remote Prohibited",
        "Already Applied"
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
    # === END FIX ===

    # --- Фильтры для интерактивной аналитики с кнопками Select/Deselect All ---
    st.sidebar.header("Фильтры для аналитики")
    all_companies = sorted(str(c).strip() for c in df['Company'].dropna().unique())
    all_skills = sorted(set(
        s.strip() for skills in df['Skills'].dropna()
        for s in str(skills).split(",") if s.strip()
    ))

    # Фильтр по компаниям (selectbox)
    company_filter = st.sidebar.selectbox("Фильтр по компаниям", options=["Все компании"] + all_companies, index=0, key='company_filter_select')
    if company_filter == "Все компании":
        selected_companies = all_companies
    else:
        selected_companies = [company_filter]

    # Фильтр по навыкам (selectbox)
    skill_filter = st.sidebar.selectbox("Фильтр по навыкам (Skills)", options=["Все навыки"] + all_skills, index=0, key='skill_filter_select')
    if skill_filter == "Все навыки":
        selected_skills = all_skills
    else:
        selected_skills = [skill_filter]

    # --- Галочка: удалять дубликаты вакансий ---
    remove_duplicates = st.sidebar.checkbox("Remove vacancies duplicates (by Company + Vacancy Title)", value=True)
    dedup_priority = None
    if remove_duplicates:
        dedup_priority = st.sidebar.selectbox(
            "If duplicates: which to keep?",
            ["First event (any stage)", "Prefer TG message sent if exists"],
            index=1
        )

    filtered_df = df[
        df['Company'].isin(selected_companies)
    ]
    if selected_skills:
        filtered_df = filtered_df[filtered_df['Skills'].apply(lambda x: any(skill in str(x) for skill in selected_skills))]

    if remove_duplicates and "Company" in filtered_df.columns and "Vacancy Title" in filtered_df.columns:
        # Привести Company и Vacancy Title к строке и убрать пробелы для строгой фильтрации
        filtered_df["Company"] = filtered_df["Company"].astype(str).str.strip()
        filtered_df["Vacancy Title"] = filtered_df["Vacancy Title"].astype(str).str.strip()
        if dedup_priority == "First event (any stage)":
            filtered_df = filtered_df.drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
        elif dedup_priority == "Prefer TG message sent if exists":
            if "TG message sent" in filtered_df.columns:
                filtered_df["TG message sent"] = filtered_df["TG message sent"].astype(str).str.strip().str.lower()
                df_yes = filtered_df[filtered_df["TG message sent"] == "yes"].drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
                df_no = filtered_df[filtered_df["TG message sent"] != "yes"].drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")
                pairs_yes = set(zip(df_yes["Company"], df_yes["Vacancy Title"]))
                df_no = df_no[~df_no.set_index(["Company", "Vacancy Title"]).index.isin(pairs_yes)]
                filtered_df = pd.concat([df_yes, df_no], ignore_index=True)
            else:
                filtered_df = filtered_df.drop_duplicates(subset=["Company", "Vacancy Title"], keep="first")

    # --- LIVE ПРОГРЕСС ---
    st.sidebar.markdown("---")
    st.sidebar.header("Live-прогресс поиска")
    total_jobs = len(filtered_df)
    filtered_jobs = len(filtered_df)
    st.sidebar.metric("Всего вакансий", total_jobs)
    st.sidebar.metric("Вакансий после фильтров", filtered_jobs)
    st.sidebar.progress(filtered_jobs / total_jobs if total_jobs else 0)

    # --- FUNNEL: REAL PROGRESS FROM MAIN SHEET ---
    st.subheader("Search Funnel (All Stages)")
    funnel_counts = {}
    try:
        import gspread
        import matplotlib.pyplot as plt
        gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS)
        sh = gc.open_by_url(GOOGLE_SHEETS_URL)
        ws = sh.sheet1
        log_df = pd.DataFrame(ws.get_all_records())
        # === ФИКС: приведение типов для всех потенциально проблемных колонок ===
        for col in ["Elapsed Time (s)", "Job ID"]:
            if col in log_df.columns:
                log_df[col] = pd.to_numeric(log_df[col], errors='coerce')
        if "Timestamp" in log_df.columns:
            log_df["Timestamp"] = pd.to_datetime(log_df["Timestamp"], errors='coerce')
        for col in bool_cols:
            if col in log_df.columns:
                log_df[col] = log_df[col].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
        # === END FIX ===
        stages = [
            "Viewed",
            "Filtered (criteria)",
            "Passed filters",
            "TG message sent",
            "Filtered (already applied)"
        ]
        for stage in stages:
            if stage == "TG message sent":
                # Для этого этапа считаем по колонке TG message sent == 'yes', если колонка есть
                if "TG message sent" in log_df.columns:
                    funnel_counts[stage] = (log_df["TG message sent"].astype(str).str.lower() == "yes").sum()
                else:
                    funnel_counts[stage] = 0
            elif stage == "Passed filters":
                # Passed filters: только те, у кого TG message sent != 'yes'
                if "TG message sent" in log_df.columns:
                    mask_passed = (log_df["Stage"] == stage)
                    mask_not_sent = (log_df["TG message sent"].astype(str).str.lower() != "yes")
                    funnel_counts[stage] = (mask_passed & mask_not_sent).sum()
                else:
                    funnel_counts[stage] = (log_df["Stage"] == stage).sum()
            else:
                funnel_counts[stage] = (log_df["Stage"] == stage).sum()
        percent_stages = ["Viewed", "Filtered (criteria)", "Passed filters", "TG message sent"]
        values = [funnel_counts[stage] for stage in percent_stages]
        labels = []
        prev = None
        for i, stage in enumerate(percent_stages):
            val = values[i]
            if prev is not None and prev > 0:
                percent = val / prev * 100
                labels.append(f"{stage} ({val}, {percent:.1f}%)")
            else:
                labels.append(f"{stage} ({val})")
            prev = val
        if funnel_counts["Filtered (already applied)"] > 0:
            labels.append(f"Filtered (already applied) ({funnel_counts['Filtered (already applied)']})")
            values.append(funnel_counts["Filtered (already applied)"])
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.barh(range(len(values)), values, color=plt.cm.viridis([i / len(values) for i in range(len(values))]))
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel("Количество")
        ax.set_title("Воронка по этапам")
        for i, bar in enumerate(bars):
            ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height()/2, str(values[i]), va='center')
        st.pyplot(fig)

        # --- Детальная механика этапов воронки под спойлером ---
        with st.expander("Как считается каждый этап воронки? (кликните для подробностей)"):
            st.markdown("""
            **Механика расчёта этапов воронки:**

            - **Viewed** — Вакансия просмотрена парсером и добавлена в лог. На этом этапе фиксируются все ключевые слова и флаги (релокация, удалёнка, Remote Prohibited и др.).
            - **Filtered (criteria)** — Вакансия прошла первичную фильтрацию по основным критериям:
                - Ключевые слова (Visa/Relocation, Anaplan, SAP APO, Planning и др.)
                - Поддержка релокации/визы
                - Удалёнка (Remote/Remote Prohibited)
                - Нет поддержки релокации (No Relocation Support)
            - **Filtered (already applied)** — Вакансия отфильтрована, т.к. ранее уже была подана заявка (Already Applied = True).
            - **Passed filters** — Вакансия прошла все фильтры и признана релевантной (по ключевым словам и критериям). Такие вакансии попадают в итоговый список для дальнейших действий.
            - **TG message sent** — Для релевантной вакансии отправлено уведомление в Telegram.

            **Почему может быть разное количество на этапах?**
            - На каждом этапе вакансии могут отсекаться по разным причинам (например, не совпали ключевые слова, нет релокации, уже подавались и т.д.).
            - Все этапы логируются по отдельности: одна и та же вакансия может появиться на нескольких этапах, но в аналитике учитывается только по текущему этапу.
            - Подробная логика фильтрации описана в README.md (раздел "Логика парсинга и мэтчинга вакансий").
            """)
    except Exception as e:
        st.info(f"Unable to load funnel from main sheet: {e}")

    # --- BAR CHART: Совпадения по критериям поиска ---
    st.subheader("Совпадения по критериям поиска")
    criteria_columns = [
        "Visa Sponsorship or Relocation",
        "Anaplan",
        "SAP APO",
        "Planning",
        "No Relocation Support",
        "Remote",
        "Remote Prohibited",
        "Already Applied"
    ]
    present_criteria = [col for col in criteria_columns if col in log_df.columns]
    if present_criteria:
        matches = {col: (log_df[col].astype(str).str.upper() == "TRUE").sum() for col in present_criteria}
        import matplotlib.pyplot as plt
        fig_crit, ax_crit = plt.subplots(figsize=(8, 4))
        ax_crit.bar(matches.keys(), matches.values(), color=plt.cm.Paired.colors)
        ax_crit.set_ylabel("Количество совпадений")
        ax_crit.set_xlabel("Критерии поиска")
        ax_crit.set_title("Вакансии, соответствующие критериям поиска")
        ax_crit.set_xticklabels(matches.keys(), rotation=30, ha='right')
        for i, v in enumerate(matches.values()):
            ax_crit.text(i, v + max(matches.values()) * 0.01, str(v), ha='center', va='bottom')
        st.pyplot(fig_crit)
    else:
        st.info("В Google Sheets нет колонок с критериями поиска для построения графика.")

    # --- TAG CLOUD: matched key words ---
    st.subheader("Облако тегов: совпавшие ключевые слова (Matched key words)")
    matched_keywords_col = None
    for col in log_df.columns:
        if col.lower().replace('_', ' ').startswith('matched key'):
            matched_keywords_col = col
            break
    if matched_keywords_col:
        import itertools
        from collections import Counter
        all_keywords = list(itertools.chain.from_iterable(
            [s.strip() for s in str(keywords).split(",") if s.strip()] for keywords in log_df[matched_keywords_col].dropna()
        ))
        keyword_counts = Counter(all_keywords)
        if keyword_counts:
            from wordcloud import WordCloud
            fig_kw, ax_kw = plt.subplots(figsize=(12, 5))
            wc_kw = WordCloud(width=900, height=400, background_color='white', colormap='plasma',
                              max_words=100, prefer_horizontal=1.0, collocations=False).generate_from_frequencies(keyword_counts)
            ax_kw.imshow(wc_kw, interpolation='bilinear')
            ax_kw.axis('off')
            st.pyplot(fig_kw)
        else:
            st.info("Нет данных для построения облака совпавших ключевых слов.")
    else:
        st.info("В Google Sheets нет колонки с совпавшими ключевыми словами для облака тегов.")

    # --- BAR CHART: Remote Prohibited ---
    st.subheader("Вакансии с запретом удалёнки (Remote Prohibited)")
    if 'Remote Prohibited' in log_df.columns:
        st.write(f"Всего вакансий с запретом на удалёнку: {(log_df['Remote Prohibited']==True).sum()}")
        st.bar_chart(log_df['Remote Prohibited'].value_counts())
    else:
        st.info("Нет данных по запрету удалёнки.")

    # --- Filter main data for all analytics by Stage ---
    filtered_df = filtered_df[filtered_df.get("Stage", "Passed filters") == "Passed filters"] if "Stage" in filtered_df.columns else filtered_df

    # --- Heatmap активности по времени ---
    st.subheader("Активность по времени (день/15-минутный интервал)")
    if 'Timestamp' in filtered_df.columns:
        dt = pd.to_datetime(filtered_df['Timestamp'], errors='coerce')
        if not dt.isnull().all():
            filtered_df['weekday'] = dt.dt.day_name()
            # Добавляем 15-минутные интервалы
            filtered_df['quarter'] = dt.dt.hour.astype(str).str.zfill(2) + ':' + (dt.dt.minute // 15 * 15).astype(str).str.zfill(2)
            heatmap_time = pd.pivot_table(filtered_df, index='weekday', columns='quarter', values='Vacancy Title', aggfunc='count', fill_value=0)
            # Сортировка дней недели и времени
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_time = heatmap_time.reindex(weekday_order)
            import seaborn as sns
            fig_time, ax_time = plt.subplots(figsize=(16, 5))
            sns.heatmap(heatmap_time, cmap='YlOrRd', ax=ax_time)
            ax_time.set_title('Heatmap: Активность по дням и 15-минутным интервалам')
            st.pyplot(fig_time)
        else:
            st.info("Нет данных для построения heatmap активности.")
    else:
        st.info("Нет данных для построения heatmap активности.")

    # --- Топ компаний и вакансий ---
    st.subheader("Топ компаний и вакансий")
    if 'Vacancy Title' in filtered_df.columns:
        st.write("**Топ-10 вакансий:**")
        st.dataframe(filtered_df['Vacancy Title'].value_counts().head(10).reset_index().rename(columns={'index': 'Вакансия', 'Vacancy Title': 'Частота'}), hide_index=True)

    # --- Heatmap: топ навыков по компаниям (skills) ---
    st.subheader("Heatmap: топ навыков по компаниям (skills)")
    if 'Skills' in filtered_df.columns and 'Company' in filtered_df.columns:
        from collections import Counter
        import itertools
        all_skills = list(itertools.chain.from_iterable(
            [s.strip() for s in str(skills).split(",") if s.strip()] for skills in filtered_df['Skills'].dropna()
        ))
        most_common_skills = [w for w, _ in Counter(all_skills).most_common(10)]
        skill_matrix = pd.DataFrame(0, index=filtered_df['Company'].unique(), columns=most_common_skills)
        for _, row in filtered_df.iterrows():
            company = row['Company']
            for skill in [s.strip() for s in str(row['Skills']).split(",") if s.strip()]:
                if skill in skill_matrix.columns:
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

    # --- User-friendly таблица ---
    if "Job URL" in filtered_df.columns:
        filtered_df["Job Link"] = filtered_df["Job URL"].apply(lambda x: f"[Открыть вакансию]({x})" if pd.notnull(x) and x else "")
        display_cols = [col for col in filtered_df.columns if col not in ["Job URL"]]
        if "Job Link" not in display_cols:
            display_cols.append("Job Link")
        st.dataframe(filtered_df[display_cols], use_container_width=True, height=420, hide_index=True)
    else:
        st.dataframe(filtered_df, use_container_width=True, height=420, hide_index=True)

    # --- График по дням ---
    if 'Timestamp' in filtered_df.columns:
        filtered_df['Date'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce').dt.date
        daily_counts = filtered_df.groupby('Date').size()
        if not daily_counts.empty:
            st.line_chart(daily_counts)
        else:
            st.info("Нет данных для построения графика по дням.")
    else:
        st.info("Нет данных для построения графика по дням.")

except Exception as e:
    st.error(f"Ошибка при чтении Google Sheets: {e}")
