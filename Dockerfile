# 1. Python image tanlaymiz
FROM python:3.10-slim

# 2. Ishchi papkani belgilaymiz
WORKDIR /app

# 3. Kerakli paketlar uchun apt update va install
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. requirements.txtni nusxalash
COPY requirements.txt .

# 5. Python paketlarini o‘rnatish
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 6. Loyiha fayllarini nusxalash
COPY . .

# 7. Statik fayllarni collect qilish
RUN python manage.py collectstatic --noinput

# 8. Portni ochish (Render $PORT dan oladi)
EXPOSE 10000

# 9. Gunicorn orqali serverni ishga tushirish
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:10000"]
