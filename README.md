# Интернет-магазин цветов и конструктор букетов

Проект по учебной практике: сайт цветочного магазина на Django.

## Как запустить

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
база пустая: букеты, сорта, упаковку, интервалы доставки и тестовые заказы надо добавить
через админку по адресу /admin/.
