FROM alpine:3.19.1

RUN apk update

RUN apk add vim curl

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip

RUN pip3 install --no-cache --upgrade pip setuptools

RUN mkdir -p /home/transcendance

# RUN python3 -m venv .venv

# RUN source .venv/bin/activate

COPY ./requirements.txt /

RUN pip3 install --no-cache-dir -r requirements.txt

RUN cd /home/transcendance && django-admin startproject projectName 

WORKDIR /home/transcendance/projectName

RUN python3 manage.py startapp channels_demo

RUN python3 manage.py makemigrations

RUN python3 manage.py migrate

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]