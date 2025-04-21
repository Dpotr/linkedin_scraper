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
import json
import re

# ================================
# Настройка логирования
# ================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ================================
# Значения по умолчанию
# ================================
TG_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "tg_config.json")
try:
    with open(TG_CONFIG_PATH, "r", encoding="utf-8") as f:
        tg_config = json.load(f)
        DEFAULT_TELEGRAM_BOT_TOKEN = tg_config.get("TELEGRAM_BOT_TOKEN", "")
        DEFAULT_TELEGRAM_CHAT_ID = tg_config.get("TELEGRAM_CHAT_ID", "")
except Exception as e:
    DEFAULT_TELEGRAM_BOT_TOKEN = ""
    DEFAULT_TELEGRAM_CHAT_ID = ""
    logging.error(f"Ошибка чтения tg_config.json: {e}")

DEFAULT_CHROMEDRIVER_PATH = r"C:\selenium\chromedriver.exe"
DEFAULT_CHROME_PROFILE_PATH = r"C:\Users\potre\SeleniumProfileNew"
DEFAULT_CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
DEFAULT_OUTPUT_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies_usa_remote.xlsx"
DEFAULT_SEARCH_COUNTRY = "United States"
DEFAULT_KEYWORD = "remote job"

# Ключевые слова
NO_RELOCATION_REQUIREMENTS = [
    "no relocation support", "we do not provide relocation", "no visa sponsorship",
    "relocation not provided", "visa sponsorship unavailable", "relocation assistance not offered",
    "visa sponsorship not included", "no relocation assistance", "we are unable to sponsor visas",
    "visa sponsorship not possible", "local applicants only", "we cannot provide relocation"
]
REMOTE_REQUIREMENTS = [
    "remote", "work from home", "fully remote", "telecommute", "telecommuting", "remote work", "remote position"
]
REMOTE_PROHIBITED = [
    "onsite only", "remote not considered", "remote work not allowed", "no remote work", "remote not possible",
    "remote not available", "remote option not available", "remote is not possible", "remote work not considered",
    "must be onsite", "on-site only", "requires onsite", "remote applicants not considered", "remote work prohibited",
    "remote work is not permitted", "remote is not permitted", "remote not permitted", "remote not supported",
    "remote applicants will not be considered", "must work onsite", "must be on-site", "remote is not an option",
    "remote working is not possible", "no option for remote", "remote is not supported"
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
    "supply planning", "supply chainh planning" "distribution requirements planning", "inventory planning", "production planning",
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

# Глобальные переменные
results = []
total_vacancies_checked = 0

# ================================
# Функция отправки сообщений в Telegram
# ================================
def send_telegram_message(bot_token, chat_id, message, job_url=None, images=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if job_url:
        message += f"\n\n<a href='{job_url}'>Открыть вакансию на LinkedIn</a>"
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
        url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        for img in images:
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
    criteria = ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "No Relocation Support", "Remote", "Remote Prohibited"]
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
# Google Sheets Integration
# ================================
def log_parser_event_to_sheets(event_dict, credentials_path, sheet_url, log_sheet_name=None):
    """
    Logs parser event as a new row in the main Google Sheet (not a separate tab).
    :param event_dict: dict - event info (stage, vacancy, reason, etc.)
    :param credentials_path: str - path to JSON credentials
    :param sheet_url: str - Google Sheets URL
    :param log_sheet_name: str - ignored (for compatibility)
    """
    import gspread
    try:
        gc = gspread.service_account(filename=credentials_path)
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        # Ensure header exists
        headers = worksheet.row_values(1)
        # Add any missing columns from event_dict
        for col in event_dict.keys():
            if col not in headers:
                worksheet.update_cell(1, len(headers)+1, col)
                headers.append(col)
        # --- Duplicate check logic ---
        key_fields = ["Company", "Vacancy Title", "Stage", "TG message sent"]
        key_indices = [headers.index(f)+1 for f in key_fields if f in headers]
        if len(key_indices) == 4:
            all_rows = worksheet.get_all_values()[1:]
            existing_keys = set()
            for row in all_rows:
                try:
                    key = "-".join([row[i-1] for i in key_indices])
                    existing_keys.add(key)
                except Exception:
                    continue
            new_key = "-".join([str(event_dict.get(f, "")) for f in key_fields])
            if new_key in existing_keys:
                logging.info(f"Duplicate event (key: {new_key}) not logged to Google Sheets.")
                return
        # Prepare row to append (align to headers)
        row = [event_dict.get(col, "") for col in headers]
        worksheet.append_row(row, value_input_option='USER_ENTERED')
    except Exception as e:
        logging.error(f"Error logging event to Google Sheets (main sheet): {e}")

# === Batch logging to Google Sheets ===
def batch_log_parser_events_to_sheets(events, credentials_path, sheet_url):
    import gspread
    if not events:
        return
    try:
        gc = gspread.service_account(filename=credentials_path)
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        headers = worksheet.row_values(1)
        # Add any missing columns from events
        for event_dict in events:
            for col in event_dict.keys():
                if col not in headers:
                    worksheet.update_cell(1, len(headers)+1, col)
                    headers.append(col)
        # --- Duplicate check logic for batch ---
        key_fields = ["Company", "Vacancy Title", "Stage", "TG message sent"]
        key_indices = [headers.index(f)+1 for f in key_fields if f in headers]
        all_rows = worksheet.get_all_values()[1:]
        existing_keys = set()
        if len(key_indices) == 4:
            for row in all_rows:
                try:
                    key = "-".join([row[i-1] for i in key_indices])
                    existing_keys.add(key)
                except Exception:
                    continue
        filtered_events = []
        for event_dict in events:
            new_key = "-".join([str(event_dict.get(f, "")) for f in key_fields])
            if len(key_indices) == 4 and new_key in existing_keys:
                logging.info(f"Duplicate event (key: {new_key}) not logged to Google Sheets.")
                continue
            filtered_events.append(event_dict)
            existing_keys.add(new_key)
        if not filtered_events:
            return
        rows = [[event_dict.get(col, "") for col in headers] for event_dict in filtered_events]
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
    except Exception as e:
        logging.error(f"Error batch logging events to Google Sheets: {e}")

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
# Обработка вакансий на странице
# ================================
def parse_current_page(driver, wait, start_time, config):
    global results, total_vacancies_checked
    logs_buffer = []
    matching_jobs = []
    try:
        scroll_until_loaded(driver, pause_time=1, max_consecutive=3)
        job_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        logging.info(f"Найдено вакансий на странице: {len(job_listings)}")
        total_vacancies_checked += len(job_listings)
        # Используем пользовательские ключевые слова
        keywords_visa = config.get("keywords_visa") or KEYWORDS_VISA
        keywords_anaplan = config.get("keywords_anaplan") or KEYWORDS_ANAPLAN
        keywords_sap = config.get("keywords_sap") or KEYWORDS_SAP
        keywords_planning = config.get("keywords_planning") or KEYWORDS_PLANNING
        no_relocation_requirements = config.get("no_relocation_requirements") or NO_RELOCATION_REQUIREMENTS
        remote_requirements = config.get("remote_requirements") or REMOTE_REQUIREMENTS
        remote_prohibited = config.get("remote_prohibited") or REMOTE_PROHIBITED
        all_keywords = config.get("all_keywords") or (
            keywords_visa + keywords_anaplan + keywords_sap + keywords_planning + no_relocation_requirements + remote_requirements + remote_prohibited
        )

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

                try:
                    # 1. Самый специфичный класс
                    try:
                        link_elem = job.find_element(By.CSS_SELECTOR, "a.job-card-list__title--link")
                    except Exception:
                        # 2. Более общий класс
                        try:
                            link_elem = job.find_element(By.CSS_SELECTOR, "a.job-card-container__link")
                        except Exception:
                            link_elem = None

                    job_url = link_elem.get_attribute('href') if link_elem else None
                    if job_url and job_url.startswith('/jobs/view/'):
                        job_url = 'https://www.linkedin.com' + job_url

                    # 3. Если не нашли — старый fallback
                    if not job_url:
                        all_links = job.find_elements(By.TAG_NAME, 'a')
                        for a in all_links:
                            href = a.get_attribute('href')
                            if href and '/jobs/view/' in href:
                                if href.startswith('/jobs/view/'):
                                    href = 'https://www.linkedin.com' + href
                                job_url = href
                                break

                    if not job_url:
                        logging.warning(f"[Job URL] Не удалось найти ссылку для: {job_title} / {job_company_name}\nHTML карточки:\n{job.get_attribute('outerHTML')}")
                except Exception as ex:
                    job_url = None
                    logging.error(f"[Job URL] Ошибка поиска ссылки: {ex}\nHTML карточки:\n{job.get_attribute('outerHTML')}")

                # ДО ФИЛЬТРОВ: логируем просмотр вакансии
                matched_keywords = []
                for kw in (
                    keywords_visa + keywords_anaplan + keywords_sap + keywords_planning + no_relocation_requirements + remote_requirements + remote_prohibited
                ):
                    if kw.lower() in desc_text.lower():
                        matched_keywords.append(kw)
                logs_buffer.append({
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Stage": "Viewed",
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Visa Sponsorship or Relocation": False,
                    "Anaplan": False,
                    "SAP APO": False,
                    "Planning": False,
                    "No Relocation Support": False,
                    "Remote": False,
                    "Remote Prohibited": False,
                    "Already Applied": False,
                    "Job URL": job_url,
                    "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                    "Skills": "",
                    "TG message sent": "",
                    "Matched key words": ", ".join(matched_keywords),
                })

                # Определяем флаги соответствия
                remote_found = any(x in desc_text for x in remote_requirements)
                remote_prohibited_found = any(x in desc_text for x in remote_prohibited)
                visa_or_relocation = any(x in desc_text for x in keywords_visa)
                anaplan_found = any(x in desc_text for x in keywords_anaplan)
                sap_apo_found = any(x in desc_text for x in keywords_sap)
                planning_found = any(x in desc_text for x in keywords_planning)
                already_applied = any(x in desc_text for x in ["applied", "see application", "you have already applied", "already submitted", "previously applied"])

                # Быстрый парсинг навыков для каждой вакансии
                title_words = set(re.findall(r"[A-Za-z0-9\-]+", job_title.lower()))
                desc_words = set(re.findall(r"[A-Za-z0-9\-]+", desc_text))
                stopwords = set(['and','or','the','a','of','to','in','for','on','at','by','with','without','from','is','are','as','an','be','it','this','that','will','not','but','if','we','you','our','your','can','may','all'])
                skill_candidates = [w for w in title_words.union(desc_words) if len(w)>2 and w not in stopwords]
                top_skills = sorted(skill_candidates, key=lambda x: desc_text.count(x) + job_title.lower().count(x), reverse=True)[:10]

                # ФИЛЬТРЫ: если вакансия отсеяна
                if already_applied:
                    logs_buffer.append({
                        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Stage": "Filtered (already applied)",
                        "Company": job_company_name,
                        "Vacancy Title": job_title,
                        "Visa Sponsorship or Relocation": visa_or_relocation,
                        "Anaplan": anaplan_found,
                        "SAP APO": sap_apo_found,
                        "Planning": planning_found,
                        "No Relocation Support": any(x in desc_text for x in no_relocation_requirements),
                        "Remote": remote_found,
                        "Remote Prohibited": remote_prohibited_found,
                        "Already Applied": already_applied,
                        "Job URL": job_url,
                        "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                        "Skills": ", ".join(top_skills),
                        "TG message sent": "",
                        "Matched key words": ", ".join(matched_keywords),
                    })
                    continue

                #!!!!!!!!!!!!!!!!!!!!!!!!!!!! Если не прошла по условиям (remote/visa/anaplan/sap/planning)
                if not ((remote_found or visa_or_relocation) and (anaplan_found or sap_apo_found or planning_found)):
                    logs_buffer.append({
                        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Stage": "Filtered (criteria)",
                        "Company": job_company_name,
                        "Vacancy Title": job_title,
                        "Visa Sponsorship or Relocation": visa_or_relocation,
                        "Anaplan": anaplan_found,
                        "SAP APO": sap_apo_found,
                        "Planning": planning_found,
                        "No Relocation Support": any(x in desc_text for x in no_relocation_requirements),
                        "Remote": remote_found,
                        "Remote Prohibited": remote_prohibited_found,
                        "Already Applied": already_applied,
                        "Job URL": job_url,
                        "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                        "Skills": ", ".join(top_skills),
                        "TG message sent": "",
                        "Matched key words": ", ".join(matched_keywords),
                    })
                    continue

                # ПРОШЛА ФИЛЬТРЫ: логируем
                tg_sent = False
                logs_buffer.append({
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Stage": "Passed filters",
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Visa Sponsorship or Relocation": visa_or_relocation,
                    "Anaplan": anaplan_found,
                    "SAP APO": sap_apo_found,
                    "Planning": planning_found,
                    "No Relocation Support": any(x in desc_text for x in no_relocation_requirements),
                    "Remote": remote_found,
                    "Remote Prohibited": remote_prohibited_found,
                    "Already Applied": already_applied,
                    "Job URL": job_url,
                    "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                    "Skills": ", ".join(top_skills),
                    "TG message sent": "",
                    "Matched key words": ", ".join(matched_keywords),
                })

                matched_keywords = []
                for kw in (
                    keywords_visa + keywords_anaplan + keywords_sap + keywords_planning + no_relocation_requirements + remote_requirements + remote_prohibited
                ):
                    if kw.lower() in desc_text.lower():
                        matched_keywords.append(kw)
                current_result = {
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Visa Sponsorship or Relocation": visa_or_relocation,
                    "Anaplan": anaplan_found,
                    "SAP APO": sap_apo_found,
                    "Planning": planning_found,
                    "No Relocation Support": any(x in desc_text for x in no_relocation_requirements),
                    "Remote": remote_found,
                    "Remote Prohibited": remote_prohibited_found,
                    "Already Applied": already_applied,
                    "Job URL": job_url,
                    "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                    "Skills": ", ".join(top_skills),
                    "Matched key words": ", ".join(matched_keywords),
                }
                matching_jobs.append(current_result)
                running_minutes = (time.perf_counter() - start_time) / 60
                summary = get_excel_summary(config["output_file_path"], running_minutes)
                message_text = (
                    f"🔔 Найдена вакансия по ключевому слову <b>{config['keyword']}</b>\n"
                    f"Компания: <b>{job_company_name}</b>\n"
                    f"Вакансия: <b>{job_title}</b>\n\n"
                    f"Matched key words: {', '.join(matched_keywords)}\n"
                    f"Навыки: {', '.join(top_skills)}\n"
                    f"Язык описания: {detected_language.upper()}\n\n"
                    f"Ссылка на вакансию: <a href='{job_url}'>{job_url}</a>\n\n"
                    f"Всего проверено вакансий: {total_vacancies_checked}\n"
                    + summary
                )
                p_chart = create_p_chart(results)
                bar_chart = create_bar_chart(results)
                images = []
                if p_chart:
                    images.append(p_chart)
                if bar_chart:
                    images.append(bar_chart)
                send_telegram_message(config["telegram_bot_token"], config["telegram_chat_id"], message_text, job_url=job_url, images=images)
                tg_sent = True
                # Update log with TG message sent
                logs_buffer.append({
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Stage": "Passed filters",
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Visa Sponsorship or Relocation": visa_or_relocation,
                    "Anaplan": anaplan_found,
                    "SAP APO": sap_apo_found,
                    "Planning": planning_found,
                    "No Relocation Support": any(x in desc_text for x in no_relocation_requirements),
                    "Remote": remote_found,
                    "Remote Prohibited": remote_prohibited_found,
                    "Already Applied": already_applied,
                    "Job URL": job_url,
                    "Elapsed Time (s)": round(time.perf_counter() - start_time, 2),
                    "Skills": ", ".join(top_skills),
                    "TG message sent": "yes",
                    "Matched key words": ", ".join(matched_keywords),
                })
                results.append(current_result)
            except Exception as e:
                logging.error(f"Ошибка при обработке вакансии №{i}: {e}")
                continue

        # --- Google Sheets: запись результатов (batch) ---
        if config.get("google_sheets_url") and config.get("google_sheets_credentials"):
            batch_log_parser_events_to_sheets(logs_buffer, config["google_sheets_credentials"], config["google_sheets_url"])
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
    repetitive_parsing = config.get("repetitive_parsing", False)
    while True:
        # Используем пользовательские ключевые слова, если они есть, иначе дефолтные
        keywords_visa = config.get("keywords_visa") or KEYWORDS_VISA
        keywords_anaplan = config.get("keywords_anaplan") or KEYWORDS_ANAPLAN
        keywords_sap = config.get("keywords_sap") or KEYWORDS_SAP
        keywords_planning = config.get("keywords_planning") or KEYWORDS_PLANNING
        no_relocation_requirements = config.get("no_relocation_requirements") or NO_RELOCATION_REQUIREMENTS
        remote_requirements = config.get("remote_requirements") or REMOTE_REQUIREMENTS
        remote_prohibited = config.get("remote_prohibited") or REMOTE_PROHIBITED
        all_keywords = (
            keywords_visa
            + keywords_anaplan
            + keywords_sap
            + keywords_planning
            + no_relocation_requirements
            + remote_requirements
            + remote_prohibited
        )
        # Передаче all_keywords и остальные списки в parse_current_page через config
        config["all_keywords"] = all_keywords
        config["keywords_visa"] = keywords_visa
        config["keywords_anaplan"] = keywords_anaplan
        config["keywords_sap"] = keywords_sap
        config["keywords_planning"] = keywords_planning
        config["no_relocation_requirements"] = no_relocation_requirements
        config["remote_requirements"] = remote_requirements
        config["remote_prohibited"] = remote_prohibited

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
                parse_current_page(driver, wait, start_time, config)
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
                "Remote Prohibited": False,
                "Already Applied": False,
                "Job URL": None,
                "Elapsed Time (s)": elapsed_time,
                "Skills": "",
                "TG message sent": "",
                "Matched key words": "",
            })
            save_results_to_file_with_calculations(results, config["output_file_path"], elapsed_time)
        finally:
            driver.quit()
            logging.info("Браузер закрыт.")
            if config.get("shutdown_on_finish"):
                logging.info("Скрипт завершён. Выключение компьютера через 30 секунд.")
                os.system("shutdown /s /t 30")
        if not repetitive_parsing:
            break
        logging.info("Repetitive parsing enabled: restarting from first page...")
        # Здесь можно добавить сброс состояния, если нужно
        # Например, сбросить текущую страницу на 1, обновить драйвер и т.д.
        # В зависимости от вашей логики, возможно потребуется реализовать функцию reset_to_first_page()
        # reset_to_first_page(driver)

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
    repetitive_parsing_var = tk.BooleanVar(value=False)

    keywords_visa_var = tk.StringVar(value=", ".join(KEYWORDS_VISA))
    keywords_anaplan_var = tk.StringVar(value=", ".join(KEYWORDS_ANAPLAN))
    keywords_sap_var = tk.StringVar(value=", ".join(KEYWORDS_SAP))
    keywords_planning_var = tk.StringVar(value=", ".join(KEYWORDS_PLANNING))
    no_relocation_requirements_var = tk.StringVar(value=", ".join(NO_RELOCATION_REQUIREMENTS))
    remote_requirements_var = tk.StringVar(value=", ".join(REMOTE_REQUIREMENTS))
    remote_prohibited_var = tk.StringVar(value=", ".join(REMOTE_PROHIBITED))

    google_sheets_url_var = tk.StringVar(value="https://docs.google.com/spreadsheets/d/173Zb-CkHxamDlQ3q7aFD-1Ay3nk6W7hrEq2aD6y4VJ4/edit?usp=sharing")
    google_sheets_credentials_var = tk.StringVar(value="C:/Users/potre/OneDrive/LinkedIn_Automation/google_sheets_credentials.json")

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
    repetitive_checkbox = tk.Checkbutton(root, text="Repetitive parsing (бесконечный парсинг)", variable=repetitive_parsing_var)
    repetitive_checkbox.grid(row=9, column=0, columnspan=3, pady=5)

    def on_start():
        # Получаем пользовательские ключевые слова и разбиваем их по запятым
        config = {
            "search_country": search_country_var.get(),
            "keyword": keyword_var.get(),
            "output_file_path": output_file_var.get(),
            "telegram_bot_token": telegram_bot_token_var.get(),
            "telegram_chat_id": telegram_chat_id_var.get(),
            "chromedriver_path": chromedriver_path_var.get(),
            "chrome_profile_path": chrome_profile_path_var.get(),
            "chrome_binary_location": chrome_binary_location_var.get(),
            "shutdown_on_finish": shutdown_var.get(),
            "keywords_visa": [kw.strip() for kw in keywords_visa_var.get().split(",") if kw.strip()],
            "keywords_anaplan": [kw.strip() for kw in keywords_anaplan_var.get().split(",") if kw.strip()],
            "keywords_sap": [kw.strip() for kw in keywords_sap_var.get().split(",") if kw.strip()],
            "keywords_planning": [kw.strip() for kw in keywords_planning_var.get().split(",") if kw.strip()],
            "no_relocation_requirements": [kw.strip() for kw in no_relocation_requirements_var.get().split(",") if kw.strip()],
            "remote_requirements": [kw.strip() for kw in remote_requirements_var.get().split(",") if kw.strip()],
            "remote_prohibited": [kw.strip() for kw in remote_prohibited_var.get().split(",") if kw.strip()],
            "google_sheets_url": google_sheets_url_var.get(),
            "google_sheets_credentials": google_sheets_credentials_var.get(),
            "repetitive_parsing": repetitive_parsing_var.get()
        }
        if not config["output_file_path"]:
            messagebox.showerror("Ошибка", "Укажите путь для сохранения Excel файла.")
            return
        root.destroy()
        start_scraper_thread(config)

    tk.Button(root, text="Start Scraper", command=on_start, bg="green", fg="white").grid(row=18, column=0, columnspan=3, pady=10)
    root.mainloop()

if __name__ == "__main__":
    create_gui()
