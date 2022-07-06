# [aws-security-scan](./aws-scan.yaml) workflow

## Purpose
This shared workflow is created to be used by other repositories workflows in the OOZOU organization for aws security scanning.

## Inputs

|  Input Name   | Input Type  | Required | Note |
| :------------: | :------------: | :------------: | :------------ |
| AWS_ROLE  | string | Yes | The workflow uses Github AWS OIDC, the AWS OIDC Configuration and role for aws security scan need to be setup in the target AWS account. [GitHub AWS OIDC Configure Guide](https://oozouhq.atlassian.net/wiki/spaces/DOT/pages/2002714692/GitHub+AWS+OIDC+Configure)  |
| AWS_REGION | string | Yes |AWS regions to be scanned, for multiple regions, use comma to separate| 
| AWS_ENVIRONMENT |  string | Yes | choose either "dev" or "prod", different rules will be applied | |
| PROJECT_NAME |  string | Yes | name of the project, the name in defectdojo will be {{ PROJECT_NAME }}-AWS| |


## Example usage
In your project workflow,  add `scan` job and pass the required variables.

Example:
```yml
name: AWS security scan
on:
  workflow_dispatch:
  schedule:
      - cron: '0 11 * * 1' 
  
jobs:
        
  scan:
    uses: oozou/.github/.github/workflows/aws-scan.yaml@main
    secrets: inherit
    with:
        AWS_ROLE : arn:aws:iam::xxxxxxx:role/oozou-internal-devops-github-action-oidc-security-scan-role
        AWS_REGION : ap-southeast-1
        AWS_ENVIRONMENT: dev
        PROJECT_NAME: oozou-sandbox
```
