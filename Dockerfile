FROM mcr.microsoft.com/playwright/python:v1.64.1-noble

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir python-telegram-bot requests playwright
RUN playwright install chromium

CMD ["python", "bot.py"]
