#!/usr/local/bin/python3.

import os
import requests
import utils
import boto3
import pandas as pd

from dotenv import dotenv_values
from datetime import datetime, timedelta
from xhtml2pdf import pisa

# скрыть системные оповещения;
from warnings import filterwarnings
filterwarnings('ignore')

# подгрузиить системные переменные;
config = dotenv_values(".env")

# параметры s3-хранилища
ENDPOINT_URL = config['ENDPOINT_URL']
AWS_ACCESS_KEY_ID = config['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = config['AWS_SECRET_ACCESS_KEY']
BUCKET = config['BUCKET']

# URL Ликарда
IP_SERVER = config['IP_SERVER']
PORT = config['PORT']
WEB_SERVICE = config['WEB_SERVICE']
METHOD = config['METHOD']

# параметры для запроса
url_licard = f"https://{IP_SERVER}:{PORT}/{WEB_SERVICE}/{METHOD}"
dateFrom = f"{(datetime.now() - timedelta(days=2)).date()}T19:00:00"
dateTo = f"{(datetime.now()).date()}T19:00:00"
maxRowsThreshold = 1_000_000
contractId = int(config['CONTRACT_ID'])

# задавать пути к файлам здесь;
path_to_cards_file = "Список_активных_ТК.csv"  # путь до файла с картами;

s3_session = utils.make_s3_session(ENDPOINT_URL, 
                                   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
names = []
if 'Contents' in s3_session.list_objects(Bucket=BUCKET):
    paginator = s3_session.get_paginator('list_objects')
    response_iterator = paginator.paginate(Bucket=BUCKET)
    for page in response_iterator:
        for key in page['Contents']:
            names.append(key['Key'])
df_names = pd.DataFrame({'bills' : names})
cards = pd.read_csv(path_to_cards_file)
if '1' in cards.columns[-1]:
    utils.request_to_licard(df_names, s3_session, url_licard, contractId, 
                      dateFrom, dateTo, maxRowsThreshold)
elif '2' in cards.columns[-1]:
    for card in cards.columns[0]:
        utils.request_to_licard(df_names, s3_session, url_licard, contractId, 
                          dateFrom, dateTo, maxRowsThreshold, card)
else:
    print("Проверьте указанный в файле параметр!")
    exit()
print(f"{datetime.now()} Выгрузка завершена!\n")
utils.delete_old_bills(s3_session)
