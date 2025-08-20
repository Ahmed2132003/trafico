FROM python:3.10-slim-bullseye

WORKDIR /app

# تثبيت مكتبة SQLite والحزم المطلوبة
RUN apt-get update && apt-get install -y \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# جمع ملفات الـ static
RUN python manage.py collectstatic --noinput

# إنشاء startup.sh
RUN echo '#!/bin/bash\npython manage.py migrate\nexec gunicorn --bind :8000 trafico.wsgi:application' > startup.sh
RUN chmod +x startup.sh

EXPOSE 8000

ENTRYPOINT ["./startup.sh"]