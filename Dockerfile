FROM python:latest

ENV CPATH=/usr/local/include/python3.8

RUN mkdir /sharky
WORKDIR /sharky

ADD requirements.txt /sharky/requirements.txt
RUN pip install --no-cache-dir --src /usr/src -r requirements.txt

ADD . /sharky
