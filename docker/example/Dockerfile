FROM python:3.7
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

RUN mkdir /code
RUN pip install --upgrade pip

COPY ./example/requirements.txt .
RUN pip install -r requirements.txt

COPY . /code
WORKDIR /code

CMD FLASK_APP='./example/app.py' flask run -p5000 -h0.0.0.0


