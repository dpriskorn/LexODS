#!/usr/bin/env python3
# author: Dennis Priskorn 2021
# based on https://gist.github.com/salgo60/73dc99d71fcdeb75e4d69bd73b71acf9 which was
# based on https://github.com/Torbacka/wordlist/blob/master/client.py
import logging
from datetime import datetime
import requests

from models.ods_entry import Entry

# This script loads all lemmas from ODS via their Elastic Search endpoint

logging.basicConfig(level=logging.ERROR)

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0',
    'Content-Type': 'application/json; charset=UTF-8',
}
date = datetime.today().strftime("%Y-%m-%d")
print(date)
file = open(f"ods_{date}.csv", "a")


def main():
    for x in range(0, 200000, 1000):
        if x > 0 and x % 1000 == 0:
            print(x)
        data = {
            "size": 1000,
            "from": x
        }
        response = requests.post("https://ordnet.dk/ods/es/artikel/_search",
                                 headers=headers, json=data)
        if response.status_code == 200:
            entries = response.json()
            source = entry["_source"]
            if "pos" in source.keys():
                lexical_category = ["pos"]
            else:
                lexical_category = None
            for entry in entries["hits"]["hits"]:
                entry = Entry(
                    id=int(entry["_id"]),
                    lexical_category=lexical_category,
                    lemma=source["lemma"]
                )
                # print(entry.json())
                file.write(entry.csv())
        else:
            raise ValueError(f"Got {response.status_code}, {response.text}")


if __name__ == '__main__':
    main()
