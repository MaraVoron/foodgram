FROM python:3.11-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static /app/media

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py load_data && gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 3"]