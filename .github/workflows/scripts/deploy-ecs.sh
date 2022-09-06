#!/bin/bash -eu
#
# Args: deploy.sh <stage name> <role assume to deploy> <region> <app name> <service name> <container image> <container tag>
#
export STAGE=$1
export DEPLOY_ROLE_ARN=$2
export REGION=$3
export APP_NAME=$4
export SERVICE_NAME=$5
export CONTAINER_IMAGE=$6
export CONTAINER_TAG=$7

export JSON_TASK_FILE=newtask-${STAGE}.json
export JSON_ASSUME_FILE=assume-role-${STAGE}.json
export CLUSTER_NAME=${APP_NAME}

echo "========= assume role =========="
rm -f ${JSON_ASSUME_FILE}
aws sts assume-role --region $REGION --role-arn ${DEPLOY_ROLE_ARN} --role-session-name "Deploy"  | jq .Credentials > ${JSON_ASSUME_FILE}
export AWS_ACCESS_KEY_ID=$(jq -r .AccessKeyId ${JSON_ASSUME_FILE})
export AWS_SECRET_ACCESS_KEY=$(jq -r .SecretAccessKey ${JSON_ASSUME_FILE})
export AWS_SESSION_TOKEN=$(jq -r .SessionToken ${JSON_ASSUME_FILE})
rm -f ${JSON_ASSUME_FILE}

echo "========= Retrive the existing task def =========="
rm -f ${JSON_TASK_FILE}
aws ecs describe-task-definition \
  --region $REGION \
  --task-definition ${SERVICE_NAME} \
  --query taskDefinition |  
  jq '.containerDefinitions[0].image = "'"$CONTAINER_IMAGE"':'"$CONTAINER_TAG"'"' |
  jq '.containerDefinitions[0].environment[.containerDefinitions[0].environment | length] |= . + {"name": "VERSION", "value": "'"$CONTAINER_TAG"'"}' |
  jq 'del(.status)' | 
  jq 'del(.revision)' | 
  jq 'del(.compatibilities)' | 
  jq 'del(.taskDefinitionArn)'|
  jq 'del(.requiresAttributes)'|
  jq 'del(.registeredBy)'|
  jq 'del(.registeredAt)' \
  > ${JSON_TASK_FILE}

echo "========= Register the existing task def =========="
REVISION=$(aws ecs register-task-definition --region $REGION --cli-input-json file://${JSON_TASK_FILE}|jq .taskDefinition.revision)

echo "========= Updating Service =========="
aws ecs update-service --region $REGION --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME}  --task-definition ${SERVICE_NAME}:$REVISION
rm -f ${JSON_TASK_FILE}

echo "========= Deploy Completed =========="
