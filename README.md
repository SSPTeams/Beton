# Beton

**Beton** — проект для симуляции операций с заводами, клиентами и заказами. Проект включает в себя классы для описания сущностей, логику симуляции, генерацию тестовых данных и визуализацию результатов.

## Структура проекта


### Описание файлов

- **`classes.py`**: Содержит классы, описывающие основные сущности проекта.
  
- **`simulation.py`**: Реализует логику симуляции.
  
- **`main.py`**: Отвечает за чтение данных тесткейса и запуск симуляции.
  
- **`visualisation.py`**: На данный момент не работает; предназначен для визуализации результатов симуляции.
  
- **`generate_test_data.py`**: Генерирует тестовые данные на основе конфигурации, указанной в `config.json`.
  
- **`data/`**: Папка, содержащая тестовые данные. Каждая подпапка соответствует отдельному тестовому кейсу и имеет произвольное название (например, `case_2_2_2` для 2 заводов, 2 клиентов и 2 заказов).

## Описание тест-кейсов

Для создания и запуска тестового кейса выполните следующие шаги:

1. **Описание тест-кейса**:
   - Создайте подпапку внутри папки `data/`.
   - В этой подпапке создайте файл `config.json` (см. пример в `case_2_2_2`).

2. **Генерация тестовых данных**:
   - Запустите `generate_test_data.py` и введите название тестовой папки при запросе.

3. **Редактирование сгенерированных данных (при необходимости)**:
   - При необходимости вручную измените сгенерированные данные в той же папке тестового кейса.

## Запуск симуляции

1. **Запуск**:
   - Запустите `main.py` и введите название тестовой папки при запросе.

2. **Получение результатов**:
   - Результат симуляции будет сохранён в файле `result.json` внутри папки тестового кейса.

## TODO

1. **Сократить время работы**:
   - В данный момент используется полный перебор, одна симуляция занимает примерно 0.2 секунды. Это можно оптимизировать.

2. **Визуализация**:
   - Модуль `visualisation.py` пока не работает. Требуется доделать визуализацию результатов.

3. **Добавить чекеры**:
   - Реализовать проверки на непротиворечивость назначенных поездок.

4. **Добавить занятые изначально слоты в тестовые данные**:
   - Включить в тестовые данные уже занятые слоты.

5. **Добавить метрики**:
   - В данный момент учитывается только отклонение от плана. Необходимо добавить дополнительные метрики.

6. **Реализовать разумный выбор лучшего подходящего ТС и его маршрута**:
   - Сейчас выбирается первый возможный вариант. Нужно реализовать более интеллектуальный выбор.

7. **Добавить недостающие поля в данные**:
   - Например, `factory_id` и другие необходимые поля.
