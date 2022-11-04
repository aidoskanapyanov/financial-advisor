FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root

WORKDIR /financial-advisor

COPY src src

CMD [ "python", "src/app.py" ]