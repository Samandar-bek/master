FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 10000

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:10000"]