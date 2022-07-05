import json, csv
import requests
from datetime import date
import sys, getopt
import configparser


class SecretScanSlackMessage:
    HEADER_BLOCK = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Code Scan Summary " + date.today().strftime("%d/%m/%Y")
        },
    }
    DIVIDER_BLOCK = {"type": "divider"}

    def __init__(self, channel, icon_emoji, report):
        self.channel = channel
        self.report = report
        self.icon_emoji = icon_emoji
        self.reaction_task_completed = False
        self.pin_task_completed = False

    def get_message_payload(self):
        return {
            "channel": self.channel,
            "icon_emoji": self.icon_emoji,
            "username": "code-scan",
            "text": "Code Scan Summary!",
            "blocks": [
                self.HEADER_BLOCK,
                *self.get_section_block()
            ],
        }

    def get_section_block(self):
        blocks = []
        for block in self.report:
            repo = block['repo']
            count = block['count']
            owner = block['owner'].split('@')[0]
            dojo_product_id = block['dojo_product_id']
            dojo_engagement_id = block['dojo_engagement_id']
            blocks.append(self._get_section_block(repo, count, owner, dojo_product_id, dojo_engagement_id))
            blocks.append(self.DIVIDER_BLOCK)
        return blocks

    @staticmethod
    def _get_section_block(repo, count, owner, dojo_product_id, dojo_engagement_id):
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Repository:* <{repo}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Owner:* @{owner}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Issue Count:* {count}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Product Details:* <https://defectdojo.devops.team.oozou.com/product/{dojo_product_id}|defectdojo product link>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Issue Details:* <https://defectdojo.devops.team.oozou.com/engagement/{dojo_engagement_id}|defectdojo engagement link>"
                }

            ]
        }


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "h:c:", ["config="])
        if (opts == []):
            print('gitleak_report_summary.py -c <configFile> ')
            sys.exit(2)
    except getopt.GetoptError:
        print('gitleak_report_summary.py -c <configFile> ')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('gitleak_report_summary.py -c <configFile> ')
            sys.exit()
        elif opt in ("-c", "--config"):
            print(arg)
            config_file = arg
        else:
            print('gitleak_report_summary.py -c <configFile> ')
            sys.exit(2)

    config = configparser.ConfigParser()
    config.read(config_file)
    webhook = config['slack']['webhook']
    channel = config['slack']['channel']
    report_summary = config['report']['report_summary_path']
    print(report_summary)
    report = {}
    with open(report_summary) as report_summary:
        csvReader = csv.DictReader(report_summary)
        print("+++++++")
        print(csvReader)
        report = list(csvReader)
        print(report)

    print("=============")
    print(report)
    if (report == []):
        print("no issue found, skip the notification")
    else:
        secret_scan_payload = SecretScanSlackMessage(channel, ':oozou:', report).get_message_payload()
        print(secret_scan_payload)
        print(requests.post(webhook, json.dumps(secret_scan_payload)))


if __name__ == "__main__":
    main(sys.argv[1:])