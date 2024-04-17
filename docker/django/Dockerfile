FROM alpine:3.14

RUN apk update

RUN apk add vim curl

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip

RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip install django

WORKDIR /home
RUN mkdir test

WORKDIR /home/test

RUN python3 -m venv .venv

COPY ./requirements.txt /home/test

RUN pip install --no-cache-dir -r requirements.txt
