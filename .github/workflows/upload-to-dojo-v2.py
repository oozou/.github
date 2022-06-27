import json, requests, configparser
from datetime import datetime

class Defectdojo:
    def __init__(self, URL, api_key):
        self.URL = URL
        self.api_key = api_key
        self.headers = self.set_header(api_key)

    def set_header(self, x_api_key):
        headers = dict()
        headers['Authorization'] = "Token " + x_api_key
        self.headers = headers
        return headers

    def post(self, x_json, x_file=None):
        headers = self.headers
        if x_file is None:
            headers['content-type'] = "application/json"
            r = requests.post(self.URL, headers=headers, verify=True, json=x_json)
        else:
            files = dict()
            files['file'] = open(x_file, 'rb')

            r = requests.post(self.URL, headers=headers, verify=True, data=x_json, files=files)

        print("Status Code is: " + str(r.status_code) + "\ntext is: " + str(r.text))
        return r.status_code, r.text

    def get(self, x_query_string):
        r = requests.get(self.URL + str(x_query_string), headers=self.headers, verify=True)
        r = json.loads(r.text)
        if r['count'] > 0:
            return r['results']
        else:
            return None

    def __str__(self):
        return self.URL


class Engagement(Defectdojo):
    def __init__(self, url, api_key):
        super().__init__(url + "/engagements/", api_key)

    def create(self,name, product_id, commit_hash, branch_tag, source_code_management_uri, lead):
        json = dict()
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
        print("=======Creating A new Engagement========")
        return super().post(json)

class Product(Defectdojo):
    def __init__(self, url, api_key):
        super().__init__(url + "/products/", api_key)

    def create(self, product_name, product_type, description):
        json = dict()
        json['prod_type'] = str(product_type)
        json['name'] = str(product_name)
        json['description'] = str(description)
        print("=======Creating A new Product========")
        return super().post(json)


class ScanResult(Defectdojo):
    def __init__(self, url, api_key):
        super().__init__(url, api_key)

    def prepare_data(self, product_name, engagement_name, scan_type):
        json = dict()
        json['minimum_severity'] = "Info"
        json['scan_date'] = datetime.now().strftime("%Y-%m-%d")
        json['verified'] = False
        json['tags'] = "automated"
        json['active'] = True
        json['engagement_name'] = engagement_name
        json['product_name'] = product_name
        json['scan_type'] = scan_type
        return json

    def upload(self, product_name, engagement_name, scan_type, file_path):
        self.URL = self.URL + "/import-scan/"
        x_json = self.prepare_data(product_name, engagement_name, scan_type)
        return self.post(x_json, x_file=file_path)

    def reupload(self, product_name, engagement_name, scan_type, file_path):
        self.URL = self.URL + "/reimport-scan/"
        x_json = self.prepare_data(product_name, engagement_name, scan_type)
        return super().post(x_json, x_file=file_path)


class User(Defectdojo):
    def __init__(self,url,api_key):
        super().__init__(url + "/users/", api_key)


class ConfigData:
    def __init__(self, ini_path):
        config = configparser.ConfigParser()
        config.read(ini_path)

        self.url = config['server']['url']
        self.api_key = config['server']['api_key']

        self.product_name = config['product']['product_name']
        self.description = config['product']['description']
        self.product_type = config['product']['product_type']

        self.source_code_management_uri = config['engagement']['source_code_management_uri']
        self.engagement_name = config['engagement']['engagement_name']
        self.commit_hash = config['engagement']['commit_hash']
        self.branch = config['engagement']['branch']

        self.scan_type = config['scan']['scan_type']
        self.file_path = config['scan']['file_path']

        try:
            self.reupload_enabled = config['scan']['reupload']
        except:
            self.reupload_enabled = "false"

        auto_assign_enabled = config['notify']['auto_assign_enabled']
        # Get email to assignee
        if auto_assign_enabled == "true":
            self.email = config['notify']['assignee']
        else:
            self.email = None

if __name__ == "__main__":

    config_data = ConfigData('dojo-env.ini')

    #Connectors
    product_con = Product(getattr(config_data, 'url'),getattr(config_data, 'api_key'))
    engagement_con = Engagement(getattr(config_data, 'url'),getattr(config_data, 'api_key'))
    user_con = User(getattr(config_data, 'url'),getattr(config_data, 'api_key'))
    scan_result_con = ScanResult(getattr(config_data, 'url'),getattr(config_data, 'api_key'))

    # find product
    query_result = product_con.get("?name=" + str(getattr(config_data, 'product_name')))

    product_id = None
    if query_result is None:
        print("Not found the exist product, will create the new product")
        status, text = product_con.create(
            getattr(config_data,'product_name'),
            getattr(config_data, 'product_type'),
            getattr(config_data, 'description')
        )
        product_id = json.loads(text)['id']
    else:
        print("Product exists")
        product_id = query_result[0]['id']
    print("product id is "+str(product_id))

    # Find user
    print("=======Find User=============")
    query_result = user_con.get("?email=" + str(getattr(config_data,'email')))
    user_id = None
    if query_result is not None:
        print("Found assignee user")
        user_id = query_result[0]['id']
    else:
        print("Not found user,Set to default user")
        user_id = 1
    print("User id is " + str(user_id))

    # Find engagement
    print("=======Find Engagement=======")
    engagement_id = None
    query_string = "?name=" + getattr(config_data, 'engagement_name') + '&product=' + str(product_id) + \
                   '&status=In Progress'
    query_result = engagement_con.get(query_string)

    if query_result is not None and getattr(config_data,'reupload_enabled') == 'true':
        print("Engagement exists or enable reuploading")
        engagement_id = query_result[0]['id']
        print("Engagement id is " + str(engagement_id))

        # reimporting
        print("======ReUploading new scan result=========")
        status, text = scan_result_con.reupload(
            getattr(config_data,'product_name'),
            getattr(config_data, 'engagement_name'),
            getattr(config_data, 'scan_type'),
            getattr(config_data, 'file_path')
        )
        print("upload status is "+str(status))

    else:
        print("Engagement doesn't exists")
        status, text = engagement_con.create(
            getattr(config_data,'engagement_name'),
            product_id,
            getattr(config_data,'commit_hash'),
            getattr(config_data,'branch'),
            getattr(config_data,'source_code_management_uri'),
            user_id
        )
        engagement_id = json.loads(text)['id']
        print("Engagement id is " + str(engagement_id))

        # import the new
        print("======Uploading new scan result=========")
        status, text = scan_result_con.upload(
            getattr(config_data,'product_name'),
            getattr(config_data, 'engagement_name'),
            getattr(config_data, 'scan_type'),
            getattr(config_data, 'file_path')
        )
        print("upload status is " + str(status))

    print("=====Output the result to CSV=====")
    data = open(getattr(config_data, 'file_path'), "r")
    issue_count = len(json.load(data))
    print(issue_count)

    report_summary = open("output.csv", "a")
    report_summary.write("repo,count,owner,dojo_product_id,dojo_engagement_id\n")
    source_code_management_uri = getattr(config_data, 'source_code_management_uri').split("blob", 1)[0]
    report_summary.write(
        str(getattr(config_data, 'source_code_management_uri')) + "," + str(issue_count) + ","
        + str(getattr(config_data, 'email')) + ","
        + str(product_id) + "," + str(engagement_id) + "\n")
    report_summary.close()
    print("=====Done Output the result to CSV=====")
