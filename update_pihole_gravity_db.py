#/usr/bin/python3

# URL filterlists.com for API request --> https://filterlists.com/api/?ref=public-apis

import requests
import os
import json
import sqlite3

url_list_to_import = []
list_tags_domain_block = []
url_software = "https://filterlists.com/api/directory/software"

payload={}
headers = {}

response_software = requests.request("GET", url_software, headers=headers, data=payload)
data_filter=json.loads(response_software.text)

# define the software used Pi-Hole
res = next((sub for sub in data_filter if sub['name'] == 'Pi-hole'), None)
list_adid_compatible = res['syntaxIds']

url_ad_lists = "https://filterlists.com/api/directory/lists"
response_adlists = requests.request("GET", url_ad_lists, headers=headers, data=payload)
formatted_data_adlists = json.loads(response_adlists.text)

# define domain to be blocked and get all IDs from filterlists

domain_to_block = ['ads','privacy','anti-adblock','malware','phishing','annoyances','clickbait']
url_domain_to_block = "https://filterlists.com/api/directory/tags"
response_domain_to_block = requests.request("GET", url_domain_to_block, headers=headers, data=payload)
formatted_domain_to_block = json.loads(response_domain_to_block.text)
for i3 in formatted_domain_to_block:
  list_tags_domain_block.extend(i3['filterListIds'])

unique_tags_domain_to_block = list(set(list_tags_domain_block))

#Get all lists for the software defined previously and matching domain categories to block
for i in formatted_data_adlists:
  url_detail_adlist = "https://filterlists.com/api/directory/lists/"
  check1 =  any(item in list_adid_compatible for item in i['syntaxIds'])
  check2 =  any(item in unique_tags_domain_to_block for item in i['tagIds'])
  if (check1 is True) and (check2 is True):
    url_detail_adlist += str(i['id'])
    response_detail_adlists = requests.request("GET", url_detail_adlist, headers=headers, data=payload)
    formatted_detail_data_adlists = json.loads(response_detail_adlists.text)
    for i1 in formatted_detail_data_adlists['viewUrls']:
      validating_url = i1['url']
      try:
        request_response_validation = requests.head(validating_url)
        status_code = request_response_validation.status_code
        if status_code == 200:
          try:
            url_list_to_import.append(validating_url)
            break
          except:
            continue
        else:
          continue
      except:
        continue

# Validation if urls exist already in database
sqldb= 'gravity.db'
connection = sqlite3.connect(sqldb)
cursor = connection.cursor()
sql_request = """select * from adlist where address = ?"""
sql_request_insert = """insert into adlist ('address') values (?);"""
url_insert_sql = []
for i4 in url_list_to_import:
  cursor.execute(sql_request,(i4,))
  result = cursor.fetchall()
  if not result:
    if i4 not in url_insert_sql:
      url_insert_sql.append(i4)

# update gravity.db with new urls
for i5 in url_insert_sql:
  cursor.execute(sql_request_insert, (i5,))
connection.commit()

# To avoid issue, run pihole -g manually when ready to update as it could take time based on number of urls added.

