FROM python:3.7
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN mkdir /code
RUN pip install --upgrade pip

COPY ./example/requirements.txt .
RUN pip install -r requirements.txt

COPY . /code
WORKDIR /code

CMD celery -E -A example.worker worker --loglevel=warn --concurrency=2
