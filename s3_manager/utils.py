import os
import requests
import pandas as pd
import boto3
from datetime import datetime, timedelta
from xhtml2pdf import pisa


def make_s3_session(endpoint, key_id, secret_key):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret_key,
        use_ssl=True
    )
    return s3


def draw_bills(json_response, s3_session):
    transactions_json = json_response.json()
    transactions = transactions_json['getContractTransactionsRs']['getContractTransactionsPayload']['contractTransactions']
    # итерирование по списку транзакций по карте;
    for transaction in transactions:
        if ("Покупка" in transaction['transType']):
            date_check, time_check = transaction['transDate'].split('T') # разделение времени и даты транзакции;
            yyyy, mm, dd = date_check.split('-')                         # разделение компонент времени;
            date_check = f"{dd}.{mm}.{yyyy}"
            if len(time_check.split(':')) < 3:
                time_check += (':00')
            hh, mm, ss = time_check.split(':')
            time_check_name = f"{hh}.{mm}.{ss}"
           # path_card = os.path.join(BASE_DIR, transaction['cardNumberOut'])  # путь до директории с чеками по карте;
           # if not os.path.exists(path_card):                             # проверка существования директории;
           #     os.mkdir(path_card)
           # формирование файла для чека; 
            html_pattern = "<table align='center' class='basic-table card-table' id='echeques-report' cellpadding='2' cellspacing='0' border='0'>" \
                           "    <tbody>" \
                           "        <tr><th align='center' bgcolor='#d7d7d7'><b>Электронный терминальный чек</b></th></tr>" \
                          f"        <tr><td align='center' style='padding-top: 3px !important;'>{transaction['partnerName']}</td></tr>" \
                          f"        <tr><td align='center'>{transaction['outletName']}</td></tr>" \
                          f"        <tr><td align='left'><span class='colortext'>Адрес места расчётов:</span></td></tr>" \
                          f"        <tr><td >{transaction['region']}, {transaction['streetAddress']}</td></tr>" \
                          f"        <tr><td><span class='colortext'>Топливо</span>: {transaction['goodsName']}</td></tr>" \
                           "        <tr><td><span class='colortext'>Объем отгруженного топлива</span>:" \
                          f"        {transaction['quantity'] if (transaction['quantity'] - int(transaction['quantity'])) > 0 else int(transaction['quantity'])} " \
                          f"        {transaction['measureUnit']}</td></tr>" \
                           "        <tr><td>Цена определена договором</td></tr>" \
                          f"        <tr><td>{transaction['transType']}</td></tr>" \
                          f"        <tr><td><span class='colortext'>ТК</span>: {transaction['cardNumberOut']}</td></tr>" \
                          f"        <tr><td>{date_check}&nbsp;{time_check}&nbsp;</td></tr>" \
                           "        <tr style='background-color: black; color: white;'>" \
                           "            <td align='center' valign='middle'>ОДОБРЕНО (RC: 00)</td>" \
                           "        </tr>" \
                           "        <tr><td align='center'>Операция подтверждена вводом ПИН</td></tr>" \
                           "    </tbody>" \
                           "</table>" \
                           "<style>" \
                           "    @page { size: A6 landscape; margin-right: 1.5cm; margin-left: 1.5cm; margin-top: 1cm}" \
                           "    @font-face { font-family: Courier New;" \
                          f"                 src: url({path_to_font});"\
                           "    }"\
                           "    #echeques-report {width: 470px !important;}" \
                           "    #echeques-report th{" \
                           "      font-family: 'Courier New' !important;" \
                           "      font-size: 1.3em !important;" \
                           "      font-weight: bold !important;" \
                           "      vertical-align: top !important;" \
                           "      padding: 4px 7px !important;} "   \
                           "    #echeques-report td{" \
                           "      height: auto  !important;"  \
                           "      padding: 0px 15px 1px  !important;"  \
                           "      vertical-align: top !important;"      \
                           "      font-size: 1.2em !important;"          \
                           "      font-family: 'Courier New' !important;}" \
                           "    .colortext {" \
                           "       color: #454545;" \
                           "       font-weight: bold;}" \
                           "</style>"
            if 'Возврат' in transaction['transType']:
                path_to_check = f"{transaction['cardNumberOut']}_{date_check}_{time_check_name}_r.pdf"
            elif 'Отмена' in transaction['transType']:
                path_to_check = f"{transaction['cardNumberOut']}_{date_check}_{time_check_name}_c.pdf"
            else:
                path_to_check = f"{transaction['cardNumberOut']}_{date_check}_{time_check_name}.pdf"
            if ('Contents' not in s3_session.list_objects(Bucket='agat-bills-likard')) \
                or (path_to_check not in s3_session.list_objects(Bucket='agat-bills-likard')['Contents']):
                new_file = open(path_to_check, "wb")
                pisaStatus = pisa.CreatePDF(html_pattern, dest=new_file, encoding='UTF-8')
                new_file.close()
                s3_session.upload_file(path_to_check, 'agat-bills-likard', f"{path_to_check}")
                if os.path.isfile(path_to_check):
                    os.remove(path_to_check)

def request_to_licard(url, contractId, dateFrom, dateTo, maxRowsThreshold, card=None):
    if card is None:
        print(f"{datetime.now()} Идёт выгрузка по всем картам...")
        body = {
            "contractId"       : contractId,
            "dateFrom"         : dateFrom,
            "dateTo"           : dateTo,
            "maxRowsThreshold" : maxRowsThreshold
        }
    else:
        print(f"{datetime.now()} Идёт выгрузка по выбранным картам...")
        body = {
            "contractId"      : contractId,          
            "dateFrom"        : dateFrom,           
            "dateTo"          : dateTo,             
            "cardNumberIn"    : card,       
            "maxRowsThreshold": maxRowsThreshold
    }
    headers = {"Content-Type" : "application/json;charset=utf-8"}
    res = requests.post(url, headers=headers, json=body, 
                        verify=False, cert=path_to_certificate)
    if res.status_code == 403:
        print(f"{datetime.now()} Error 403: доступ запрещён, \
                                проверьте действительность сертификата или его наличие.")
        exit()
    elif res.status_code == 500:
        print(f"{datetime.now()} Error 500: внутренняя ошибка приложения, \
                                 необработанное исключение. Проверьте \
                                 правильность входных параметров.")
        exit()
    else:
        draw_bills(res, s3_session)

def delete_old_bills(s3_session):
    to_delete = []
    for file in s3_session.list_objects(Bucket='agat-bills-likard')['Contents']:
        if {file['LastModified'].date() - datetime.now().date()} == datetime(3,12,30,23,59,59):
            to_delete.append({"Key" : file['Key']})
    
    response = s3.delete_objects(Bucket='agat-bills-likard',
                                 Delete={'Objects': to_delete})
    return response['HTTPStatusCode'] != 200 or "Возникла ошибка при удалении"
    
    
    
def download_file(s3, file_name, bucket):
    output = f"downloads/{file_name}"
    s3.Bucket(bucket).download_file(file_name, output)
    return output

