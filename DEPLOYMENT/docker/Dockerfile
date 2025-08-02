FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt || echo "No requirements"
COPY . .
CMD ["python", "main.py", "--help"]
