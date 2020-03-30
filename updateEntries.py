#!/usr/bin/env python3.8

import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

url_base = 'http://ipinfo.io/'

p = Path('.')

for asn_file in p.glob('*.csv'):
    
    ip_list_file = asn_file.name.replace('.csv', '.lst')
    print(ip_list_file)
    output = open(ip_list_file, 'w')
    with open(asn_file) as f:
        lines = f.read().splitlines()
        for asn in lines:
            page = requests.get(url_base+asn)
            html_doc = page.content
            soup = BeautifulSoup(html_doc, 'html.parser')
            for link in soup.find_all('a'):
                if asn in link.get('href'):
                    auxstring = '/'+asn+'/'
                    line = re.sub(auxstring, '', link.get('href'))
                    printstring = asn+','+line+'\n'
                    if 'AS' not in printstring:
                        output.write(printstring)
            print(asn+'\n')

