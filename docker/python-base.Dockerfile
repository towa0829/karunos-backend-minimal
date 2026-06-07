FROM python:3.12-slim

WORKDIR /app

COPY shared/requirements.txt /tmp/shared-requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/shared-requirements.txt
