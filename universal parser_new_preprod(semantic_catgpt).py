#!/usr/bin/env python3
import logging
import time
import io
import threading
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import pandas as pd
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langdetect import detect, LangDetectException
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import os  # для shutdown системы

# ================================
# Настройка логирования
# ================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ================================
# Глобальные переменные для семантической модели
# ================================
SEMANTIC_MODEL = None
SEMANTIC_QUERY_EMBEDDINGS = {}

def initialize_semantic_model():
    global SEMANTIC_MODEL, SEMANTIC_QUERY_EMBEDDINGS
    try:
        from sentence_transformers import SentenceTransformer, util
        # Загружаем модель all-MiniLM-L12-v2 без параметра force_download и указываем каталог кеша
        SEMANTIC_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2', cache_folder='C:\\temp\\huggingface_cache')
        semantic_queries = {
            "Remote": "This job offers remote work",
            "Visa Sponsorship": "This job provides visa sponsorship or relocation assistance",
            "Anaplan": "This job requires Anaplan skills",
            "SAP": "This job involves SAP supply chain management",
            "Planning": "This job is related to supply chain planning"
        }
        SEMANTIC_QUERY_EMBEDDINGS = {cat: SEMANTIC_MODEL.encode(text, convert_to_tensor=True) for cat, text in semantic_queries.items()}
        logging.info("Семантическая модель успешно загружена глобально.")
    except Exception as e:
        logging.error("Ошибка загрузки семантической модели: " + str(e))

# Инициализация семантической модели до создания GUI и запуска потоков
initialize_semantic_model()

# ================================
# Значения по умолчанию
# ================================
DEFAULT_TELEGRAM_BOT_TOKEN = "7690052120:AAHewK4ztdFw7y-iCApCmRMkCwz9inLLkfI"
DEFAULT_TELEGRAM_CHAT_ID = "1908191"
DEFAULT_CHROMEDRIVER_PATH = r"C:\selenium\chromedriver.exe"
DEFAULT_CHROME_PROFILE_PATH = r"C:\Users\potre\SeleniumProfileNew"
DEFAULT_CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
DEFAULT_OUTPUT_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies_usa_remote.xlsx"
DEFAULT_SEARCH_COUNTRY = "United States"
DEFAULT_KEYWORD = "remote job"

# Ключевые слова для базового поиска
NO_RELOCATION_REQUIREMENTS = [
    "no relocation support", "we do not provide relocation", "no visa sponsorship",
    "relocation not provided", "visa sponsorship unavailable", "relocation assistance not offered",
    "visa sponsorship not included", "no relocation assistance", "we are unable to sponsor visas",
    "visa sponsorship not possible", "local applicants only", "we cannot provide relocation"
]
REMOTE_REQUIREMENTS = [
    "remote", "work from home", "fully remote", "telecommute", "telecommuting", "remote work", "remote position"
]
KEYWORDS_VISA = [
    "we provide relocation", "relocation assistance", "relocation support", "we sponsor visas",
    "visa sponsorship available", "work visa sponsorship", "relocation package", "we support relocation",
    "visa sponsorship provided", "relocation offered", "visa and relocation assistance",
    "international relocation", "relocation and visa support"
]
KEYWORDS_ANAPLAN = [
    "anaplan", "anaplan model builder", "anaplan planning", "anaplan developer", "anaplan consultant",
    "anaplan architect", "anaplan implementation", "anaplan solution", "anaplan support", "anaplan admin",
    "connected planning", "anaplan integration"
]
KEYWORDS_SAP = [
    "sap snp", "sap apo", "sap pp/ds", "sap scm", "sap supply planning", "sap advanced planning and optimization",
    "sap production planning", "sap demand planning", "sap distribution planning", "sap key user",
    "sap supply chain management"
]
KEYWORDS_PLANNING = [
    "supply planning", "distribution requirements planning", "inventory planning", "production planning",
    "demand planning", "material requirements planning", "capacity planning", "supply chain planning",
    "logistics planning", "operations planning", "master production scheduling", "forecasting", "s&op",
    "sales and operations planning", "warehouse planning", "network planning", "procurement planning"
]
ALL_KEYWORDS = (
    KEYWORDS_VISA
    + KEYWORDS_ANAPLAN
    + KEYWORDS_SAP
    + KEYWORDS_PLANNING
    + NO_RELOCATION_REQUIREMENTS
    + REMOTE_REQUIREMENTS
)

# Порог для семантического сходства
SEMANTIC_THRESHOLD = 0.65

# Глобальные переменные для результатов
results = []
total_vacancies_checked = 0

# ================================
# Функция отправки сообщений в Telegram
# ================================
def send_telegram_message(bot_token, chat_id, message, images=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            logging.info("Сообщение отправлено в Telegram.")
        else:
            logging.error(f"Ошибка при отправке сообщения: {resp.text}")
    except Exception as e:
        logging.error(f"Ошибка подключения к Telegram: {e}")
    
    if images:
        for img in images:
            url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            files = {"photo": img}
            data = {"chat_id": chat_id}
            try:
                resp_img = requests.post(url_photo, files=files, data=data)
                if resp_img.status_code == 200:
                    logging.info("Изображение отправлено в Telegram.")
                else:
                    logging.error(f"Ошибка при отправке изображения: {resp_img.text}")
            except Exception as e:
                logging.error(f"Ошибка подключения к Telegram при отправке изображения: {e}")

# ================================
# Работа с Excel
# ================================
def get_excel_summary(file_path, running_time_minutes):
    try:
        wb = load_workbook(file_path)
        sheet = wb.active
        summary = []
        summary.append(f"Running time, min: {running_time_minutes:.2f}")
        summary.append(f"Checked companies: {sheet['S1'].value} {sheet['T1'].value}")
        return "\n".join(summary)
    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из Excel: {e}")
        return ""

def save_results_to_file_with_calculations(results, output_file, elapsed_time):
    try:
        # Преобразуем семантические оценки в строку, если они присутствуют
        for row in results:
            if "Semantic Scores" in row and isinstance(row["Semantic Scores"], dict):
                row["Semantic Scores"] = ", ".join([f"{k}: {v}" for k, v in row["Semantic Scores"].items()])
        df = pd.DataFrame(results)
        true_count = sum(
            any(value is True for key, value in row.items() if key not in ["Elapsed Time (s)", "Job URL"])
            for row in results
        )
        ratio = true_count / len(df) if len(df) > 0 else 0
        processed_companies = len(df)
        avg_time_per_company = elapsed_time / processed_companies if processed_companies > 0 else 0

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
            wb = writer.book
            sheet = writer.sheets["Results"]
            sheet["S1"] = "Checked companies:"
            sheet["T1"] = processed_companies

        logging.info(f"Результаты сохранены в файл: {output_file}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении результатов в Excel: {e}")

# ================================
# Построение аналитики
# ================================
def create_p_chart(results):
    if len(results) < 2:
        return None
    df = pd.DataFrame(results)
    try:
        df["Elapsed Time (s)"] = df["Elapsed Time (s)"].astype(float)
        df["Time Difference (s)"] = df["Elapsed Time (s)"].diff()
        time_diffs = df["Time Difference (s)"][1:].tail(50)
        avg_time_diff = time_diffs.mean()
        plt.figure(figsize=(10, 5))
        plt.plot(time_diffs.index, time_diffs, marker='o', linestyle='-', color='b', label='Time Difference (s)')
        plt.axhline(y=avg_time_diff, color='r', linestyle='--', label=f'Avg Diff ({avg_time_diff:.2f}s)')
        plt.fill_between(time_diffs.index, avg_time_diff, time_diffs,
                         where=(time_diffs > avg_time_diff), color='red', alpha=0.1)
        plt.fill_between(time_diffs.index, avg_time_diff, time_diffs,
                         where=(time_diffs < avg_time_diff), color='green', alpha=0.1)
        plt.xlabel('Listing Index')
        plt.ylabel('Time Diff (s)')
        plt.title('P-Chart: Time Difference (Last 50)')
        plt.legend()
        plt.grid(True)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        logging.error(f"Ошибка при построении p-chart: {e}")
        return None

def create_bar_chart(results):
    if not results:
        return None
    df = pd.DataFrame(results)
    criteria = ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "No Relocation Support", "Remote"]
    try:
        counts = {crit: df[crit].sum() if crit in df.columns else 0 for crit in criteria}
        plt.figure(figsize=(8, 5))
        plt.bar(counts.keys(), counts.values(), color='skyblue')
        plt.xlabel('Criteria')
        plt.ylabel('Count')
        plt.title('Distribution of Criteria in Processed Jobs')
        num_labels = len(counts)
        fontsize = max(6, 14 - num_labels)
        plt.xticks(rotation=45, fontsize=fontsize)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        logging.error(f"Ошибка при построении бар-чарта: {e}")
        return None

# ================================
# Функция прокрутки
# ================================
def scroll_until_loaded(driver, pause_time=1, max_consecutive=3):
    global total_vacancies_checked
    consecutive = 0
    prev_count = 0
    body = driver.find_element(By.TAG_NAME, "body")
    # Принудительный PAGE_DOWN на первой странице
    body.send_keys(Keys.PAGE_DOWN)
    time.sleep(pause_time)
    while consecutive < max_consecutive:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(pause_time)
        current_count = len(driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable"))
        logging.debug(f"PAGE_DOWN -> вакансий сейчас: {current_count}")
        if current_count <= prev_count:
            consecutive += 1
        else:
            consecutive = 0
            prev_count = current_count

# ================================
# Обработка вакансий на странице с семантическим поиском
# ================================
def parse_current_page(driver, wait, start_time, config, semantic_model=None, semantic_query_embeddings=None):
    global results, total_vacancies_checked
    try:
        scroll_until_loaded(driver, pause_time=1, max_consecutive=3)
        job_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        logging.info(f"Найдено вакансий на странице: {len(job_listings)}")
        total_vacancies_checked += len(job_listings)
        matching_jobs = []

        for i, job in enumerate(job_listings, start=1):
            try:
                action = ActionChains(driver)
                # Получаем данные вакансии
                try:
                    job_company_name = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle span").text.strip()
                except Exception as e:
                    logging.debug(f"Не удалось получить имя компании: {e}")
                    job_company_name = "Unknown Company"
                try:
                    job_title = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title span").text.strip()
                except Exception as e:
                    try:
                        job_title = job.find_element(By.CSS_SELECTOR, ".job-card-list__title").text.strip()
                    except Exception as e2:
                        logging.debug(f"Не удалось получить заголовок вакансии: {e2}")
                        job_title = "Title not found"

                logging.info(f"Обработка вакансии №{i}: '{job_title}' / {job_company_name}")
                action.move_to_element(job).click().perform()

                desc_element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-box__html-content"))
                )
                desc_text = ""
                for _ in range(10):
                    time.sleep(0.8)
                    tmp = desc_element.get_attribute("innerText").strip()
                    if len(tmp) > 50:
                        desc_text = tmp.lower()
                        break
                if not desc_text:
                    logging.info("Описание не успело прогрузиться, пропускаем.")
                    continue

                try:
                    detected_language = detect(desc_text)
                except LangDetectException:
                    detected_language = "unknown"

                job_url = driver.current_url

                # Базовый поиск по ключевым словам
                remote_found = any(x in desc_text for x in REMOTE_REQUIREMENTS)
                visa_or_relocation = any(x in desc_text for x in KEYWORDS_VISA)
                anaplan_found = any(x in desc_text for x in KEYWORDS_ANAPLAN)
                sap_apo_found = any(x in desc_text for x in KEYWORDS_SAP)
                planning_found = any(x in desc_text for x in KEYWORDS_PLANNING)
                already_applied = any(x in desc_text for x in ["applied", "see application", "you have already applied", "already submitted", "previously applied"])

                # Семантический поиск и расчёт скоринга
                semantic_flags = {}
                semantic_flags_binary = {}
                semantic_scores_percent = {}
                matched_semantic = []
                if semantic_model and semantic_query_embeddings:
                    # Вычисляем эмбеддинг для описания вакансии
                    desc_embedding = semantic_model.encode(desc_text, convert_to_tensor=True)
                    from sentence_transformers import util
                    for cat, query_emb in semantic_query_embeddings.items():
                        cosine_score = util.cos_sim(desc_embedding, query_emb)
                        semantic_flags[cat] = cosine_score.item()
                    semantic_flags_binary = {cat: (score >= SEMANTIC_THRESHOLD) for cat, score in semantic_flags.items()}
                    semantic_scores_percent = {cat: f"{score*100:.2f}%" for cat, score in semantic_flags.items()}
                    matched_semantic = [f"{cat} ({semantic_scores_percent[cat]})" for cat, flag in semantic_flags_binary.items() if flag]
                    # Логируем в терминале скоринг для каждой вакансии
                    logging.info(f"Semantic scores for vacancy '{job_title}': {semantic_scores_percent}")

                # Объединённое условие: учитывать как текстовый поиск, так и семантический
                if not already_applied and (
                    (remote_found or visa_or_relocation or semantic_flags_binary.get("Remote", False) or semantic_flags_binary.get("Visa Sponsorship", False))
                    and (anaplan_found or sap_apo_found or planning_found or semantic_flags_binary.get("Anaplan", False) or semantic_flags_binary.get("SAP", False) or semantic_flags_binary.get("Planning", False))
                ):
                    matched_keywords = [kw for kw in ALL_KEYWORDS if kw in desc_text]
                    # Формируем строку со всеми семантическими оценками в процентах для вывода
                    semantic_scores_str = ", ".join([f"{cat}: {score}" for cat, score in semantic_scores_percent.items()]) if semantic_scores_percent else "N/A"
                    current_result = {
                        "Company": job_company_name,
                        "Vacancy Title": job_title,
                        "Visa Sponsorship or Relocation": visa_or_relocation or semantic_flags_binary.get("Visa Sponsorship", False),
                        "Anaplan": anaplan_found or semantic_flags_binary.get("Anaplan", False),
                        "SAP APO": sap_apo_found or semantic_flags_binary.get("SAP", False),
                        "Planning": planning_found or semantic_flags_binary.get("Planning", False),
                        "No Relocation Support": any(x in desc_text for x in NO_RELOCATION_REQUIREMENTS),
                        "Remote": remote_found or semantic_flags_binary.get("Remote", False),
                        "Already Applied": already_applied,
                        "Job URL": job_url,
                        "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                        "Semantic Scores": semantic_scores_percent  # сохранение в виде словаря (будет преобразовано в строку для Excel)
                    }
                    running_minutes = (time.perf_counter() - start_time) / 60
                    summary = get_excel_summary(config["output_file_path"], running_minutes)
                    message_text = (
                        f"🔔 Найдена вакансия по ключевому слову <b>{config['keyword']}</b>\n"
                        f"Компания: <b>{job_company_name}</b>\n"
                        f"Вакансия: <b>{job_title}</b>\n\n"
                        f"Matched key words: {', '.join(matched_keywords)}\n"
                        f"Semantic scores: {semantic_scores_str}\n"
                        f"Язык описания: {detected_language.upper()}\n\n"
                        f"Ссылка на вакансию: <a href='{job_url}'>{job_url}</a>\n\n"
                        f"Всего проверено вакансий: {total_vacancies_checked}\n"
                        + summary
                    )
                    send_telegram_message(config["telegram_bot_token"], config["telegram_chat_id"], message_text)
                    matching_jobs.append(current_result)
            except Exception as e:
                logging.error(f"Ошибка при обработке вакансии №{i}: {e}")
                continue

        results.extend(matching_jobs)
    except Exception as e:
        logging.error(f"Ошибка при разборе текущей страницы: {e}")

# ================================
# Основная функция запуска парсера
# ================================
def run_scraper(config):
    global results, total_vacancies_checked
    results = []
    total_vacancies_checked = 0
    start_time = time.perf_counter()

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={config['chrome_profile_path']}")
    # options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-webrtc")
    options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
    options.add_argument("--disable-udp")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--v=0")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if config.get("chrome_binary_location"):
        options.binary_location = config["chrome_binary_location"]

    service = Service(config["chromedriver_path"])
    try:
        driver = uc.Chrome(options=options, service=service)
    except Exception as e:
        logging.error(f"Ошибка запуска браузера: {e}")
        return

    driver.get("https://www.linkedin.com/login")
    logging.info("Ожидаем ручной вход в систему...")
    try:
        WebDriverWait(driver, 60).until(
            lambda d: ("feed" in d.current_url or "linkedin.com/feed" in d.current_url)
        )
        logging.info("Вход выполнен успешно.")
    except Exception as e:
        logging.error("Ошибка при входе в систему. Проверьте логин вручную.")
        driver.quit()
        return

    try:
        direct_url = (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={config['keyword'].replace(' ', '%20')}"
            f"&location={config['search_country'].replace(' ', '%20')}"
        )
        driver.get(direct_url)
        time.sleep(3)
        wait = WebDriverWait(driver, 30)

        current_page = 1
        while True:
            logging.info(f"=== Обработка страницы {current_page} ===")
            parse_current_page(driver, wait, start_time, config, SEMANTIC_MODEL, SEMANTIC_QUERY_EMBEDDINGS)
            elapsed_time = round(time.perf_counter() - start_time, 2)
            save_results_to_file_with_calculations(results, config["output_file_path"], elapsed_time)

            next_page_number = current_page + 1
            next_button_xpath = f"//button[@aria-label='Page {next_page_number}']"
            next_buttons = driver.find_elements(By.XPATH, next_button_xpath)
            if not next_buttons:
                logging.info(f"Страница {next_page_number} не найдена. Пагинация завершена.")
                break

            next_buttons[0].click()
            current_page += 1
            time.sleep(3)

        elapsed_time = round(time.perf_counter() - start_time, 2)
        save_results_to_file_with_calculations(results, config["output_file_path"], elapsed_time)
        logging.info("Пагинация завершена. Финальные результаты сохранены.")
    except Exception as e:
        logging.error(f"Глобальная ошибка при поиске вакансий: {e}")
        elapsed_time = round(time.perf_counter() - start_time, 2)
        results.append({
            "Company": config["keyword"],
            "Vacancy Title": "",
            "Visa Sponsorship or Relocation": False,
            "Anaplan": False,
            "SAP APO": False,
            "Planning": False,
            "No Relocation Support": False,
            "Remote": False,
            "Already Applied": False,
            "Job URL": None,
            "Elapsed Time (s)": elapsed_time
        })
        save_results_to_file_with_calculations(results, config["output_file_path"], elapsed_time)
    finally:
        driver.quit()
        logging.info("Браузер закрыт.")
        if config.get("shutdown_on_finish"):
            logging.info("Скрипт завершён. Выключение компьютера через 30 секунд.")
            os.system("shutdown /s /t 30")

def start_scraper_thread(config):
    thread = threading.Thread(target=run_scraper, args=(config,))
    thread.start()

# ================================
# Интерфейс (Tkinter)
# ================================
def create_gui():
    root = tk.Tk()
    root.title("LinkedIn Job Scraper")

    search_country_var = tk.StringVar(value=DEFAULT_SEARCH_COUNTRY)
    keyword_var = tk.StringVar(value=DEFAULT_KEYWORD)
    output_file_var = tk.StringVar(value=DEFAULT_OUTPUT_FILE_PATH)
    telegram_bot_token_var = tk.StringVar(value=DEFAULT_TELEGRAM_BOT_TOKEN)
    telegram_chat_id_var = tk.StringVar(value=DEFAULT_TELEGRAM_CHAT_ID)
    chromedriver_path_var = tk.StringVar(value=DEFAULT_CHROMEDRIVER_PATH)
    chrome_profile_path_var = tk.StringVar(value=DEFAULT_CHROME_PROFILE_PATH)
    chrome_binary_location_var = tk.StringVar(value=DEFAULT_CHROME_BINARY_LOCATION)
    shutdown_var = tk.BooleanVar(value=False)

    tk.Label(root, text="Search Country:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=search_country_var, width=40).grid(row=0, column=1, padx=5, pady=5)
    tk.Label(root, text="Keyword:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=keyword_var, width=40).grid(row=1, column=1, padx=5, pady=5)
    tk.Label(root, text="Output Excel File:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=output_file_var, width=40).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=lambda: output_file_var.set(
        filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    )).grid(row=2, column=2, padx=5, pady=5)
    tk.Label(root, text="Telegram Bot Token:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=telegram_bot_token_var, width=40).grid(row=3, column=1, padx=5, pady=5)
    tk.Label(root, text="Telegram Chat ID:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=telegram_chat_id_var, width=40).grid(row=4, column=1, padx=5, pady=5)
    tk.Label(root, text="ChromeDriver Path:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=chromedriver_path_var, width=40).grid(row=5, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=lambda: chromedriver_path_var.set(
        filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
    )).grid(row=5, column=2, padx=5, pady=5)
    tk.Label(root, text="Chrome Profile Path:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=chrome_profile_path_var, width=40).grid(row=6, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=lambda: chrome_profile_path_var.set(
        filedialog.askdirectory()
    )).grid(row=6, column=2, padx=5, pady=5)
    tk.Label(root, text="Chrome Binary Location:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=chrome_binary_location_var, width=40).grid(row=7, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=lambda: chrome_binary_location_var.set(
        filedialog.askopenfilename(filetypes=[("Chrome Executable", "*.exe")])
    )).grid(row=7, column=2, padx=5, pady=5)
    shutdown_checkbox = tk.Checkbutton(root, text="Выключить компьютер после завершения работы скрипта", variable=shutdown_var)
    shutdown_checkbox.grid(row=8, column=0, columnspan=3, pady=5)

    def on_start():
        config = {
            "search_country": search_country_var.get(),
            "keyword": keyword_var.get(),
            "output_file_path": output_file_var.get(),
            "telegram_bot_token": telegram_bot_token_var.get(),
            "telegram_chat_id": telegram_chat_id_var.get(),
            "chromedriver_path": chromedriver_path_var.get(),
            "chrome_profile_path": chrome_profile_path_var.get(),
            "chrome_binary_location": chrome_binary_location_var.get(),
            "shutdown_on_finish": shutdown_var.get()
        }
        if not config["output_file_path"]:
            messagebox.showerror("Ошибка", "Укажите путь для сохранения Excel файла.")
            return
        root.destroy()
        start_scraper_thread(config)

    tk.Button(root, text="Start Scraper", command=on_start, bg="green", fg="white").grid(row=9, column=0, columnspan=3, pady=10)
    root.mainloop()

if __name__ == "__main__":
    create_gui()
