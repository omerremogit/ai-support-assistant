# Container for the prototype. Used by Railway (or any host that runs Docker).
FROM python:3.12-slim

WORKDIR /srv
COPY prototype/requirements.txt prototype/requirements.txt
RUN pip install --no-cache-dir -r prototype/requirements.txt

# The app reads the test customers and the automation matrix from the repo
COPY prototype prototype
COPY tests/mock_customers.json tests/mock_customers.json
COPY docs/automation_matrix.csv docs/automation_matrix.csv

WORKDIR /srv/prototype
ENV PYTHONUNBUFFERED=1
# The host sets PORT; 8000 is the fallback for running locally
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
