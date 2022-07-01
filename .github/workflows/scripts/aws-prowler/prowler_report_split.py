import json
from itertools import groupby
from jinja2 import Template
from jinja2 import Environment, FileSystemLoader
import sys, getopt
import configparser

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
    report = config['report']['report_path']
    group_key = config['report']['group_key']

    report_file = open(report, 'r')
    Lines = report_file.readlines()

    count = 0
    # Strips the newline character
    json_data = []
    for line in Lines:
        count += 1
        line = json.loads(line)
        json_data.append(line)

    json_data.sort(key=lambda json_data: json_data[group_key])
    groups = groupby(json_data, lambda json_data: json_data[group_key])

    # print(json_data)
    #
    import os

    print(groups)
    for key, group in groups:
        sub_report_name=str(key) + '.json'
        sub_report = open(sub_report_name, 'a')
        print(group)
        for content in group:
            print(content)
            if(content['Status']=='FAIL'):
                sub_report.writelines(json.dumps(content)+"\n")
        sub_report.close()
        if os.stat(sub_report_name).st_size == 0:
            os.remove(sub_report_name)


if __name__ == "__main__":
    main(sys.argv[1:])
