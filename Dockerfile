FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    zlib1g-dev \
    rustc \
    cargo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD . /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential rustc cargo # to remove build dependencies, helps to reduce size.

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
