# [Infracost](./infracost.yaml) workflow

## Purpose
This shared workflow is created to be used by other repositories workflows in the OOZOU organization for generating the estimated monthly cost base on the terraform plan files and publish the report to a confluence page.

## Inputs

|  Input Name   | Input Type  | Required | Note |
| :------------: | :------------: | :------------: | :------------ |
| CONFLUENCE_PAGE_ID  | string | Yes |The ID of the confluence page  |
|  CONFLUENCE_PAGE_TITLE | string | Yes |The Title of the confluence page| 
|  INFRACOST_ARTIFACT |  string | Yes | The name of GitHub Artifact that contains the infracost.yaml configure and terraform plan files | |

## Secrets

|  Secret Name   | Required | Note |
| :------------: |  :------------: | :------------ |
| INFRACOST_API_KEY  |  Yes |API Key of Infracost. [Get Infracost API KEY](https://www.infracost.io/docs/#2-get-api-key) |
|  CONFLUENCE_USERNAME |  Yes |Atlassian Account User Name| 
|  CONFLUENCE_API_TOKEN |  Yes | Atlassian Account User API Token. [How to Generate API Token](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)  | |


## Example usage
In your project workflow,  add `Infracost` job and pass the required variables.

Workflow Example:
```yml
name: infracost-oozou-internal
on: 
      workflow_dispatch:
      push:

jobs:
  terraform:
    name: Infracost
    runs-on: oozou-eks-runner
    steps:
      # Checkout the base branch of the pull request (e.g. main/master).
      - name: Checkout base branch
        uses: actions/checkout@v2

      # setup terraform
      - name: setup terraform
        run: |
            wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
            echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
            sudo apt update && sudo apt install terraform
          
      - name: Generate tfplan json for oozou-estate-hub 
        working-directory: examples/oozou-estate-hub
        run: |
            terraform init
            terraform plan -out tfplan.binary -var-file=terraform.internal-devops.tfvars -var "aws_account={access_key =\"${{ secrets.AWS_ACCESS_KEY_ID }}\",secret_key =\"${{ secrets.AWS_SECRET_ACCESS_KEY }}\",region=\"us-east-2\"}"
            terraform show -json tfplan.binary > plan.json
            echo "update region"
            echo "$( jq '.configuration.provider_config.aws.expressions.region={"constant_value":"us-east-2"}' plan.json )" > plan.json
            
      - name: Generate tfplan json for oozou-pass-example
        working-directory: examples/oozou-pass-example
        run: |
            terraform init
            terraform plan -out tfplan.binary -var-file=terraform.internal-devops.tfvars -var "aws_account={access_key =\"${{ secrets.AWS_ACCESS_KEY_ID }}\",secret_key =\"${{ secrets.AWS_SECRET_ACCESS_KEY }}\",region=\"us-east-2\"}"
            terraform show -json tfplan.binary > plan.json
            echo "update region"
            echo "$( jq '.configuration.provider_config.aws.expressions.region={"constant_value":"us-east-2"}' plan.json )" > plan.json
            
      - uses: actions/upload-artifact@v3
        with:
          name: infracost-artifact
          path: |
            examples/infracost-config-oozou-internal.yml
            examples/*/plan.json
            examples/*/usage*.yml
    
  infracost:
    needs: terraform
    uses: oozou/.github/.github/workflows/infracost.yaml@feat/infracost
    with:
        CONFLUENCE_PAGE_ID: xxxxxxxx
        CONFLUENCE_PAGE_TITLE: OOZOU-Internal-Cost
        INFRACOST_ARTIFACT: infracost-artifact  
    secrets:
        INFRACOST_API_KEY: ${{ secrets.INFRACOST_API_KEY }}
        CONFLUENCE_USERNAME: ${{ secrets.CONFLUENCE_USERNAME }}
        CONFLUENCE_API_TOKEN: ${{ secrets.CONFLUENCE_API_TOKEN }}
```

## Infracost config file
An Infracost config file can be created in each of your Terraform repos to specify how Infracost should be run.
**Note:** Make sure the config file name follow pattern `infracost*.yml`

infracost.yml Example:
```
version: 0.1
projects:
  - path: oozou-estate-hub/plan.json
    name: oozou-hub
    usage_file: oozou-estate-hub/usage-oozou-internal.yml
  - path: oozou-estate-security-hub/plan.json
    name: oozou-security-hub
    usage_file: oozou-estate-security-hub/usage-oozou-internal.yml
```
## Usage file
You can specify usage estimates in a file called usage.yml, which can be passed to Infracost to calculate costs based on usage
##### 1. Generate usage file
Use the `--sync-usage-file` option to generate a new usage file or update an existing one. You must specify the location of the new or existing usage file using the `--usage-file` flag:
```
infracost breakdown --sync-usage-file --usage-file usage.yml --path /code
```
##### 2. Edit usage file
Edit the generated usage file with your usage estimates, for example a Lambda function can have the following parameters. This file can be checked into git alongside other code, and updated when needed.
```
version: 0.1
resource_usage:
  aws_lambda_function.hi:
    monthly_requests: 0 # Monthly requests to the Lambda function.
    request_duration_ms: 0 # Average duration of each request in milliseconds.
```
##### Supported parameters
The reference file [usage-example.yml](https://github.com/infracost/infracost/blob/master/infracost-usage-example.yml) contains the list of all of the available parameters and their descriptions.

usage.yml Example:
```
# You can use this file to define resource usage estimates for Infracost to use when calculating
# the cost of usage-based resource, such as AWS S3 or Lambda.
# `infracost breakdown --usage-file infracost-usage.yml [other flags]`
# See https://infracost.io/usage-file/ for docs
version: 0.1
resource_usage:
  module.hub_cloudtrail[0].aws_cloudtrail.this[0]:
    # monthly_additional_management_events: 0.0 # Monthly additional copies of read and write management events. The first copy of management events per region is free, so this should only be non-zero if there are multiple trails recording management events in this region.
    monthly_data_events: 94 # Monthly data events delivered to S3, Lambda or DynamoDB
    monthly_insight_events: 2000000 # Monthly CloudTrail Insight events
  module.hub_cloudtrail[0].aws_cloudwatch_log_group.trail_log[0]:
    # storage_gb: 4.0 # Total data stored by CloudWatch logs in GB.
    # monthly_data_ingested_gb: 0.0 # Monthly data ingested by CloudWatch logs in GB.
    # monthly_data_scanned_gb: 0.0 # Monthly data scanned by CloudWatch logs insights in GB.
  module.vpc.aws_nat_gateway.nat[0]:
    monthly_data_processed_gb: 60.0 # Monthly data processed by the NAT Gateway in GB.
  module.vpc.module.flow_log.aws_cloudwatch_log_group.flow_log[0]:
    storage_gb: 4.0 # Total data stored by CloudWatch logs in GB.
    # monthly_data_ingested_gb: 0.0 # Monthly data ingested by CloudWatch logs in GB.
    # monthly_data_scanned_gb: 0.0 # Monthly data scanned by CloudWatch logs insights in GB.
  module.ecr_example.aws_ecr_repository.this:
    storage_gb: 4.0 # Total size of ECR repository in GB.
  module.hub_cloudtrail[0].module.centralize_log_bucket[0].aws_s3_bucket.this:
    # object_tags: 0 # Total object tags. Only for AWS provider V3.
    standard:
      storage_gb: 2.0 # Total storage in GB.
      monthly_tier_1_requests: 100000 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      monthly_tier_2_requests: 400000 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB.
      # monthly_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB.
    # intelligent_tiering:
      # frequent_access_storage_gb: 0.0 # Total storage for Frequent Access Tier in GB.
      # infrequent_access_storage_gb: 0.0 # Total storage for Infrequent Access Tier in GB.
      # monitored_objects: 0 # Total objects monitored by the Intelligent Tiering.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_lifecycle_transition_requests: 0 # Monthly Lifecycle Transition requests.
      # monthly_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB.
      # monthly_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB.
      # early_delete_gb: 0.0 # If an archive is deleted within 1 months of being uploaded, you will be charged an early deletion fee per GB.
      # archive_access_storage_gb: 0.0
      # deep_archive_access_storage_gb: 0.0
    # standard_infrequent_access:
      # storage_gb: 0.0 # Total storage in GB.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_lifecycle_transition_requests: 0 # Monthly Lifecycle Transition requests.
      # monthly_data_retrieval_gb: 0.0 # Monthly data retrievals in GB
      # monthly_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB.
      # monthly_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB.
    # one_zone_infrequent_access:
      # storage_gb: 0.0 # Total storage in GB.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_lifecycle_transition_requests: 0 # Monthly Lifecycle Transition requests.
      # monthly_data_retrieval_gb: 0.0 # Monthly data retrievals in GB
      # monthly_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB.
      # monthly_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB.
    # glacier_flexible_retrieval:
      # storage_gb: 0 # Total storage in GB.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_lifecycle_transition_requests: 0 # Monthly Lifecycle Transition requests.
      # monthly_standard_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB (for standard level of S3 Glacier).
      # monthly_standard_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB (for standard level of S3 Glacier).
      # monthly_bulk_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB (for bulk level of S3 Glacier)
      # monthly_bulk_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB (for bulk level of S3 Glacier)
      # monthly_expedited_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB (for expedited level of S3 Glacier)
      # monthly_expedited_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB (for expedited level of S3 Glacier)
      # monthly_standard_data_retrieval_requests: 0 # Monthly data Retrieval requests (for standard level of S3 Glacier).
      # monthly_expedited_data_retrieval_requests: 0 # Monthly data Retrieval requests (for expedited level of S3 Glacier).
      # monthly_standard_data_retrieval_gb: 0.0 # Monthly data retrievals in GB (for standard level of S3 Glacier).
      # monthly_expedited_data_retrieval_gb: 0.0 # Monthly data retrievals in GB (for expedited level of S3 Glacier).
      # early_delete_gb: 0.0 # If an archive is deleted within 3 months of being uploaded, you will be charged an early deletion fee per GB.
    # glacier_deep_archive:
      # storage_gb: 0.0 # Total storage in GB.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_lifecycle_transition_requests: 0 # Monthly Lifecycle Transition requests.
      # monthly_standard_data_retrieval_requests: 0 # Monthly data Retrieval requests (for standard level of S3 Glacier).
      # monthly_bulk_data_retrieval_requests: 0 # Monthly data Retrieval requests (for bulk level of S3 Glacier).
      # monthly_standard_data_retrieval_gb: 0.0 # Monthly data retrievals in GB (for standard level of S3 Glacier).
      # monthly_bulk_data_retrieval_gb: 0.0 # Monthly data retrievals in GB (for bulk level of S3 Glacier).
      # early_delete_gb: 0.0 # If an archive is deleted within 6 months of being uploaded, you will be charged an early deletion fee per GB.
  module.vpc.module.flow_log.module.centralize_flow_log_bucket[0].aws_s3_bucket.this:
    # object_tags: 0 # Total object tags. Only for AWS provider V3.
    # standard:
      # storage_gb: 0.0 # Total storage in GB.
      # monthly_tier_1_requests: 0 # Monthly PUT, COPY, POST, LIST requests (Tier 1).
      # monthly_tier_2_requests: 0 # Monthly GET, SELECT, and all other requests (Tier 2).
      # monthly_select_data_scanned_gb: 0.0 # Monthly data scanned by S3 Select in GB.
      # monthly_select_data_returned_gb: 0.0 # Monthly data returned by S3 Select in GB.
```
