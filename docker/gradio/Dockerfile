FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Use a user-local install target to avoid write permission issues during build
ENV PYTHONUSERBASE=/app/.local
ENV PATH=/app/.local/bin:$PATH
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
COPY src/ ./src/
COPY data/ ./data/
EXPOSE 7860
# Run the gradio UI; ensure it listens on 0.0.0.0
CMD ["python3", "-u", "src/gradio_ui.py"]
