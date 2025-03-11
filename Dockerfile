FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN pip install poetry

WORKDIR /app

COPY . .

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "-m", "energy_monitor_server"]
