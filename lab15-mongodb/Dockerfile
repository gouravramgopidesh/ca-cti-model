FROM python:3.12-slim
WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/lab
CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
