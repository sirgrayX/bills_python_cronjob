image:
  repository: "registry-01.gandiva.ru:443/s3manager"
  tag: "$CI_COMMIT_SHORT_SHA"
  pullPolicy: IfNotPresent

s3manager:
  name: s3manager
  port: "8888"
