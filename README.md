### Запуск скрипта по Cron 

Скрипт лежит в папке src, переименовывать нельзя!

Скрпит после коммита упаковывается в контейнер и пушится в  registry-01.gandiva.ru:443/bills-job с тегом $CI_COMMIT_SHORT_SHA

Далее из него через Helm делается CronJob и отправляется в namespace cronjobs в кубер.

Расписание запуска в файле /bills-job-chart/values.yaml.tpl в последней строке 

Отлаживать локально, контейнер можно получить себе после пуша docker pull registry-01.gandiva.ru:443/bills-job:$CI_COMMIT_SHORT_SHA (SHA коммита посмотреть на гитлабе)
Далее  docker run registry-01.gandiva.ru:443/bills-job:67a9236a 
