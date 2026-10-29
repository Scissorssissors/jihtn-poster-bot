FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app
COPY . /app

# Pin playwright to 1.49.0 so it matches the pre-installed browser perfectly
RUN pip install --no-cache-dir python-telegram-bot requests "playwright==1.49.0"

CMD ["python", "bot.py"]
