import csv
import json
import os
import re
import threading

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

headers = ['Ime i prezime', 'Adresa', 'Redovno radno vrijeme', 'Radno vrijeme za primanje stranaka', 'Telefon', 'Fax',
           'E-Mail', 'Web']
test = False
hjk = "https://www.hjk.hr/uredi"
out = 'out-hjk.csv'
outxl = 'out-hjk.xlsx'
error = 'error-hjk.txt'
s = "scraped-hjk.txt"
encoding = 'cp1250'
lock = threading.Lock()
threadcount = 5
semaphore = threading.Semaphore(threadcount)


def scrape(i):
    with semaphore:
        purl = f'{hjk}/jb/{i}'
        print("Working on", purl)
        try:
            if test:
                with open('post.html', encoding=encoding) as ufile:
                    data = ufile.read()
            else:
                data = requests.get(purl).text
            x = BeautifulSoup(data, 'lxml').find('div', {"id": "dnn_ctr1630_View_DetailsPanel"}).text.replace("Naiad",
                                                                                                              "").split(
                '\n')
            detail = [line for line in x if line.strip()]
            js = {}
            for l in detail:
                if ":" in l:
                    js[l.split(':')[0].strip()] = ":".join((l.split(':'))[1:]).strip()
            print(json.dumps(js, indent=4))
            append(js, i)
        except:
            with open(error, 'a') as efile:
                efile.write(f"{i}\n")


def append(js, i):
    with lock:
        with open(out, 'a', encoding=encoding, newline='') as outfile:
            csv.DictWriter(outfile, fieldnames=headers).writerow(js)
        with open(s, 'a') as sfile:
            sfile.write(f"{i}\n")


def main():
    logo()
    if not os.path.isfile(out):
        with open(out, 'w', encoding=encoding, newline='') as outfile:
            csv.DictWriter(outfile, fieldnames=headers).writeheader()
    if os.path.isfile(error):
        print("Working on", error)
        threads = []
        with open(error) as efile:
            for line in efile:
                t = threading.Thread(target=scrape, args=(line.strip(),))
                t.start()
                threads.append(t)
        for thread in threads:
            thread.join()
        print("Done with error file")
    if not os.path.isfile(s):
        with open(s, 'w') as sfile:
            sfile.write("")
    with open(s) as sfile:
        scraped = sfile.read().splitlines()
    print('Loading data...')
    if test:
        with open('uredi.html', encoding='utf8') as ufile:
            uredi = ufile.read()
    else:
        uredi = requests.get(hjk).text
    ids = set(
        re.findall(r'<a href="/uredi/jb/(.*?)" >', BeautifulSoup(uredi, 'lxml').find('script', {'id': 'ertz'}).string))
    print("Already scraped data", scraped)
    threads = []
    for i in ids:
        if i not in scraped:
            t = threading.Thread(target=scrape, args=(i,))
            t.start()
            threads.append(t)
        # else:
        #     print("Already scraped", i)
        if test:
            break
    for thread in threads:
        thread.join()
    print("Done with scraping.")
    cvrt()
    print("Done with conversion.")
    print("All done!")


def cvrt():
    wb = Workbook()
    ws = wb.active
    with open(out, 'r', encoding=encoding) as f:
        for row in csv.reader(f):
            ws.append(row)
    wb.save(outxl)


def logo():
    os.system('color 0a')
    print(f"""
    .__         __ __        .__           
    |  |__     |__|  | __    |  |_________ 
    |  |  \    |  |  |/ /    |  |  \_  __ \\
    |   Y  \   |  |    <     |   Y  \  | \/
    |___|  /\__|  |__|_ \ /\ |___|  /__|   
         \/\______|    \/ \/      \/       
=================================================
               hjk.hr scraper by:
        https://github.com/evilgenius786
=================================================
[+] Multithreaded (Thread count: {threadcount})
[+] Without browser
[+] Super fast
[+] Resumable
[+] Check duplicate
________________________________________________
""")


if __name__ == '__main__':
    main()
