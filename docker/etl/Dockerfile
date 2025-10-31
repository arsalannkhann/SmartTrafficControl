FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install into a user-writable location to avoid read-only filesystem issues during build
ENV PYTHONUSERBASE=/app/.local
ENV PATH=/app/.local/bin:$PATH
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
COPY src/ ./src/
COPY data/ ./data/
# ETL runs once on startup; if you want it to run periodically, wrap with a scheduler
CMD ["python3", "-u", "src/etl_pipeline.py"]
