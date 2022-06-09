# [code-scan](./code-scan.yaml) workflow

## Purpose
This shared workflow is created to be used by other repositories workflows in the OOZOU organization for code scanning.

## Inputs

|  Input Name   | Input Type  | Required | Note |
| :------------: | :------------: | :------------: | :------------ |
| SCAN_TYPE  | string | Yes |Support types:<br/>- IAC (Include Terraform, Docker, Kubernetes) <br/>- Ruby   <br/>- Javascript (.njsscan file is required under the root path, sample: [.nsscan](./.njsscan)) <br/>- Mobile  (.mobsf file is required under the root path, sample: [.mobsf](./.mobsf)) |
|  SCAN_INCLUDE | string | Yes |Comma-separated paths to directories containing main source files. For directories add "/" behind. Example: terraform/,Dockerfile| 
|  SCAN_EXCLUDE |  string | No |Comma-separated paths to directories containing main source files. For directories add "/" behind. Example: app/assets/,test/ | |



## Example usage
In your project workflow,  add `scan` job and pass the required variables.

IaC Example:
```yml
name: code-scan

# Controls when the workflow will run
on:
  workflow_dispatch:
  schedule:
      - cron: '0 11 * * 1-5' 
jobs:
		
  scan:
    uses: oozou/.github/.github/workflows/code-scan.yml@main
    secrets: inherit
    with:
        SCAN_TYPE: IAC
        SCAN_INCLUDE: terraform/,docker/
        SCAN_EXCLUDE: terraform/modules/
```

Ruby Example:
```yml
name: code-scan

# Controls when the workflow will run
on:
  workflow_dispatch:
  schedule:
      - cron: '0 11 * * 1-5' 
jobs:
		
  scan:
    uses: oozou/.github/.github/workflows/code-scan.yml@main
    secrets: inherit
    with:
        SCAN_TYPE: Ruby
        SCAN_INCLUDE: app/,config/,db/,lib/
        SCAN_EXCLUDE: app/assets/
```

JavaScript Example: (Note: make sure .njsscan file is added under the root path. sample: [.nsscan](./.njsscan))
```yml
name: code-scan

# Controls when the workflow will run
on:
  workflow_dispatch:
  pull_request:
    branches:
      - 'main'
jobs:
		
  scan:
    uses: oozou/.github/.github/workflows/code-scan.yml@main
    secrets: inherit
    with:
        SCAN_TYPE: Javascript
        SCAN_INCLUDE: packages/
```

Mobile Example: (Note: make sure .mobsf file is added under the root path. sample: [.mobsf](./.mobsf))
```yml
name: code-scan

# Controls when the workflow will run
on:
  workflow_dispatch:
  pull_request:
    branches:
      - 'main'
jobs:
		
  scan:
    uses: oozou/.github/.github/workflows/code-scan.yml@main
    secrets: inherit
    with:
        SCAN_TYPE: Mobile
        SCAN_INCLUDE: .
```
