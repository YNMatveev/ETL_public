FROM python:3.9-slim-buster

RUN apt-get update -y && apt-get upgrade

WORKDIR /etl

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY postgres_to_es .

CMD ["python3", "main.py"]