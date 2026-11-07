FROM python:3.12.0-slim-bookworm

WORKDIR /app

COPY . /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install -y git libgomp1 libpq-dev && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r /app/requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip

# Numeric, so that Kubernetes can check runAsNonRoot.
USER 10001:10001

# exec: fastapi must be PID 1 to receive SIGTERM and finish its requests.
CMD ["sh", "-c", "exec fastapi run /app/src/main.py --host \"${API_HOST-0.0.0.0}\" --port ${DOCKER_PORT:-8080}"]
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
# CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "src.main:app","--bind", "0.0.0.0:8080"]
# CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8080"]
# CMD ["/bin/bash"]
