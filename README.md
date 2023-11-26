# Репозиторий для задачи Suggest Service

## Запуск сервиса

Команда запуска:

`bash run.sh`

## Тесты

Команда запуска:

`pytest .`

Запуск с подробным выводом (ошибки и prints):

`pytest -svv .`

Запуск одного теста (если нужно тестировать конкретную функцию):

`pytest -svv tests/test_app.py::test_suggestions_recall`

## Pylint

Команда запуска:

`pylint app.py`
