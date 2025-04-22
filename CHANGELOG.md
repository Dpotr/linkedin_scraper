# Changelog

## v2.3 (2025-04-22)

### Major Features & Improvements
- **Полная поддержка дат публикации LinkedIn:**
  - Автоматическое извлечение и преобразование любых форматов дат: "N days ago", "N hours ago", "N weeks ago", "Yesterday", "Today", "Just now".
  - Новая колонка `transformed publish date from description` в Google Sheets/Excel — всегда содержит нормализованную дату публикации в формате YYYY-MM-DD.
- **Надёжная прокрутка вакансий:**
  - Функция scroll_until_loaded теперь гарантирует, что на каждой странице будут обработаны все вакансии, даже если они догружаются с задержкой (ожидание появления новых карточек после каждого скролла).
  - Исключены ситуации, когда парсер видел только часть вакансий на первой или последующих страницах.
- **Улучшения стабильности и документации:**
  - Улучшена стабильность и читаемость кода.
  - Обновлены комментарии и документация по новым функциям.

## v2.2 (2025-04-21)

### Major Features & Improvements
- **Прозрачная логика мэтчинга и логирования:** Теперь для каждой вакансии логируются все этапы (Viewed, Filtered (criteria), Filtered (already applied), Passed filters, TG message sent) отдельными строками в Google Sheets/Excel. Все ключевые флаги (включая Remote Prohibited) фиксируются на каждом этапе.
- **Remote Prohibited**: Вакансии с этим флагом не отсекаются автоматически, а отмечаются для аналитики. Теперь ни одна релевантная вакансия (например, с визой/релокацией) не пропускается из-за наличия запрета на удалёнку.
- **Matched key words:** Для каждой вакансии сохраняется строка с совпавшими ключевыми словами.
- **README обновлён:** Подробно описана логика парсинга и выбора мэтчей, обновлены инструкции и требования.

### Minor
- Улучшена документация, исправлены мелкие баги.

## v2.1 (2025-04-21)

### Major Features & Improvements
- **Full logging of all job stages**: All stages (Viewed, Filtered, Passed filters, TG message sent) are now logged as separate rows in the main Google Sheets tab. All columns (including skills, flags, elapsed time, etc.) are always filled for every stage.
- **Column 'TG message sent'**: Added to log when a Telegram notification was sent for a vacancy.
- **Streamlit: Remove duplicates**: Added checkbox to show only unique vacancies (by Company + Vacancy Title) on all boards and analytics.
- **Stage-based analytics**: Dashboard funnel and analytics now use the main sheet and the 'Stage' column for all calculations.
- **Performance**: Logging and analytics now use a single worksheet, minimizing Google Sheets API quota issues.

### Minor
- Improved error handling, code cleanup, and documentation.

## v2.0 (2025-04-21)

### Major Features & Improvements
- **Streamlit Dashboard**: Добавлен современный интерактивный дашборд с аналитикой по вакансиям, компаниям и навыкам.
- **Фильтры**: Фильтры по компаниям, названиям вакансий и навыкам с кнопками "Select All"/"Deselect All" для удобного анализа любых срезов данных.
- **Облако навыков (Tag Cloud)**: Визуализация самых популярных навыков в виде облака слов.
- **Heatmap по навыкам и критериям**: Улучшена логика построения heatmap, теперь учитываются только реально встречающиеся навыки (Skills), а не слова из названия вакансии.
- **Проверка дубликатов при экспорте в Google Sheets**: Дубликаты определяются по ключу "Vacancy Title - Company" (а не по URL).
- **Оптимизация скорости**: Быстрый парсинг навыков, минимальная нагрузка на интерфейс.
- **Гибкая аналитика**: Все графики и облако тегов строятся по отфильтрованным данным, не мешая работе парсера в фоне.
- **Улучшенная обработка ошибок**: Более информативные сообщения при недостатке данных для построения графиков.

### Minor
- Мелкие исправления, улучшена читаемость кода, обновлены зависимости.

---

## v1.x (до 2025-04-21)
- Базовый функционал парсинга, экспорта в Excel и Google Sheets, Telegram-уведомления, простая аналитика и фильтрация.
