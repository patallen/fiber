FROM python:3.7
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
RUN pip install --upgrade pip

RUN mkdir /code

COPY ./fiber/requirements.txt /code/requirements.txt
RUN pip install -r ./code/requirements.txt

ADD . /code

RUN pip install -e /code/fiber

WORKDIR /code/fiber

CMD python ./fiber/app.py
