import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
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
EXCEL_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies USA.xlsx"  # (не используется в этой версии)
OUTPUT_FILE_PATH = r"C:\Users\potre\OneDrive\LinkedIn_Automation\companies_usa_remote.xlsx"

# Параметры поиска
SEARCH_COUNTRY = "United States"
KEYWORD = "remote job"   # <-- Замените на нужное ключевое слово
NO_RELOCATION_REQUIREMENTS = [
    "no relocation support", "we do not provide relocation", "no visa sponsorship",
    "relocation not provided", "visa sponsorship unavailable", "relocation assistance not offered",
    "visa sponsorship not included", "no relocation assistance", "we are unable to sponsor visas",
    "visa sponsorship not possible", "local applicants only", "we cannot provide relocation"
]
REMOTE_REQUIREMENTS = [
    "remote", "work from home", "fully remote", "telecommute", "telecommuting", "remote work", "remote position"
]

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

def get_excel_summary(file_path, running_time_minutes):
    try:
        workbook = load_workbook(file_path)
        sheet = workbook.active
        summary = []
        summary.append(f"Running time, min: {running_time_minutes:.2f}")
        ###summary.append(f"{sheet['K1'].value} {sheet['L1'].value}")
        ###summary.append(f"{sheet['M1'].value} {sheet['N1'].value}")
        ###summary.append(f"{sheet['P1'].value} {sheet['Q1'].value}")
        summary.append(f"{sheet['S1'].value} {sheet['T1'].value}")
        ###summary.append(f"{sheet['V1'].value} {sheet['W1'].value}")
        return "\n".join(summary)
    except Exception as e:
        print(f"Ошибка при извлечении данных из Excel: {e}")
        return ""

def create_p_chart(results):
    df = pd.DataFrame(results)
    if len(df) < 2:
        return None

    df["Elapsed Time (s)"] = df["Elapsed Time (s)"].astype(float)
    df["Time Difference (s)"] = df["Elapsed Time (s)"].diff()
    time_differences = df["Time Difference (s)"][1:].tail(50)
    avg_time_diff = time_differences.mean()

    plt.figure(figsize=(10, 5))
    plt.plot(time_differences.index, time_differences, marker='o', linestyle='-', color='b', label='Time Difference (s)')
    plt.axhline(y=avg_time_diff, color='r', linestyle='--', label=f'Average Time Difference ({avg_time_diff:.2f}s)')
    plt.fill_between(
        time_differences.index,
        avg_time_diff,
        time_differences,
        where=(time_differences > avg_time_diff),
        color='red',
        alpha=0.1
    )
    plt.fill_between(
        time_differences.index,
        avg_time_diff,
        time_differences,
        where=(time_differences < avg_time_diff),
        color='green',
        alpha=0.1
    )
    plt.xlabel('Listing Index')
    plt.ylabel('Time Difference (s)')
    plt.title('P-Chart: Time Difference between Listings (Last 50)')
    plt.legend()
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument("profile-directory=Default")
options.add_argument("--disable-webrtc")
options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
options.add_argument("--disable-udp")
options.add_argument("--log-level=3")
options.add_argument("--disable-logging")
options.add_argument("--v=0")

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

start_time = time.perf_counter()

driver.get("https://www.linkedin.com/login")
print("Пожалуйста, выполните вход вручную...")
time.sleep(5)

if "feed" in driver.current_url or "linkedin.com" in driver.current_url:
    print("Вход выполнен успешно, продолжаем...")
else:
    print("Проверьте, выполнен ли вход корректно.")

results = []

def save_results_to_file_with_calculations(results, output_file, total_companies, elapsed_time):
    df_results = pd.DataFrame(results)
    true_count = sum(
        any(value is True for key, value in row.items() if key not in ["Elapsed Time (s)", "Job URL"])
        for _, row in df_results.iterrows()
    )
    ratio = true_count / len(df_results) if len(df_results) > 0 else 0
    processed_companies = len(df_results)
    ###remaining_companies = total_companies - processed_companies
    avg_time_per_company = elapsed_time / processed_companies if processed_companies > 0 else 0
    ###remaining_hours = remaining_companies * avg_time_per_company / 3600 if avg_time_per_company > 0 else 0
    ###remaining_minutes = remaining_hours * 60

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_results.to_excel(writer, index=False, sheet_name="Results")
        workbook = writer.book
        worksheet = writer.sheets["Results"]

        ###worksheet["K1"] = "RATIO:"
        ###worksheet["L1"] = f"{ratio:.1%}"
        ###worksheet["M1"] = "Left hours:"
        ###worksheet["N1"] = f"{remaining_hours:.1f}"
        ###worksheet["P1"] = "Left minutes:"
        ###worksheet["Q1"] = f"{remaining_minutes:.2f}"

        worksheet["S1"] = "Checked companies:"
        worksheet["T1"] = processed_companies
        ###worksheet["V1"] = "Remaining for check companies:"
        ###worksheet["W1"] = remaining_companies

    print(f"Результаты временно сохранены в файл: {output_file}")

# =========================
# Поиск по заданному KEYWORD
# =========================
try:
    print(f"Поиск по ключевому слову: {KEYWORD}")

    # Идём напрямую на страницу поиска (можно и вручную вводить страну + keyword)
    driver.get("https://www.linkedin.com/jobs/search/")
    time.sleep(3)

    wait = WebDriverWait(driver, 15)

    # Поле для ввода локации
    country_box = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//input[@class='jobs-search-box__text-input jobs-search-box__text-input--with-clear']")
    ))
    country_box.clear()
    country_box.send_keys(SEARCH_COUNTRY)
    country_box.send_keys(Keys.RETURN)
    time.sleep(2)

    # Поле для ввода ключевого слова
    search_box = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//input[@class='jobs-search-box__text-input jobs-search-box__keyboard-text-input jobs-search-global-typeahead__input']")
    ))
    search_box.clear()
    search_box.send_keys(KEYWORD)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)

    # Функция: собрать и обработать ВСЕ вакансии на текущей странице
    def parse_current_page():
        """Скроллим страницу вниз до упора и обходим все вакансии."""
        scroll_pause_time = 2
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        job_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
        print(f"На текущей странице найдено {len(job_listings)} вакансий.")

        best_result_for_page = {
            "Company": KEYWORD,
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

        for i, job in enumerate(job_listings, start=1):
            try:
                job_company_name = "Unknown Company"
                job_title = "Title not found"
                try:
                    job_company_name = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle span").text.strip()
                except:
                    pass

                try:
                    job_title = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title span").text.strip()
                except:
                    try:
                        job_title = job.find_element(By.CSS_SELECTOR, ".job-card-list__title").text.strip()
                    except:
                        pass

                print(f"Обработка вакансии №{i}: '{job_title}' / {job_company_name}")

                # Клик по карточке для раскрытия описания
                job.click()
                time.sleep(1)

                # Описание
                job_description_element = driver.find_element(By.CLASS_NAME, "jobs-box__html-content")
                job_description = job_description_element.get_attribute("innerText").lower()

                try:
                    detected_language = detect(job_description)
                except LangDetectException:
                    detected_language = "unknown"

                job_url = driver.current_url

                # Проверка ключевых слов
                visa_or_relocation = any(x in job_description for x in [
                    "we provide relocation", "relocation assistance", "relocation support", "we sponsor visas",
                    "visa sponsorship available", "work visa sponsorship", "relocation package", "we support relocation",
                    "visa sponsorship provided", "relocation offered", "visa and relocation assistance",
                    "international relocation", "relocation and visa support"
                ])
                anaplan_found = any(x in job_description for x in [
                    "anaplan", "anaplan model builder", "anaplan planning", "anaplan developer", "anaplan consultant",
                    "anaplan architect", "anaplan implementation", "anaplan solution", "anaplan support", "anaplan admin",
                    "connected planning", "anaplan integration"
                ])
                sap_apo_found = any(x in job_description for x in [
                    "sap snp", "sap apo", "sap pp/ds", "sap scm", "sap supply planning", "sap advanced planning and optimization",
                    "sap production planning", "sap demand planning", "sap distribution planning", "sap key user",
                    "sap supply chain management"
                ])
                planning_found = any(x in job_description for x in [
                    "supply planning", "distribution requirements planning", "inventory planning", "production planning",
                    "demand planning", "material requirements planning", "capacity planning", "supply chain planning",
                    "logistics planning", "operations planning", "master production scheduling", "forecasting", "s&op",
                    "sales and operations planning", "warehouse planning", "network planning", "procurement planning"
                ])
                no_relocation_found = any(x in job_description for x in NO_RELOCATION_REQUIREMENTS)
                remote_found = any(x in job_description for x in REMOTE_REQUIREMENTS)
                already_applied = any(x in job_description for x in [
                    "applied", "see application", "you have already applied", "already submitted", "previously applied"
                ])

                 # Собираем все найденные ключевые слова (для лога или анализа) - удаленный кусок
                matched_keywords = [
                kw for kw in (
                    NO_RELOCATION_REQUIREMENTS
                    + REMOTE_REQUIREMENTS
                    + [
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
                    ]
                )
                if kw in job_description
                ] #удаленный кусок тиут закончился 

                current_result = {
                    "Company": job_company_name, #тут было KEYWORD, но заменил, чтобы в эксель записывалось
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

                # Сравниваем с best_result_for_page
                current_true_count = sum(
                    current_result[k] is True
                    for k in ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "Remote"]
                )
                best_true_count = sum(
                    best_result_for_page[k] is True
                    for k in ["Visa Sponsorship or Relocation", "Anaplan", "SAP APO", "Planning", "Remote"]
                )
                if current_true_count > best_true_count or (current_true_count == best_true_count and no_relocation_found):
                    best_result_for_page = current_result

                # Логика отправки в Telegram
                found_criteria = [
                    k for k, val in current_result.items()
                    if val is True and k not in ["Company", "Already Applied", "Job URL", "Elapsed Time (s)"]
                ]
                if not already_applied:
                    # Пропускаем, если только Remote без других критериев
                    if "Remote" in found_criteria and len(found_criteria) <= 1:
                        continue
                    # Если есть хоть что-то ещё
                    if (
                        ("No Relocation Support" in found_criteria and len(found_criteria) > 1)
                        or ("Remote" in found_criteria and len(found_criteria) > 1)
                        or ("No Relocation Support" not in found_criteria and found_criteria)
                    ):
                        running_minutes = (time.perf_counter() - start_time) / 60
                        message = (
                            f"🔔 Найдена вакансия по ключевому слову <b>{KEYWORD}</b>\n"
                            f"Компания: <b>{job_company_name}</b>\n"
                            f"Вакансия: <b>{job_title}</b>\n\n"
                            f"Критерии: {', '.join(found_criteria)}\n"
                            f"Язык описания: {detected_language.upper()}\n\n"
                            f"Ссылка на вакансию: <a href='{job_url}'>{job_url}</a>\n\n"
                            + get_excel_summary(OUTPUT_FILE_PATH, running_minutes)
                            + f"\nKey word(s) found: {matched_keywords}"
                        )
                        chart_image = create_p_chart(results)
                        send_telegram_message(message, chart_image=chart_image)

            except Exception as e:
                print(f"Ошибка при обработке вакансии №{i}: {e}")
                continue

        # Добавляем лучший результат на этой странице
        best_result_for_page["Elapsed Time (s)"] = round(time.perf_counter() - start_time, 2)
        results.append(best_result_for_page)

    # Теперь перебираем страницы, кликая по номерам (1, 2, 3 ...)
    current_page = 1
    while True:
        print(f"=== Обработка страницы {current_page} ===")
        parse_current_page()
        # Сохраним промежуточный результат
        save_results_to_file_with_calculations(
            results,
            OUTPUT_FILE_PATH,
            total_companies=9999999,  # Можно поставить большое число
            elapsed_time=round(time.perf_counter() - start_time, 2)
        )

        # Пытаемся найти кнопку (или ссылку) следующей страницы
        # Вариант 1: кнопка с aria-label="Page N", где N = current_page+1
        next_page_number = current_page + 1
        next_button_xpath = f"//button[@aria-label='Page {next_page_number}']"
        # иногда бывает <li> или <span>, зависит от верстки:
        # "//li[@aria-label='Page {next_page_number}']"
        # "//button[contains(@aria-label,'Page {next_page_number}')]"

        next_buttons = driver.find_elements(By.XPATH, next_button_xpath)
        if not next_buttons:
            print(f"Страница {next_page_number} не найдена. Значит, достигли конца или LinkedIn не показывает дальше.")
            break

        # Кликаем, переходим на следующую страницу
        next_buttons[0].click()
        current_page += 1
        time.sleep(3)

    # В конце — финальная запись (хотя мы уже писали внутри цикла)
    print("Пагинация завершена. Сохраняем финал.")
    save_results_to_file_with_calculations(
        results,
        OUTPUT_FILE_PATH,
        total_companies=9999999,
        elapsed_time=round(time.perf_counter() - start_time, 2)
    )

except Exception as e:
    print(f"Глобальная ошибка при поиске по ключевому слову {KEYWORD}: {e}")
    elapsed_time = round(time.perf_counter() - start_time, 2)
    results.append({
        "Company": KEYWORD,
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
    save_results_to_file_with_calculations(
        results,
        OUTPUT_FILE_PATH,
        total_companies=9999999,
        elapsed_time=elapsed_time
    )

finally:
    print(f"Финальные результаты сохранены в файл: {OUTPUT_FILE_PATH}")
    driver.quit()
