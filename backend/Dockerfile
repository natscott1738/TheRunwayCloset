FROM python:3.11-slim

# prevent Python from writing pyc files & enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# install pip & dependencies
RUN pip install --upgrade pip

# install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project files
COPY . .

# gunicorn entrypoint
CMD ["gunicorn", "runway.wsgi:application", "--bind", "0.0.0.0:8001"]
