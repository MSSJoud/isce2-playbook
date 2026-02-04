FROM python:3.11-bookworm

COPY requirements.txt .

RUN apt update && \
    apt install -y git gdal-bin libgdal-dev

RUN pip install --upgrade pip setuptools && \
    pip install -r requirements.txt
RUN pip install gdal==$(gdal-config --version)