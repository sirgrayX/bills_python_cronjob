import os
import pandas as pd
import numpy
import utils

from datetime import datetime, timedelta
from xhtml2pdf import pisa
from flask import Flask, Response, render_template, request
from dotenv import load_dotenv

from warnings import filterwarnings
filterwarnings("ignore")

# инициализация приложения flask
app = Flask(__name__)

# подтянуть переменные окружения
load_dotenv('.env')
app.config.from_pyfile('settings.py')


# параметры s3-хранилища
ENDPOINT_URL = app.config.get("ENDPOINT_URL")
AWS_ACCESS_KEY_ID = app.config.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = app.config.get("AWS_SECRET_ACCESS_KEY")
BUCKET = app.config.get("BUCKET")

# URL Ликарда
IP_SERVER = app.config.get("IP_SERVER")
PORT = app.config.get("PORT")
WEB_SERVICE = app.config.get("WEB_SERVICE")
METHOD = app.config.get("METHOD")

months_names = {
    '01' : "Январь",
    '02' : "Февраль",
    '03' : "Март",
    '04' : "Апрель",
    '05' : "Май",
    '06' : "Июнь",
    '07' : "Июль",
    '08' : "Август",
    '09' : "Сентябрь",
    '10' : "Октябрь",
    '11' : "Ноябрь",
    '12' : "Декабрь"
}

def get_month(dic, value):
    for k, v in dic.items():
        if value == v:
            return f".{k}."

@app.route("/")
def main_page():
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
        df_names['folders'] = df_names['bills'].str.split('/', expand=True)[0]
        folders = df_names['folders'].unique()
    else:
        folders = []
    return render_template('cards.html', folders=folders)
    
@app.route("/<card_number>")
def years_list(card_number):
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
        df_names['names'] = df_names['bills'].str.split('/', expand=True)[1]
        df_names['date_bill'] = df_names['names'].str.split('_', expand=True)[1]
        df_names['year'] = df_names['date_bill'].str.split('.', expand=True)[2]
        years = df_names['year'].unique()
    else:
        years = ["Файлы не обнаружены"]
    return render_template('years.html', folders=years, card_number=card_number)


@app.route("/<card_number>/<year>")
def months_list(card_number, year):
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
        df_names['names'] = df_names['bills'].str.split('/', expand=True)[1]
        bills_at_card = df_names[df_names['names'].apply(lambda x: x.split('_')[0] == card_number)]['names']
        dates = bills_at_card.str.split('_', expand=True)[1]
        months = []
        for date in dates:
            ((year in date) == False) or months.append(months_names[date.split('.')[1]])
        months = numpy.unique(months)
    else:
        months = ["Файлы не обнаружены"]
    months = sorted(months)
    return render_template('months.html', 
                            folders=months, 
                            card_number=card_number, 
                            year=year
    )

@app.route("/<card_number>/<year>/<month>")
def bills_list(card_number, year, month):
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
        df_names['names'] = df_names['bills'].str.split('/', expand=True)[1]
        bills_in_folder = df_names[
            (df_names['names'].str.startswith(card_number)) & \
            (df_names['names'].apply(lambda x: get_month(months_names, month) in x.split('_')[1])) & \
            (df_names['names'].apply(lambda x: f".{year}" in x))
        ]['names']
    else:
        bills_in_folder = ["Файлы не обнаружены"]
    return render_template('bills.html', 
                            bills=bills_in_folder, 
                            card_number=card_number, 
                            year=year, 
                            month=month
    )

@app.route("/download/<bill_name>", methods=['GET'])
def download_bill(bill_name):
    s3_session = utils.make_s3_session(ENDPOINT_URL, 
                                       AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    file = s3_session.get_object(Bucket=BUCKET, 
                                 Key=f"{bill_name.split('_')[0]}/{bill_name}")
    return Response(
        file['Body'].read(),
        mimetype='text/plain',
        headers={"Content-Disposition": f"attachment;filename={bill_name}"}
    )
    
    
    
@app.errorhandler(404)
def page_not_found(e):
    return "Страница не найдена"
    
@app.errorhandler(500)
def page_not_found(e):
    return "Неправильный URL"
