FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y vim && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip && \
    pip install telethon && \
    pip install termcolor && \
    pip install python-telegram-bot

RUN adduser app
USER app

WORKDIR /app
