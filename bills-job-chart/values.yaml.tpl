image:
  repository: "registry-01.gandiva.ru:443/bills-job"
  #repository: "docker.io/npopov34/agat-cronjobs"
  tag: "$CI_COMMIT_SHORT_SHA"
  pullPolicy: IfNotPresent

cronjob:
  name: bills-job
  schedule: "*/1 * * * *"
