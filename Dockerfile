FROM python:3.9.2-slim

RUN mkdir /src
WORKDIR /src
ADD . /src/

COPY ./src/requirements.txt requirements.txt
COPY ./src/utils.py utils.py
COPY ./src/bills_job.py bills_job.py
COPY ./src/courier-new-cyr.ttf courier-new-cyr.ttf
COPY ./src/Список_активных_ТК.csv Список_активных_ТК.csv 
COPY ./src/agat_logistic.pem agat_logistic.pem
COPY ./src/env .env

RUN pip install --upgrade pip
RUN pip install -U setuptools
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "bills_job.py"]