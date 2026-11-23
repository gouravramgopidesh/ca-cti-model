FROM python:3.11-slim
WORKDIR /lab
ENV PYTHONUNBUFFERED=1 MPLBACKEND=Agg
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-u", "-c", "import time; time.sleep(10**9)"]
