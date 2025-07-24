FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/build_schema.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
