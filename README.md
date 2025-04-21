# LinkedIn Scraper V 2.0

**LinkedIn Scraper** — это мощный инструмент для автоматизированного поиска, анализа и сбора вакансий с LinkedIn с поддержкой семантического поиска, аналитики и отправки результатов в Telegram.

---

## Changelog

Полный список изменений см. в файле [CHANGELOG.md](CHANGELOG.md)

- **v2.0 (2025-04-21):**
    - Новый Streamlit-дэшборд с интерактивными фильтрами (компании, вакансии, навыки), кнопками Select/Deselect All и облаком тегов (skills tag cloud)
    - Улучшенная аналитика: все графики строятся по отфильтрованным данным
    - Проверка дубликатов при экспорте в Google Sheets по ключу "Vacancy Title - Company"
    - Heatmap и облако тегов теперь используют колонку Skills
    - Оптимизация скорости и стабильности, улучшенные сообщения об ошибках
    - См. подробности в CHANGELOG.md
- **v2.1 (2025-04-21):**
    - Все этапы вакансий (Viewed, Filtered, Passed filters, TG message sent) логируются отдельными строками в основной вкладке Google Sheets, все колонки всегда заполнены
    - Добавлена колонка 'TG message sent' для отслеживания отправки уведомлений в Telegram
    - В дашборде Streamlit добавлен чекбокс для удаления дубликатов вакансий (по Company + Vacancy Title)
    - Вся аналитика и воронка строятся по колонке Stage из основного листа
    - Оптимизация под лимиты Google Sheets API (всё в одном листе)
    - См. подробности в CHANGELOG.md

---

## Возможности

- Поиск вакансий по ключевым словам (в том числе: удалёнка, Anaplan, SAP, планирование и др.)
- Семантический анализ описаний вакансий с помощью Sentence Transformers
- Сбор и анализ данных в Excel и Google Sheets
- Автоматическая отправка уведомлений и графиков в Telegram
- Графический интерфейс (Tkinter) для удобного запуска и настройки
- Поддержка различных сценариев фильтрации (релокация, удалёнка, опыт, навыки и пр.)
- Встроенные инструменты аналитики (графики распределения, p-chart, анализ навыков и "красных флагов", Streamlit dashboard)
- Гибкая настройка через параметры интерфейса

## Структура проекта

- `universal parser_new_preprod(semantic_catgpt).py` — основной скрипт с поддержкой семантического поиска (рекомендуется для использования)
- `universal parser_wo_semantic_claude.py` — версия скрипта без семантического поиска, но с расширенными аналитическими функциями
- `universal parser_wo_semantic_chatgpt.py` — облегчённая версия без семантики
- `streamlit_linkedin_scraper.py` — интерактивный дашборд аналитики (Streamlit)
- `archive/` — архивные или вспомогательные файлы
- `companies_usa_remote.xlsx` — пример выходного файла с результатами
- `README.md` — описание проекта
- `CHANGELOG.md` — история изменений

## Установка

1. **Клонируйте репозиторий:**
   ```sh
   git clone https://github.com/Dpotr/linkedin_scraper.git
   cd linkedin_scraper
   ```

2. **Создайте виртуальное окружение и активируйте его:**
   ```sh
   python -m venv venv
   venv\Scripts\activate    # для Windows
   ```

3. **Установите зависимости:**
   ```sh
   pip install -r requirements.txt
   ```
   или вручную:
   ```sh
   pip install pandas requests matplotlib openpyxl selenium langdetect undetected-chromedriver sentence-transformers streamlit wordcloud
   ```

4. **Скачайте и установите ChromeDriver**  
   [Инструкция](https://chromedriver.chromium.org/downloads)  
   Укажите путь до chromedriver в интерфейсе или настройках скрипта.

## Быстрый старт

1. Запустите основной скрипт:
   ```sh
   python "universal parser_new_preprod(semantic_catgpt).py"
   ```
2. Для аналитики — запустите дашборд:
   ```sh
   streamlit run streamlit_linkedin_scraper.py
   ```
3. В графическом интерфейсе укажите параметры поиска, путь к профилю Chrome, токен Telegram-бота, ID чата и другие опции.
4. Нажмите "Start Scraper".

## Конфигурация и безопасность

- Все параметры (страна, ключевые слова, путь к Excel, токен Telegram, путь к ChromeDriver и профилю) настраиваются через GUI.
- Для семантического поиска требуется интернет для загрузки модели Sentence Transformers (кэшируется на диск).
- **tg_config.json** и **google_sheets_credentials.json** — содержат приватные ключи и токены. **Никогда не выкладывайте их в публичный репозиторий!** Добавьте их в .gitignore, если делаете проект публичным.

## Выходные данные

- Результаты сохраняются в Excel-файл.
- В Telegram отправляются текстовые уведомления и аналитические графики (bar chart, p-chart, skills chart).

## Требования

- Python 3.8+
- Google Chrome и соответствующий ChromeDriver
- Аккаунт Telegram для получения уведомлений

## Безопасность

- Не храните свои токены и личные данные в публичных репозиториях!
- Добавьте файл `.gitignore` для исключения секретов, кэша, виртуальных окружений и выходных данных.

## Пример .gitignore

```
venv/
__pycache__/
*.pyc
*.xlsx
*.log
*.env
*.db
.DS_Store
archive/
tg_config.json
google_sheets_credentials.json
```

## Лицензия

MIT License
