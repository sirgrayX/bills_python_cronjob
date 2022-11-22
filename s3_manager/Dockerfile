FROM python:3.9.2-slim

RUN mkdir /s3_manager
WORKDIR /s3_manager
ADD . /s3_manager/
ADD ./static /s3_manager/static/
ADD ./templates /s3_manager/templates/

RUN pip install --upgrade pip
RUN pip install -U setuptools
RUN pip install -r requirements.txt

EXPOSE 8888
CMD ["gunicorn"  , "-b", "0.0.0.0:8888", "app:app"]