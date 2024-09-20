FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

# CMD [ "python", "-m", "streamlit, "run", "app.py" ]

CMD ["streamlit", "run", "entry_page.py"]