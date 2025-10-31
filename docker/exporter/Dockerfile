FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Use a user-local install to avoid writing to /usr/local during build
ENV PYTHONUSERBASE=/app/.local
ENV PATH=/app/.local/bin:$PATH
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
COPY src/ ./src/
COPY data/ ./data/
EXPOSE 8000
CMD ["python3", "-u", "src/metrics_exporter.py"]
