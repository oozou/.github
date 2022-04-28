# [slack-notify](./slack-notify.yml) workflow

## Purpose
This workflow is created to be reused by other repositories workflows in the OOZOU organization to send notification to OOZOU slack channel.

## Usage
Best use of this workflow would be to trigger notification before or after your project workflows. Few points to note:

1. `OOZOU_SLACK_NOTIFICATION_WEBHOOK_URL` is provided as Organization Secret, so you don't need to define the secret in project repository.
2. The slack channel name should end with `-notificaions`.

## Example usage
In your project workflow, simply add `notify` job and pass the required variables.

```yml
name: Project O Deployment
on: push
jobs:
  deploy:
    name: Deploy something
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Important deployment step
        run: |
            echo "SOMETHING"
  notify:
    needs: deploy
    uses: oozou/.github/.github/workflows/slack-notify.yml@main
    with:
      CHANNEL_NAME: test-notifications
      TITLE: Production deployment
      MESSAGE: Project deployed to production environment
    secrets:
      OOZOU_SLACK_NOTIFICATION_WEBHOOK_URL: ${{ secrets.OOZOU_SLACK_NOTIFICATION_WEBHOOK_URL }}
```