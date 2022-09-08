import json, csv
import requests
from datetime import date
import sys, getopt
import configparser

class SonarScanSlackMessage:
    HEADER_BLOCK = {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Sonar Scan Result "+date.today().strftime("%d/%m/%Y")
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
            "username": "Sonar-scan",
            "text": "Sonar Scan Summary!",
            "blocks": [
                self.HEADER_BLOCK,
                *self.get_section_block()
            ],
        }

    def get_section_block(self):
        blocks = []
        for block in self.report:
            project_key = block['project_key']
            repo = block['repo']
            branch_name = block['branch_name']
            count = block['issue_count']
            blocks.append(self._get_section_block(project_key,repo, branch_name, count))
            blocks.append(self.DIVIDER_BLOCK)
        return blocks

    @staticmethod
    def _get_section_block(project_key,repo, branch_name, count):
        return {
			"type": "section",
			"fields": [
				{
					"type": "mrkdwn",
					"text": f"*Repository:* <https://github.com/oozou/{repo}/tree/{branch_name}|{repo}>"
				},
				{
					"type": "mrkdwn",
					"text": f"*Issue Count:* {count}"
				},      
				{
					"type": "mrkdwn",
					"text": f"*Issue Details:* <https://sonarqube.devops.team.oozou.com/project/issues?id={project_key}&resolved=false|Sonarqube link>"
				}                           
			]
	}

#get open issue count with severities in BLOCKER,CRITICAL,MAJOR
def count_issues(url, api_token, project_key):
    session = requests.Session()
    session.auth = api_token, ''
    call = getattr(session, 'get')
    res = call(url+f'/api/issues/search?componentKeys={project_key}&statuses=OPEN&severities=CRITICAL,BLOCKER,MAJOR')
    output = json.loads(res.content)
    return output['total']

def main(argv):
   try:
      opts, args = getopt.getopt(argv,"h:c:",["config="])
      if(opts==[]):
        print('sonarqube_notification.py -c <configFile> ')
        sys.exit(2)
   except getopt.GetoptError:
      print('sonarqube_notification.py -c <configFile> ')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
        print('sonarqube_notification.py -c <configFile> ')
        sys.exit()
      elif opt in ("-c", "--config"):
        print(arg)
        config_file = arg
      else:
         print('sonarqube_notification.py -c <configFile> ')
         sys.exit(2)       

# read configure
   config = configparser.ConfigParser()
   config.read(config_file)
   webhook = config['slack']['webhook']
   channel = config['slack']['channel']
   url = config['sonarqube']['url']
   token = config['sonarqube']['token']
   project_key    = config['sonarqube']['project_key']
   repo_name    = config['repo']['repo_name']
   branch_name    = config['repo']['repo_branch']


# get sonarqube issue count
   issue_count = count_issues(url,token,project_key)
   print(issue_count)


 # send notification  
   report = [{"project_key":project_key,"repo":repo_name,"branch_name":branch_name,"issue_count":issue_count}]
   if(issue_count==0):
        print("no issue found, skip the notification")
   else:
        print("send notification")
        secret_scan_payload =  SonarScanSlackMessage(channel,':oozou:',list(report)).get_message_payload()
        print(secret_scan_payload)
        print(requests.post(webhook, json.dumps(secret_scan_payload)))


if __name__ == "__main__":
   main(sys.argv[1:])