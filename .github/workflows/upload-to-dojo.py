import requests
from datetime import datetime
import configparser
import json


def find_product_by_name(host, api_key, product_name):
    headers = dict()
    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    print("\n==============Lists Products=================")
    r = requests.get(host + "/products/?name=" + str(product_name), headers=headers, verify=True)
    print(r.text)

    r = json.loads(r.text)
    if (r['count'] > 0):
        return r['results']
    else:
        return None


def find_engagement(host, api_key, engagement_name, product_id, engagement_status):
    headers = dict()
    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    print("\n==============Lists Engagement=================")
    r = requests.get(
        host + "/engagements/?name=" + str(engagement_name) + '&product=' + str(product_id) + '&status=' + str(
            engagement_status), headers=headers, verify=True)
    print(r.text)

    r = json.loads(r.text)
    if (r['count'] > 0):
        return r['results']
    else:
        return None


def create_product(host, api_key, product_name, product_type, description):
    headers = dict()
    json = dict()

    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    headers['content-type'] = "application/json"
    print(headers)

    json['prod_type'] = str(product_type)
    json['name'] = str(product_name)
    json['description'] = str(description)

    r = requests.post(host + "/products/", headers=headers, verify=True, json=json)
    print(r)
    print(r.text)

    return r.status_code, r.text


def create_engagement(host, api_key, name, product_id, commit_hash, branch_tag, source_code_management_uri, lead):
    print("\n==============Create Engagement================")
    headers = dict()
    json = dict()

    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    headers['content-type'] = "application/json"
    # print(headers)

    json['name'] = str(name)
    json['product'] = str(product_id)
    json['target_start'] = datetime.now().strftime("%Y-%m-%d")
    json['target_end'] = datetime.now().strftime("%Y-%m-%d")
    json['commit_hash'] = str(commit_hash)
    json['branch_tag'] = str(branch_tag)
    json['deduplication_on_engagement'] = True
    json['source_code_management_uri'] = ""
    json['engagement_type'] = "CI/CD"
    json['source_code_management_uri'] = source_code_management_uri
    json['status'] = "In Progress"

    json['lead'] = lead

    print(json)
    r = requests.post(host + "/engagements/", headers=headers, verify=True, json=json)
    print(r)
    print(r.text)
    return r.status_code, r.text


def upload_scan_result(host, api_key, product_name, engagement_name, scan_type, file_path):
    print("\n===============Upload Scan Results============")
    headers = dict()

    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    # print(headers)

    files = dict()
    files['file'] = open(file_path, 'rb')

    json = dict()
    json['minimum_severity'] = "Info"
    json['scan_date'] = datetime.now().strftime("%Y-%m-%d")
    json['verified'] = False
    json['tags'] = "automated"
    json['active'] = True
    json['engagement_name'] = engagement_name
    json['product_name'] = product_name
    json['scan_type'] = scan_type

    r = requests.post(host + "/import-scan/", headers=headers, verify=True, data=json, files=files)
    print(r)
    print(r.text)
    return r.status_code, r.text


def reimport_scan_result(host, api_key, product_name, engagement_name, scan_type, file_path):
    print("\n===============Re-import Scan Results============")
    headers = dict()

    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN
    # print(headers)

    files = dict()
    files['file'] = open(file_path, 'rb')

    json = dict()
    json['minimum_severity'] = "Info"
    json['scan_date'] = datetime.now().strftime("%Y-%m-%d")
    json['verified'] = False
    json['tags'] = "automated"
    json['active'] = True
    json['engagement_name'] = engagement_name
    json['product_name'] = product_name
    json['scan_type'] = scan_type

    r = requests.post(host + "/reimport-scan/", headers=headers, verify=True, data=json, files=files)
    print(r)
    print(r.text)
    return r.status_code, r.text


def find_user_id_from_email(host, api_key, email):
    headers = dict()
    AUTH_TOKEN = "Token " + str(api_key)
    headers['Authorization'] = AUTH_TOKEN

    print("\n==============List Users=================")
    r = requests.get(host + "/users/?email=" + str(email), headers=headers, verify=True)
    # print(r.text)

    r = json.loads(r.text)
    if (r['count'] > 0):
        return r['results']
    else:
        return None


print("starting")
product_id = None

# Read config file
config = configparser.ConfigParser()
config.read('dojo-env.ini')

url = config['server']['url']
api_key = config['server']['api_key']

product_name = config['product']['product_name']
description = config['product']['description']
product_type = config['product']['product_type']

source_code_management_uri = config['engagement']['source_code_management_uri']
engagement_name = config['engagement']['engagement_name']
commit_hash = config['engagement']['commit_hash']
branch = config['engagement']['branch']

scan_type = config['scan']['scan_type']
file_path = config['scan']['file_path']

try:
    reupload_enabled = config['scan']['reupload']
except:
    reupload_enabled = "false"


auto_assign_enabled = config['notify']['auto_assign_enabled']
# Get email to assignee
if auto_assign_enabled == "true":
    email = config['notify']['assignee']
else:
    email = None

query_result = find_product_by_name(url, api_key, product_name)
if (query_result != None):
    print("Product is created already")
    product_id = query_result[0]['id']
else:
    print("Creating new Product")
    status_code, result = create_product(url, api_key, product_name, product_type, description)
    result = json.loads(result)
    product_id = result['id']
print(product_id)

# Don't create the existing engagement
engagement_name_id = None
query_result = find_engagement(url, api_key, engagement_name, product_id, 'In Progress')
print(query_result)

# find user to assign engagement
user_id = None
user_data = find_user_id_from_email(url, api_key, email)
if user_data != None:
    user_id = user_data[0]['id']
else:
    user_id = 1
print(user_id)

# found engagement and try to reimport
if query_result is not None and reupload_enabled == 'true':
    print("Engagement is created already")
    engagement_name_id = query_result[0]['id']
    print(engagement_name_id)
    status_code, result = reimport_scan_result(url, api_key, product_name, engagement_name, scan_type, file_path)
else:
    # not found and engagement or force to create a new engagement
    status_code, result = create_engagement(url, api_key, engagement_name, product_id, commit_hash, branch,
                                            source_code_management_uri, user_id)
    result = json.loads(result)
    engagement_id = result['id']
    print(engagement_id)
    status_code, result = upload_scan_result(url, api_key, product_name, engagement_name, scan_type, file_path)


# Output to report summary.
data = open(file_path,'r')
data = json.load(data)
issue_count = len(data)
print(issue_count)


report_summary = open("output.csv", "a")
report_summary.write("repo,count,owner,dojo_product_id,dojo_engagement_id\n")
source_code_management_uri = source_code_management_uri.split("blob", 1)[0]
report_summary.write(str(source_code_management_uri)+","+str(issue_count)+","+str(email)+","+str(product_id)+str(engagement_id)+"\n")
report_summary.close()
