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
import random

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

# Profile Management Configuration
PROFILES = {
    "main": r"C:\Users\potre\SeleniumProfileNew",
    "dummy": r"C:\Users\potre\SeleniumProfileDummy"
}
ACTIVE_PROFILE = "dummy"  # Change this to switch profiles

def validate_and_get_profile_path():
    """Validate profile exists and return path"""
    profile_path = PROFILES[ACTIVE_PROFILE]
    if not os.path.exists(profile_path):
        os.makedirs(profile_path, exist_ok=True)
        logging.info(f"Created new profile directory: {profile_path}")
    return profile_path

def get_random_delay(min_sec=2, max_sec=8):
    """Get random delay for behavioral disguise"""
    return random.uniform(min_sec, max_sec)

def generate_output_filename(country, keyword):
    """Generate output filename from country and keyword"""
    import re
    # More conservative approach - clean and limit inputs
    safe_country = re.sub(r'[^\w]', '_', country.strip())[:20]
    safe_keyword = re.sub(r'[^\w]', '_', keyword.strip())[:25]
    
    # Ensure meaningful names even with short inputs
    if not safe_country: safe_country = "country"
    if not safe_keyword: safe_keyword = "keyword"
    
    # Remove consecutive underscores and trim
    safe_country = re.sub(r'_+', '_', safe_country).strip('_')
    safe_keyword = re.sub(r'_+', '_', safe_keyword).strip('_')
    
    base_dir = r"C:\Users\potre\OneDrive\LinkedIn_Automation"
    filename = f"{safe_country}_{safe_keyword}_jobs.xlsx"
    
    # Validate total path length (Windows limit ~260 chars)
    full_path = os.path.join(base_dir, filename)
    if len(full_path) > 250:  # Leave buffer
        # Truncate keyword more aggressively
        max_keyword_len = 250 - len(base_dir) - len(safe_country) - len("_jobs.xlsx") - 2
        if max_keyword_len > 5:
            safe_keyword = safe_keyword[:max_keyword_len].strip('_')
            filename = f"{safe_country}_{safe_keyword}_jobs.xlsx"
            full_path = os.path.join(base_dir, filename)
    
    return full_path

DEFAULT_CHROMEDRIVER_PATH = r"C:\selenium\chromedriver.exe"
DEFAULT_CHROME_PROFILE_PATH = validate_and_get_profile_path()
DEFAULT_CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
# Default will be generated dynamically based on country/keyword
DEFAULT_OUTPUT_FILE_PATH = ""
DEFAULT_SEARCH_COUNTRY = "United States"
DEFAULT_KEYWORD = "remote job, planning"

# Ключевые слова
NO_RELOCATION_REQUIREMENTS = [
    "no relocation support", "we do not provide relocation", "no visa sponsorship",
    "relocation not provided", "visa sponsorship unavailable", "relocation assistance not offered",
    "visa sponsorship not included", "no relocation assistance", "we are unable to sponsor visas",
    "visa sponsorship not possible", "local applicants only", "we cannot provide relocation", "Relocation Assistance Provided: No","no relocation"
]
REMOTE_REQUIREMENTS = [
    "remote", "work from home", "fully remote", "telecommute", "telecommuting", "remote work", "remote position"
]
REMOTE_PROHIBITED = [
    "onsite only", "remote not considered", "remote work not allowed", "no remote work", "remot3e not possible",
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

# Глобальные переменные
results = []
total_vacancies_checked = 0

# Cycle tracking variables
cycle_number = 1
cycle_parsed_jobs = 0
cycle_new_matches = 0
cycle_matched_jobs = []  # List of {company, position} dicts for current cycle
cycle_new_jobs_only = []  # NEW: List of truly new jobs (not seen in previous cycles)
total_matches_all_time = 0
unique_jobs_discovered = 0  # NEW: Count of unique jobs discovered across all cycles
all_time_matched_jobs = set()  # NEW: Track all jobs ever matched across all cycles

# ================================
# Функция отправки сообщений в Telegram
# ================================
def send_telegram_message(bot_token, chat_id, message, job_url=None, images=None):
    """Send Telegram notification with graceful degradation on failure."""
    if not bot_token or not chat_id:
        logging.warning("Telegram not configured, skipping notification")
        return  # Silently skip if not configured
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if job_url:
        message += f"\n\n<a href='{job_url}'>Открыть вакансию на LinkedIn</a>"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    
    try:
        resp = requests.post(url, data=data, timeout=10)  # Add timeout
        if resp.status_code == 200:
            logging.info("Telegram message sent successfully")
        else:
            logging.warning(f"Telegram API error: {resp.status_code} - continuing without notification")
    except requests.exceptions.Timeout:
        logging.warning("Telegram timeout - continuing without notification")
    except Exception as e:
        logging.warning(f"Telegram unavailable ({str(e)[:50]}) - continuing without notification")
    
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
# Cycle Summary Functions
# ================================
def generate_cycle_summary_message():
    """Generate cycle summary message with matched jobs list"""
    global cycle_number, cycle_parsed_jobs, cycle_new_matches, total_matches_all_time, cycle_new_jobs_only, unique_jobs_discovered
    
    # Validate state before generating summary
    if not validate_cycle_state():
        logging.error("Cycle state validation failed during summary generation")
    
    # Calculate duplicates found this cycle
    duplicates_this_cycle = cycle_new_matches - len(cycle_new_jobs_only)
    
    # Build the main summary
    message_lines = [
        f"🔄 Cycle #{cycle_number} Completed",
        "",
        "📊 Statistics:",
        f"• Jobs scanned: {cycle_parsed_jobs}",
        f"• Matches found this cycle: {cycle_new_matches} ({len(cycle_new_jobs_only)} new, {duplicates_this_cycle} duplicates)",
        f"• Unique jobs discovered to date: {unique_jobs_discovered}",
        f"• Total match occurrences: {total_matches_all_time}",
    ]
    
    # Add NEW jobs list if any (only jobs not seen in previous cycles)
    if cycle_new_jobs_only:
        message_lines.extend(["", "✅ NEW Matched Jobs:"])
        # Limit to 20 jobs to avoid message being too long
        display_jobs = cycle_new_jobs_only[:20]
        for i, job in enumerate(display_jobs, 1):
            job_line = f"{i}. {job['company']} - {job['position']}"
            # Truncate very long lines
            if len(job_line) > 100:
                job_line = job_line[:97] + "..."
            message_lines.append(job_line)
        
        # Add note if more jobs exist
        if len(cycle_new_jobs_only) > 20:
            message_lines.append(f"...and {len(cycle_new_jobs_only) - 20} more")
    else:
        message_lines.extend(["", "No new jobs found in this cycle (all matches were duplicates from previous cycles)."])
    
    return "\n".join(message_lines)

def validate_cycle_state():
    """Validate that cycle tracking variables are consistent"""
    global unique_jobs_discovered, total_matches_all_time, all_time_matched_jobs, cycle_new_matches, cycle_new_jobs_only
    
    # Validate that unique jobs counter matches the set size
    if unique_jobs_discovered != len(all_time_matched_jobs):
        logging.error(f"State inconsistency: unique_jobs_discovered={unique_jobs_discovered}, but set size={len(all_time_matched_jobs)}")
        return False
    
    # Validate that unique jobs count doesn't exceed total matches
    if unique_jobs_discovered > total_matches_all_time:
        logging.error(f"State inconsistency: unique_jobs_discovered={unique_jobs_discovered} > total_matches_all_time={total_matches_all_time}")
        return False
    
    # Validate cycle consistency  
    duplicates_this_cycle = cycle_new_matches - len(cycle_new_jobs_only)
    if duplicates_this_cycle < 0:
        logging.error(f"Cycle inconsistency: cycle_new_matches={cycle_new_matches} < cycle_new_jobs_only={len(cycle_new_jobs_only)}")
        return False
    
    return True

def reset_cycle_counters():
    """Reset cycle-specific counters for new cycle"""
    global cycle_parsed_jobs, cycle_new_matches, cycle_matched_jobs, cycle_new_jobs_only, cycle_number
    
    # Validate state before reset
    if not validate_cycle_state():
        logging.warning("Cycle state validation failed before reset - continuing anyway")
    
    cycle_parsed_jobs = 0
    cycle_new_matches = 0
    cycle_matched_jobs = []
    cycle_new_jobs_only = []  # Reset new jobs list for next cycle
    cycle_number += 1
    logging.info(f"Starting cycle #{cycle_number}")

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
    except FileNotFoundError:
        # Excel file doesn't exist yet (first run) - this is normal
        logging.info(f"Excel file not found (first run): {file_path}")
        return f"Running time, min: {running_time_minutes:.2f}"
    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из Excel: {e}")
        return f"Running time, min: {running_time_minutes:.2f}"

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
    if not credentials_path or not sheet_url:
        logging.debug("Google Sheets not configured, skipping log")
        return  # Silently skip if not configured
    
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
    except FileNotFoundError:
        logging.error(f"Google Sheets credentials file not found: {credentials_path}")
    except Exception as e:
        # Log error but continue - don't crash the scraper
        logging.warning(f"Could not log to Google Sheets: {str(e)[:100]} - continuing")

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
# Функция прокрутки с захватом вакансий
# ================================
def scroll_until_loaded_linkedin_specific(driver, max_attempts=20, pause_time=1.5):
    """
    LINKEDIN-SPECIFIC FIX: Targets LinkedIn's specific lazy loading mechanism.
    Forces the job list container to load all content by scrolling to specific trigger points.
    """
    from selenium.webdriver.common.by import By
    import time
    
    logging.info("Starting LinkedIn-specific scrolling...")
    
    # Find the specific LinkedIn job list container - EXPANDED SELECTORS
    job_list_selectors = [
        ".jobs-search-results-list",
        ".jobs-search__results-list", 
        ".scaffold-layout__list-container",
        ".jobs-search-results",
        ".jobs-search-results__list",
        ".scaffold-layout__list",
        ".jobs-search-results-list__container",
        "[data-test-id='jobs-search-results-list']",
        ".scaffold-layout__list-detail-inner",
        ".jobs-search__results",
        ".scaffold-layout-container"
    ]
    
    job_container = None
    for selector in job_list_selectors:
        try:
            job_container = driver.find_element(By.CSS_SELECTOR, selector)
            logging.info(f"Found job container: {selector}")
            break
        except:
            continue
    
    if not job_container:
        logging.warning("Could not find job container, falling back to body scroll")
        job_container = driver.find_element(By.TAG_NAME, "body")
    
    prev_count = 0
    no_change_count = 0
    
    # Strategy 1: Scroll to bottom of job container to force loading
    try:
        driver.execute_script("""
            const container = arguments[0];
            const scrollHeight = container.scrollHeight || document.documentElement.scrollHeight;
            
            // Scroll in increments to trigger lazy loading
            let currentScroll = 0;
            const scrollStep = Math.max(400, scrollHeight / 10);
            
            const scrollInterval = setInterval(() => {
                currentScroll += scrollStep;
                window.scrollTo(0, currentScroll);
                
                if (currentScroll >= scrollHeight + 1000) {
                    clearInterval(scrollInterval);
                }
            }, 800);
            
            // Also scroll the container itself if it's scrollable
            if (container.scrollHeight > container.clientHeight) {
                container.scrollTop = container.scrollHeight;
            }
        """, job_container)
        
        time.sleep(5)  # Wait for JavaScript scrolling to complete
        
    except Exception as e:
        logging.warning(f"JavaScript scroll failed: {e}")
    
    # Strategy 2: Manual step-by-step scrolling with job count monitoring  
    for attempt in range(max_attempts):
        current_count = len(driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable"))
        
        if current_count > prev_count:
            logging.info(f"Found {current_count - prev_count} new jobs (total: {current_count})")
            prev_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1
        
        # Stop if no new jobs for several attempts OR we have reasonable count
        if no_change_count >= 8 or current_count >= 20:
            logging.info(f"Stopping: no_change_count={no_change_count}, current_count={current_count}")
            break
        
        # Different scrolling strategies based on attempt
        if attempt < 5:
            # Initial: Scroll by pixels to trigger loading
            driver.execute_script(f"window.scrollBy(0, {500 + attempt * 100});")
        elif attempt < 10:
            # Mid: Try scrolling to specific job elements
            try:
                jobs = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
                if jobs:
                    last_job = jobs[-1]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last_job)
                    time.sleep(0.5)
                    driver.execute_script("window.scrollBy(0, 300);")  # Scroll past it
            except:
                driver.execute_script("window.scrollBy(0, 600);")
        else:
            # Final: Aggressive scrolling to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(0, 500);")  # Scroll even further
        
        time.sleep(pause_time + get_random_delay(0.3, 0.8))
    
    final_count = len(driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable"))
    logging.info(f"LINKEDIN SCROLLING COMPLETE: Found {final_count} jobs after {attempt + 1} attempts")
    
    # ENHANCED: More aggressive final attempt if we still have few jobs
    if final_count < 23:  # Increased threshold since we expect ~25 per page
        logging.warning(f"Moderate job count ({final_count}), trying enhanced scroll...")
        
        # Multiple enhanced strategies
        strategies = [
            # Strategy 1: Multiple bottom scrolls with pauses
            lambda: [driver.execute_script("window.scrollTo(0, document.body.scrollHeight + 500 * i);") or time.sleep(0.8) for i in range(8)],
            # Strategy 2: Scroll to each existing job element
            lambda: [driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", job) or time.sleep(0.3) for job in driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")],
            # Strategy 3: Rapid scroll bursts
            lambda: [driver.execute_script(f"window.scrollBy(0, {200 + i * 100});") or time.sleep(0.2) for i in range(12)],
            # Strategy 4: End scroll + key presses
            lambda: [driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") or time.sleep(0.5) or driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END) or time.sleep(0.5) for _ in range(3)]
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                strategy()
                current_count = len(driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable"))
                if current_count > final_count:
                    logging.info(f"Strategy {i+1} found {current_count - final_count} more jobs (total: {current_count})")
                    final_count = current_count
                    if final_count >= 23:  # Good enough
                        break
            except Exception as e:
                logging.debug(f"Strategy {i+1} failed: {e}")
        
        final_final_count = len(driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable"))
        logging.info(f"After enhanced scroll: {final_final_count} jobs (gained: {final_final_count - final_count})")
    
    # Final wait for any remaining content
    time.sleep(get_random_delay(2, 4))

# Helper functions removed - using simpler approach

# ================================
# Обработка вакансий на странице
# ================================
def parse_current_page(driver, wait, start_time, config):
    global results, total_vacancies_checked
    logs_buffer = []
    matching_jobs = []
    try:
        # LINKEDIN-SPECIFIC FIX: Target LinkedIn's lazy loading mechanism
        scroll_until_loaded_linkedin_specific(driver, max_attempts=20, pause_time=1.5)
        job_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        actual_job_count = len(job_listings)
        logging.info(f"CAPTURED вакансий на странице: {actual_job_count}")
        total_vacancies_checked += actual_job_count
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

        # SIMPLIFIED: Process jobs with basic error handling
        processed_jobs = 0
        for i, job in enumerate(job_listings, start=1):
            try:
                # Basic validation that element is still accessible
                try:
                    job.tag_name  # Simple stale element check
                except Exception:
                    logging.warning(f"Job element {i} became stale, skipping...")
                    continue
                
                action = ActionChains(driver)
                # --- Улучшенное извлечение даты публикации ДО клика на карточку ---
                date_text = ""
                transformed_publish_date = ""
                try:
                    date_selectors = [
                        ".job-search-card__listdate",
                        ".job-search-card__listdate--new",
                        ".job-card-container__listed-time",
                        ".job-card-list__footer-wrapper time",
                        "time",
                        "span"
                    ]
                    for sel in date_selectors:
                        try:
                            elem = job.find_element(By.CSS_SELECTOR, sel)
                            text = elem.text.strip()
                            if text and any(x in text.lower() for x in ["ago", "hour", "day", "month", "viewed", "yesterday", "today", "just now"]):
                                date_text = text
                                break
                        except Exception:
                            continue
                    if not date_text:
                        for elem in job.find_elements(By.XPATH, ".//*"):
                            text = elem.text.strip()
                            if text and any(x in text.lower() for x in ["ago", "hour", "day", "month", "viewed", "yesterday", "today", "just now"]):
                                date_text = text
                                break
                except Exception as e:
                    print(f"[Job Date] Ошибка поиска даты: {e}")

                # --- Преобразование "N days ago" и др. в YYYY-MM-DD ---
                import re, datetime
                def parse_relative_date(text, now=None):
                    if now is None:
                        now = datetime.datetime.now()
                    text = text.lower().strip()
                    if "just now" in text:
                        return now.date().isoformat()
                    if "today" in text:
                        return now.date().isoformat()
                    if "yesterday" in text:
                        return (now - datetime.timedelta(days=1)).date().isoformat()
                    m = re.match(r"(\d+)\s+minute", text)
                    if m:
                        return (now - datetime.timedelta(minutes=int(m.group(1)))).date().isoformat()
                    m = re.match(r"(\d+)\s+hour", text)
                    if m:
                        return (now - datetime.timedelta(hours=int(m.group(1)))).date().isoformat()
                    m = re.match(r"(\d+)\s+day", text)
                    if m:
                        return (now - datetime.timedelta(days=int(m.group(1)))).date().isoformat()
                    m = re.match(r"(\d+)\s+week", text)
                    if m:
                        return (now - datetime.timedelta(weeks=int(m.group(1)))).date().isoformat()
                    m = re.match(r"(\d+)\s+month", text)
                    if m:
                        # Приблизительно 30 дней в месяце
                        return (now - datetime.timedelta(days=30*int(m.group(1)))).date().isoformat()
                    m = re.match(r"(\d+)\s+year", text)
                    if m:
                        return (now - datetime.timedelta(days=365*int(m.group(1)))).date().isoformat()
                    # Если просто "viewed" или что-то нестандартное, возвращаем пусто
                    return ""
                transformed_publish_date = parse_relative_date(date_text, now=datetime.datetime.strptime("2025-04-22T21:35:02+02:00", "%Y-%m-%dT%H:%M:%S%z")) if date_text else ""
                # Теперь кликаем на карточку, чтобы раскрыть детали
                action.move_to_element(job).click().perform()

                desc_element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-box__html-content"))
                )
                desc_text = ""
                for _ in range(10):
                    time.sleep(get_random_delay(0.5, 1.5))  # Random delay between job clicks
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
                    "Cycle #": cycle_number,
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
                    "Search Keyword": config.get("keyword", ""),
                    "Search Country": config.get("search_country", ""),
                    "Job Date": date_text or "",
                    "transformed publish date from description": transformed_publish_date or ""
                })
                # Increment cycle parsed jobs counter
                global cycle_parsed_jobs
                cycle_parsed_jobs += 1

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
                        "Cycle #": cycle_number,
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
                        "Search Keyword": config.get("keyword", ""),
                        "Search Country": config.get("search_country", ""),
                        "Job Date": date_text or "",
                        "transformed publish date from description": transformed_publish_date or ""
                    })
                    continue

                # Apply configurable filter logic
                location_passes = True
                skills_passes = True
                
                # Check location requirements (remote/visa)
                require_remote = config.get("require_remote", False)
                require_visa = config.get("require_visa", False)
                
                if require_remote or require_visa:
                    if config.get("location_logic", "OR") == "OR":
                        # At least one location option must be available if enabled
                        location_options = []
                        if require_remote:
                            location_options.append(remote_found)
                        if require_visa:
                            location_options.append(visa_or_relocation)
                        location_passes = any(location_options) if location_options else True
                    else:  # AND logic
                        location_passes = True
                        if require_remote and not remote_found:
                            location_passes = False
                        if require_visa and not visa_or_relocation:
                            location_passes = False
                else:
                    # If both checkboxes are unticked, show all jobs (no location filtering)
                    location_passes = True
                
                # Check skills requirement
                if config.get("require_skills", True):
                    skills_passes = (anaplan_found or sap_apo_found or planning_found)
                
                # Check remote prohibited exclusion
                if config.get("block_remote_prohibited", False) and remote_prohibited_found:
                    location_passes = False
                
                # Create detailed filter reason for logging
                filter_details = []
                if not location_passes:
                    if config.get("block_remote_prohibited", False) and remote_prohibited_found:
                        filter_details.append("blocked: remote prohibited")
                    elif config.get("location_logic", "OR") == "OR":
                        missing_location = []
                        if require_remote and not remote_found:
                            missing_location.append("remote")
                        if require_visa and not visa_or_relocation:
                            missing_location.append("visa")
                        if missing_location:
                            filter_details.append(f"missing location: needs {' OR '.join(missing_location)}")
                    else:  # AND logic
                        missing_and = []
                        if require_remote and not remote_found:
                            missing_and.append("remote")
                        if require_visa and not visa_or_relocation:
                            missing_and.append("visa")
                        if missing_and:
                            filter_details.append(f"missing location: needs {' AND '.join(missing_and)}")
                
                if not skills_passes:
                    filter_details.append("missing skills: needs Anaplan OR SAP OR Planning")
                
                filter_reason = "; ".join(filter_details) if filter_details else "criteria"
                
                # Final filter decision
                if not (location_passes and skills_passes):
                    logs_buffer.append({
                        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Stage": f"Filtered ({filter_reason})",
                        "Company": job_company_name,
                        "Vacancy Title": job_title,
                        "Cycle #": cycle_number,
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
                        "Search Keyword": config.get("keyword", ""),
                        "Search Country": config.get("search_country", ""),
                        "Job Date": date_text or "",
                        "transformed publish date from description": transformed_publish_date or ""
                    })
                    continue

                # ПРОШЛА ФИЛЬТРЫ: логируем
                tg_sent = False
                logs_buffer.append({
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Stage": "Passed filters",
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Cycle #": cycle_number,
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
                    "Search Keyword": config.get("keyword", ""),
                    "Search Country": config.get("search_country", ""),
                    "Job Date": date_text or "",
                    "transformed publish date from description": transformed_publish_date or "",
                    "Filter Config": f"Remote:{require_remote}, Visa:{require_visa}, Logic:{config.get('location_logic','OR')}, Skills:{config.get('require_skills',False)}, Block:{config.get('block_remote_prohibited',False)}"
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
                    "Cycle #": cycle_number,
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
                    "Search Keyword": config.get("keyword", ""),
                    "Search Country": config.get("search_country", ""),
                    "Job Date": date_text or "",
                    "transformed publish date from description": transformed_publish_date or ""
                }
                matching_jobs.append(current_result)
                
                # Track matched job for cycle summary
                global cycle_new_matches, total_matches_all_time, cycle_matched_jobs, cycle_new_jobs_only, all_time_matched_jobs
                job_entry = {"company": job_company_name, "position": job_title}
                job_key = f"{job_company_name.lower().strip()}|{job_title.lower().strip()}"  # Create unique identifier (normalized)
                
                # Check if this is truly a NEW job (not seen in any previous cycle)
                is_new_job = job_key not in all_time_matched_jobs
                
                # Always increment counters and track in cycle (for statistics)
                cycle_new_matches += 1
                total_matches_all_time += 1
                
                # Add to matched jobs list if not already there (avoid duplicates within cycle)
                if job_entry not in cycle_matched_jobs:
                    cycle_matched_jobs.append(job_entry)
                
                # Only send Telegram message for NEW jobs (not duplicates from previous cycles)
                if is_new_job:
                    global unique_jobs_discovered
                    all_time_matched_jobs.add(job_key)  # Mark as seen
                    cycle_new_jobs_only.append(job_entry)  # Add to truly new jobs list
                    unique_jobs_discovered += 1  # Track unique jobs discovered
                    
                    # Send Telegram notification
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
                    logging.info(f"NEW job: Telegram message sent for {job_company_name} - {job_title}")
                else:
                    logging.info(f"DUPLICATE job: Telegram message NOT sent for {job_company_name} - {job_title} (already seen in previous cycle)")
                    tg_sent = False
                # Update log with TG message sent
                logs_buffer.append({
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Stage": "Passed filters",
                    "Company": job_company_name,
                    "Vacancy Title": job_title,
                    "Cycle #": cycle_number,
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
                    "TG message sent": "yes" if tg_sent else "no (duplicate)",
                    "Matched key words": ", ".join(matched_keywords),
                    "Search Keyword": config.get("keyword", ""),
                    "Search Country": config.get("search_country", ""),
                    "Job Date": date_text or "",
                    "transformed publish date from description": transformed_publish_date or ""
                })
                results.append(current_result)
                processed_jobs += 1
            except Exception as e:
                logging.error(f"Ошибка при обработке вакансии №{i}: {e}", exc_info=True)
                continue

        # Simple validation: log final counts
        logging.info(f"PAGE COMPLETE: {processed_jobs} jobs processed from {actual_job_count} found")
        
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
    global cycle_number, cycle_parsed_jobs, cycle_new_matches, cycle_matched_jobs, cycle_new_jobs_only, total_matches_all_time, unique_jobs_discovered, all_time_matched_jobs
    results = []
    total_vacancies_checked = 0
    # Initialize cycle tracking variables
    cycle_number = 1
    cycle_parsed_jobs = 0
    cycle_new_matches = 0
    cycle_matched_jobs = []
    cycle_new_jobs_only = []
    total_matches_all_time = 0
    unique_jobs_discovered = 0
    all_time_matched_jobs = set()
    start_time = time.perf_counter()
    repetitive_parsing = config.get("repetitive_parsing", False)
    logging.info(f"Starting cycle #{cycle_number}")
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
            time.sleep(get_random_delay(2, 5))  # Random delay between pages
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
                time.sleep(get_random_delay(2, 5))  # Random delay between pages

            elapsed_time = round(time.perf_counter() - start_time, 2)
            save_results_to_file_with_calculations(results, config["output_file_path"], elapsed_time)
            logging.info("Пагинация завершена. Финальные результаты сохранены.")
        except Exception as e:
            logging.error(f"Глобальная ошибка при поиске вакансий: {e}")
            elapsed_time = round(time.perf_counter() - start_time, 2)
            results.append({
                "Company": config["keyword"],
                "Vacancy Title": "",
                "Cycle #": cycle_number,
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
                "Search Keyword": config.get("keyword", ""),
                "Search Country": config.get("search_country", ""),
                "Job Date": "",
                "transformed publish date from description": ""
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
        
        # Send cycle summary via Telegram before starting next cycle
        try:
            summary_message = generate_cycle_summary_message()
            send_telegram_message(
                config["telegram_bot_token"], 
                config["telegram_chat_id"], 
                summary_message
            )
            logging.info(f"Cycle #{cycle_number} summary sent to Telegram")
        except Exception as e:
            logging.warning(f"Failed to send cycle summary: {e}")
        
        # Reset cycle counters for new cycle
        reset_cycle_counters()
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
    # Generate default output filename from country and keyword
    default_output_path = generate_output_filename(DEFAULT_SEARCH_COUNTRY, DEFAULT_KEYWORD)
    output_file_var = tk.StringVar(value=default_output_path)
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
    
    # Auto-filename generation control
    auto_filename_var = tk.BooleanVar(value=True)
    filename_preview_var = tk.StringVar(value="")
    
    def update_output_filename(*args):
        """Update output filename when country or keyword changes"""
        if not auto_filename_var.get():
            return  # Don't auto-update if manual mode is selected
            
        try:
            new_filename = generate_output_filename(search_country_var.get(), keyword_var.get())
            output_file_var.set(new_filename)
            # Update preview showing just the filename
            preview = f"→ {os.path.basename(new_filename)}"
            filename_preview_var.set(preview)
        except Exception as e:
            logging.warning(f"Error updating filename: {e}")
            filename_preview_var.set("→ Error generating filename")
    
    def toggle_auto_filename():
        """Toggle between auto and manual filename modes"""
        if auto_filename_var.get():
            # Switching to auto mode - generate filename
            update_output_filename()
        else:
            # Switching to manual mode - clear preview
            filename_preview_var.set("Manual filename mode")
    
    # Add trace to update filename when country or keyword changes
    search_country_var.trace('w', update_output_filename)
    keyword_var.trace('w', update_output_filename)
    
    # Initialize preview on startup
    update_output_filename()

    tk.Label(root, text="Search Country:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=search_country_var, width=40).grid(row=0, column=1, padx=5, pady=5)
    tk.Label(root, text="Keyword:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=keyword_var, width=40).grid(row=1, column=1, padx=5, pady=5)
    tk.Label(root, text="Output Excel File:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=output_file_var, width=40).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=lambda: output_file_var.set(
        filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    )).grid(row=2, column=2, padx=5, pady=5)
    
    # Auto-filename checkbox and preview
    tk.Checkbutton(root, text="Auto-generate filename", 
                   variable=auto_filename_var,
                   command=toggle_auto_filename).grid(row=2, column=3, padx=5, pady=5, sticky="w")
    filename_preview_label = tk.Label(root, textvariable=filename_preview_var, 
                                     fg="gray", font=("Arial", 8))
    filename_preview_label.grid(row=2, column=1, sticky="w", pady=(25,0))
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

    # === SIMPLE FILTER CONFIGURATION ===
    tk.Label(root, text="═══ Filter Requirements ═══", font=("Arial", 10, "bold")).grid(row=10, column=0, columnspan=3, pady=(10,0))
    
    # Location Requirements
    require_remote_var = tk.BooleanVar(value=True)
    require_visa_var = tk.BooleanVar(value=True)
    require_skills_var = tk.BooleanVar(value=True)
    location_logic_var = tk.StringVar(value="OR")  # OR means "Remote OR Visa is fine"
    
    tk.Label(root, text="Location Requirements:").grid(row=11, column=0, sticky="e", padx=5, pady=2)
    location_frame = tk.Frame(root)
    location_frame.grid(row=11, column=1, sticky="w", padx=5, pady=2)
    
    tk.Checkbutton(location_frame, text="Match Remote Jobs", variable=require_remote_var).grid(row=0, column=0, sticky="w")
    tk.Checkbutton(location_frame, text="Match Visa Sponsorship Jobs", variable=require_visa_var).grid(row=0, column=1, sticky="w", padx=(20,0))
    
    tk.Label(location_frame, text="Logic:").grid(row=0, column=2, padx=(20,5), sticky="e")
    location_logic_combo = tk.OptionMenu(location_frame, location_logic_var, "OR", "AND")
    location_logic_combo.config(width=5)
    location_logic_combo.grid(row=0, column=3, sticky="w")
    
    # Skills Requirement
    tk.Label(root, text="Skills Requirement:").grid(row=12, column=0, sticky="e", padx=5, pady=2)
    tk.Checkbutton(root, text="Require Technical Skills (Anaplan/SAP/Planning)", variable=require_skills_var).grid(row=12, column=1, sticky="w", padx=5, pady=2)
    
    # Block Remote Prohibited
    block_remote_prohibited_var = tk.BooleanVar(value=False)
    tk.Label(root, text="Exclusions:").grid(row=13, column=0, sticky="e", padx=5, pady=2)
    tk.Checkbutton(root, text="Block jobs that prohibit remote work", variable=block_remote_prohibited_var).grid(row=13, column=1, sticky="w", padx=5, pady=2)

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
            "repetitive_parsing": repetitive_parsing_var.get(),
            "require_remote": require_remote_var.get(),
            "require_visa": require_visa_var.get(),
            "require_skills": require_skills_var.get(),
            "location_logic": location_logic_var.get(),
            "block_remote_prohibited": block_remote_prohibited_var.get()
        }
        if not config["output_file_path"]:
            messagebox.showerror("Ошибка", "Укажите путь для сохранения Excel файла.")
            return
        root.destroy()
        start_scraper_thread(config)

    tk.Button(root, text="Start Scraper", command=on_start, bg="green", fg="white").grid(row=14, column=0, columnspan=3, pady=10)
    root.mainloop()

if __name__ == "__main__":
    create_gui()
