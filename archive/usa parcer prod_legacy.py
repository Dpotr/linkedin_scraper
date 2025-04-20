import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
import math
import requests
from openpyxl import load_workbook
import matplotlib.pyplot as plt
import io
import base64
from langdetect import detect, LangDetectException

# Параметры настройки
TELEGRAM_BOT_TOKEN = "7690052120:AAHewK4ztdFw7y-iCApCmRMkCwz9inLLkfI"
TELEGRAM_CHAT_ID = "1908191"

# Параметры пути
CHROMEDRIVER_PATH = r"C:\selenium\chromedriver.exe"
CHROME_PROFILE_PATH = r"C:\Users\potre\SeleniumChromeProfile"
EXCEL_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies USA.xlsx"
OUTPUT_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies_usa_remote.xlsx"

# Параметры поиска
SEARCH_COUNTRY = "United States"
NO_RELOCATION_REQUIREMENTS = [
    "no relocation support", "we do not provide relocation", "no visa sponsorship", 
    "relocation not provided", "visa sponsorship unavailable", "relocation assistance not offered", 
    "visa sponsorship not included", "no relocation assistance", "we are unable to sponsor visas", 
    "visa sponsorship not possible", "local applicants only", "we cannot provide relocation"
]
REMOTE_REQUIREMENTS = [
    "remote", "work from home", "fully remote", "telecommute", "telecommuting", "remote work", "remote position"
]

# Функция отправки сообщений через Telegram-бота
def send_telegram_message(message, chart_image=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Найдено соответствие, сообщение отправлено в Telegram.")
        else:
            print(f"Ошибка при отправке сообщения: {response.text}")
    except Exception as e:
        print(f"Ошибка при подключении к Telegram: {e}")

    if chart_image:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {"photo": chart_image}
        data = {"chat_id": TELEGRAM_CHAT_ID}
        try:
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                print("График отправлен в Telegram.")
            else:
                print(f"Ошибка при отправке графика: {response.text}")
        except Exception as e:
            print(f"Ошибка при подключении к Telegram для отправки графика: {e}")

# Функция для извлечения текста из файла Excel
def get_excel_summary(file_path, running_time_minutes):
    try:
        workbook = load_workbook(file_path)
        sheet = workbook.active
        summary = []
        summary.append(f"Running time, min: {running_time_minutes:.2f}")
        summary.append(f"{sheet['K1'].value} {sheet['L1'].value}")
        summary.append(f"{sheet['M1'].value} {sheet['N1'].value}")
        summary.append(f"{sheet['P1'].value} {sheet['Q1'].value}")
        summary.append(f"{sheet['S1'].value} {sheet['T1'].value}")
        summary.append(f"{sheet['V1'].value} {sheet['W1'].value}")
        return "\n".join(summary)
    except Exception as e:
        print(f"Ошибка при извлечении данных из Excel: {e}")
        return ""

# Функция для создания P-Chart графика
def create_p_chart(results):
    df = pd.DataFrame(results)
    if len(df) < 2:
        return None

    # Рассчитываем разницу между записями
    df["Elapsed Time (s)"] = df["Elapsed Time (s)"].astype(float)
    df["Time Difference (s)"] = df["Elapsed Time (s)"].diff()
    time_differences = df["Time Difference (s)"][1:].tail(50)  # Используем последние 50 записей, исключаем первую строку
    avg_time_diff = time_differences.mean()

    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(time_differences.index, time_differences, marker='o', linestyle='-', color='b', label='Time Difference (s)')
    plt.axhline(y=avg_time_diff, color='r', linestyle='--', label=f'Average Time Difference ({avg_time_diff:.2f}s)')
    plt.fill_between(time_differences.index, avg_time_diff, time_differences, where=(time_differences > avg_time_diff), color='red', alpha=0.1)
    plt.fill_between(time_differences.index, avg_time_diff, time_differences, where=(time_differences < avg_time_diff), color='green', alpha=0.1)
    plt.xlabel('Company Index')
    plt.ylabel('Time Difference (s)')
    plt.title('P-Chart: Time Difference between Companies (Last 50)')
    plt.legend()
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# Настройки Chrome
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument("profile-directory=Default")
options.add_argument("--disable-webrtc")  # Отключение WebRTC для предотвращения ошибки stun.l.google.com
options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")  # Отключение WebRTC через дополнительные настройки
options.add_argument("--disable-udp")  # Отключение UDP-сокетов для избежания ошибок
options.add_argument("--log-level=3")  # Установить уровень логирования на Error
options.add_argument("--disable-logging")  # Отключение логирования
options.add_argument("--v=0")  # Минимизация количества логов

# Запуск WebDriver с использованием профиля
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# Запуск счётчика времени
start_time = time.perf_counter()

# Шаг 1: Открыть страницу авторизации LinkedIn
driver.get("https://www.linkedin.com/login")
print("Пожалуйста, выполните вход вручную...")
time.sleep(5)

# Проверка входа
if "feed" in driver.current_url or "linkedin.com" in driver.current_url:
    print("Вход выполнен успешно, продолжаем...")
else:
    print("Проверьте, выполнен ли вход корректно.")

# Шаг 2: Загрузка компаний из Excel
try:
    companies = pd.read_excel(EXCEL_FILE_PATH)
    print("Файл успешно загружен.")
    print(companies.head())
except FileNotFoundError:
    print(f"Файл {EXCEL_FILE_PATH} не найден. Проверьте путь и название файла.")
    exit()

results = []

# Функция для расчётов и записи в файл
def save_results_to_file_with_calculations(results, output_file, total_companies, elapsed_time):
    df_results = pd.DataFrame(results)
    true_count = sum(any(value is True for key, value in row.items() if key not in ["Elapsed Time (s)", "Job URL"]) for _, row in df_results.iterrows())
    ratio = true_count / len(df_results) if len(df_results) > 0 else 0
    processed_companies = len(df_results)
    remaining_companies = total_companies - processed_companies
    avg_time_per_company = elapsed_time / processed_companies if processed_companies > 0 else 0
    remaining_hours = remaining_companies * avg_time_per_company / 3600 if avg_time_per_company > 0 else 0
    remaining_minutes = remaining_hours * 60

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_results.to_excel(writer, index=False, sheet_name="Results")
        workbook = writer.book
        worksheet = writer.sheets["Results"]

        # Запись данных в ячейки
        worksheet["K1"] = "RATIO:"
        worksheet["L1"] = f"{ratio:.1%}"  # Процент с 1 знаками
        worksheet["M1"] = "Left hours:"
        worksheet["N1"] = f"{remaining_hours:.1f}"  # Часы
        worksheet["P1"] = "Left minutes:"
        worksheet["Q1"] = f"{remaining_minutes:.2f}"  # Минуты

        # Новые поля
        worksheet["S1"] = "Checked companies:"
        worksheet["T1"] = processed_companies  # Проверенные компании
        worksheet["V1"] = "Remaining for check companies:"
        worksheet["W1"] = remaining_companies  # Оставшиеся компании

    print(f"Результаты временно сохранены в файл: {output_file}")

# Шаг 3: Поиск вакансий для каждой компании
for i, company in enumerate(companies['Company Name'], start=1):
    best_result = {
        "Company": company,
        "Visa Sponsorship or Relocation": False,
        "Anaplan": False,
        "SAP APO": False,
        "Planning": False,
        "No Relocation Support": False,
        "Remote": False,
        "Already Applied": False,
        "Job URL": None,
        "Elapsed Time (s)": 0
    }
    try:
        print(f"Поиск компании: {company}")

        # Переход на страницу поиска вакансий
        driver.get("https://www.linkedin.com/jobs/search/")
        time.sleep(3)

        # Ожидание поля поиска
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@class='jobs-search-box__text-input jobs-search-box__keyboard-text-input jobs-search-global-typeahead__input']")
        ))

        # Ввод страны в поле поиска
        country_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[@class='jobs-search-box__text-input jobs-search-box__text-input--with-clear']")
        ))
        country_box.clear()
        country_box.send_keys(SEARCH_COUNTRY)
        country_box.send_keys(Keys.RETURN)
        time.sleep(2)

        # Ввод названия компании
        search_box.clear()
        search_box.send_keys(company)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)

        # Поиск вакансий
        job_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        print(f"Найдено вакансий по компании: {len(job_listings)}")

        for job in job_listings:
            try:
                # Извлечение названия компании
                job_company_name = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle span").text.strip()
                try:
                    job_title = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title span").text.strip()
                except:
                    try:
                        job_title = job.find_element(By.CSS_SELECTOR, ".job-card-list__title").text.strip()
                    except:
                        job_title = "Title not found"

                print(f"Название компании в карточке: '{job_company_name}', из списка: '{company}'")

                if company.lower().strip() not in job_company_name.lower().strip():
                    print(f"Вакансия не относится к компании {company}. Пропускаем.")
                    continue

                # Кликаем на вакансию
                job.click()
                time.sleep(1)

                # Извлечение описания вакансии
                job_description_element = driver.find_element(By.CLASS_NAME, "jobs-box__html-content")
                job_description = job_description_element.get_attribute("innerText").lower()
                try:
                    detected_language = detect(job_description)
                except LangDetectException:
                    detected_language = "unknown"
                
                if "transport" in job_description:
                    print(f"Найдено слово 'Transport' в описании вакансии для компании {company}.")
                    
                job_url = driver.current_url

                # Проверка ключевых слов
                visa_or_relocation = any(keyword in job_description for keyword in [
                    "we provide relocation", "relocation assistance", "relocation support", "we sponsor visas", 
                    "visa sponsorship available", "work visa sponsorship", "relocation package", "we support relocation", 
                    "visa sponsorship provided", "relocation offered", "visa and relocation assistance", 
                    "international relocation", "relocation and visa support"
                ])
                anaplan_found = any(keyword in job_description for keyword in [
                    "anaplan", "anaplan model builder", "anaplan planning", "anaplan developer", "anaplan consultant", 
                    "anaplan architect", "anaplan implementation", "anaplan solution", "anaplan support", "anaplan admin", 
                    "connected planning", "anaplan integration"
                ])
                sap_apo_found = any(keyword in job_description for keyword in [
                    "sap snp", "sap apo", "sap pp/ds", "sap scm", "sap supply planning", "sap advanced planning and optimization", 
                    "sap production planning", "sap demand planning", "sap distribution planning", "sap key user", 
                    "sap supply chain management"
                ])
                planning_found = any(keyword in job_description for keyword in [
                    "supply planning", "distribution requirements planning", "inventory planning", "production planning", 
                    "demand planning", "material requirements planning", "capacity planning", "supply chain planning", 
                    "logistics planning", "operations planning", "master production scheduling", "forecasting", "s&op", 
                    "sales and operations planning", "warehouse planning", "network planning", "procurement planning"
                ])
                no_relocation_found = any(keyword in job_description for keyword in NO_RELOCATION_REQUIREMENTS)
                remote_found = any(keyword in job_description for keyword in REMOTE_REQUIREMENTS)
                already_applied = any(keyword in job_description for keyword in [
                    "applied", "see application", "you have already applied", "already submitted", "previously applied"
                ])

                # Найденные ключевые слова
                matched_keywords = [
                    keyword for keyword in NO_RELOCATION_REQUIREMENTS + REMOTE_REQUIREMENTS + [
                        "we provide relocation", "relocation assistance", "relocation support", "we sponsor visas", 
                        "visa sponsorship available", "work visa sponsorship", "relocation package", "we support relocation", 
                        "visa sponsorship provided", "relocation offered", "visa and relocation assistance", 
                        "international relocation", "relocation and visa support", "supply planning", 
                        "distribution requirements planning", "inventory planning", "production planning", "demand planning", 
                        "material requirements planning", "capacity planning", "supply chain planning", "logistics planning", 
                        "operations planning", "master production scheduling", "forecasting", "s&op", 
                        "sales and operations planning", "warehouse planning", "network planning", "procurement planning", 
                        "anaplan", "anaplan model builder", "anaplan planning", "anaplan developer", "anaplan consultant", 
                        "anaplan architect", "anaplan implementation", "anaplan solution", "anaplan support", "anaplan admin", 
                        "connected planning", "anaplan integration", "sap snp", "sap apo", "sap pp/ds", "sap scm", 
                        "sap supply planning", "sap advanced planning and optimization", "sap production planning", 
                        "sap demand planning", "sap distribution planning", "sap key user", "sap supply chain management"
                    ] if keyword in job_description
                ]

                # Обновление лучшего результата для компании
                current_result = {
                    "Company": company,
                    "Visa Sponsorship or Relocation": visa_or_relocation,
                    "Anaplan": anaplan_found,
                    "SAP APO": sap_apo_found,
                    "Planning": planning_found,
                    "No Relocation Support": no_relocation_found,
                    "Remote": remote_found,
                    "Already Applied": already_applied,
                    "Job URL": job_url,
                    "Elapsed Time (s)": round(time.perf_counter() - start_time, 2)
                }

                # Определяем, является ли текущий результат лучшим
                current_true_count = sum(current_result[key] is True for key in ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "Remote"])
                best_true_count = sum(best_result[key] is True for key in ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "Remote"])

                if current_true_count > best_true_count or (current_true_count == best_true_count and no_relocation_found):
                    best_result = current_result

                # Отправка сообщений в Telegram для каждой вакансии, кроме тех, которые имеют только No Relocation Support или Remote без других критериев, или если уже был отклик
                found_criteria = [key for key, value in current_result.items() if value is True and key not in ["Company", "Already Applied", "Job URL", "Elapsed Time (s)"]]
                if not already_applied:
                    if "Remote" in found_criteria and len(found_criteria) <= 1:
                        continue  # Пропускаем, если только Remote без других критериев
                    if ("No Relocation Support" in found_criteria and len(found_criteria) > 1) or ("Remote" in found_criteria and len(found_criteria) > 1) or ("No Relocation Support" not in found_criteria and found_criteria):
                        remaining_minutes = best_result.get("Elapsed Time (s)", 0) / 60
                        message = f"🔔 Найдена вакансия для компании <b>{company}</b> - <b>{job_title}</b>!\n"
                        message += f"Критерии: {', '.join(found_criteria)}\n"
                        message += f"Язык описания вакансии: {detected_language.upper()}\n\n"
                        message += f"Ссылка на вакансию: <a href='{job_url}'>{job_url}</a>\n\n"
                        message += get_excel_summary(OUTPUT_FILE_PATH, remaining_minutes)
                        message += f"\nKey word: '{matched_keywords}'"
                        chart_image = create_p_chart(results)
                        send_telegram_message(message, chart_image=chart_image)

            except Exception as e:
                print(f"Ошибка при обработке вакансии: {e}")
                continue

        # Добавление данных в результат для одной компании
        best_result["Elapsed Time (s)"] = round(time.perf_counter() - start_time, 2)
        results.append(best_result)

        if i % 1 == 0:
            save_results_to_file_with_calculations(results, OUTPUT_FILE_PATH, len(companies), round(time.perf_counter() - start_time, 2))

    except Exception as e:
        print(f"Ошибка для компании {company}: {e}")
        elapsed_time = round(time.perf_counter() - start_time, 2)
        results.append({
            "Company": company,
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

# Финальное сохранение
elapsed_time = round(time.perf_counter() - start_time, 2)
save_results_to_file_with_calculations(results, OUTPUT_FILE_PATH, len(companies), elapsed_time)

print(f"Финальные результаты сохранены в файл: {OUTPUT_FILE_PATH}")

# Завершение работы
driver.quit()
