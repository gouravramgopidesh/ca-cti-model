FROM python:3.12-slim
WORKDIR /work
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/work
CMD ["python", "activity-13.1/failover.py"]
