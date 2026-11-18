# Интернет-магазин цветов и конструктор букетов

Учебный проект: сайт цветочного магазина на Django, вариант 9.

## Что внутри

| Папка | Что лежит |
| --- | --- |
| app/ | приложение: models.py (14 моделей), views.py, urls.py (28 маршрутов), forms.py (6 форм), admin.py, migrations/ |
| project/ | настройки проекта: settings.py, urls.py, wsgi.py, asgi.py |
| templates/ | base.html и 16 страниц, все расширяют base.html |
| static/css/style.css | все стили и медиазапросы, цвета и отступы в переменных :root |
| static/js/validation.js | проверка форм, живой поиск, корзина без перезагрузки, данные для аналитики |

## Как запустить

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

База и загруженные фото в репозиторий не попадают, они в .gitignore. После первого запуска
база пустая: букеты, сорта, упаковку, интервалы доставки и тестовые заказы надо добавить
через админку по адресу /admin/. Модели и связи уже готовы, миграция одна.

## Проверки

- HTML: 16 страниц, 0 ошибок (Nu HTML Checker, движок validator.w3.org).
- CSS: 0 ошибок, 26 предупреждений про переменные var().
- Lighthouse, мобильный профиль: Performance 98-99, Accessibility 100.
- Консоль браузера без ошибок, горизонтальной прокрутки нет на 360, 375, 768, 1024 и 1440 px.
- Скриншоты и отчеты проверок сдаются отдельно, в репозиторий не входят.
