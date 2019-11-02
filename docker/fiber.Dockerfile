FROM python:3.7
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN pip install poetry

COPY pyproject.toml .
RUN poetry install
RUN rm pyproject.toml

COPY . /

RUN echo "About to run FiberNGN"
ENTRYPOINT poetry run python ./fiber/app.py
