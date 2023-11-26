FROM python:3.11-slim

RUN pip install srctag[embedding]

WORKDIR /app

COPY . .

CMD ["python", "main.py"]
