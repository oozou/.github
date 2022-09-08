import numbers
import os
import json
import sys
import logging
from typing import List, Tuple
from dotenv import load_dotenv
from atlassian import Confluence
from jinja2 import Environment, FileSystemLoader


data = None
config = None
DEFAULT_LOG_LEVEL = 'DEBUG'
FILL_NA_WITH = ''

def init() -> None:
    load_dotenv()
    logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()))
    global data, config

    try:
        with open(os.getenv('DATA_FILE', 'DATA_FILE_NOT_FOUND')) as f:
            data = json.load(f)
            logging.debug('Successful load data')
    except Exception as exc:
        logging.error(exc)
        sys.exit()


def update_to_confluence(body: str) -> None:
    confluence_config = {
        'URL' : os.getenv('URL', False),
        'USERNAME' : os.getenv('USERNAME', False),
        'API_TOKEN' : os.getenv('API_TOKEN', False),
        'PAGE_ID' : os.getenv('PAGE_ID', False),
        'PAGE_TITLE' : os.getenv('PAGE_TITLE', False)
    }

    if False in confluence_config.values():
        for key, value in confluence_config.items():
            if value is False:
                logging.warning(f'Confluence\'s {key} is missing')
    else:
        try:
            confluence = Confluence(url=confluence_config['URL'], username=confluence_config['USERNAME'], password=confluence_config['API_TOKEN'], cloud=True)
            confluence.update_page(confluence_config['PAGE_ID'], confluence_config['PAGE_TITLE'], body, parent_id=None, type='page', representation='storage')
        except Exception as exc:
            logging.error(exc)

if __name__ == '__main__':
    init()
    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template("infracost.jinja")

    html = template.render(projects = data['projects'], totalMonthlyCost=data['totalMonthlyCost'])
    update_to_confluence(html)
