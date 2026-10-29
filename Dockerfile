FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir python-telegram-bot requests playwright
CMD ["python", "bot.py"]