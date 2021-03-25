FROM python:3.8.0-slim
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install gcc -y && apt-get clean
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY . /app
