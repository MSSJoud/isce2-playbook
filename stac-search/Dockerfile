FROM python:3.11-bullseye

COPY requirements.txt .

RUN apt update && \
    apt install -y git

RUN pip install --upgrade pip setuptools && \
    pip install -r requirements.txt
