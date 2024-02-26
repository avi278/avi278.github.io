from pathlib import Path, PurePath
from zipfile import ZipFile
import shutil
import sys
import urllib
import requests
import json
import base64
import subprocess
import zlib
import gzip
import argparse
from datetime import date

ARCGIS_HUB = 'https://hub.arcgis.com'
API = '/api/v3'

GITHUB_API = 'https://api.github.com/repos/avi278/avi278.github.io/contents/'



def search_datasets(name, filters, agg):
    """function for searching datasets"""

    query_url: str = f"{ARCGIS_HUB}{API}/search?{name}&filter[openData]=true&filter[tags]=any(esri,boundaries)&{filters}&{agg}&fields[datasets]=id,name,owner"

    print(query_url)

    response = requests.get(query_url)

    if response.status_code != 200:
        print(response)
        return

    data = response.json()
    return data


def download_dataset(id, message, token):
    """function for downloading and saving geojson data"""

    query_url: str = f"{ARCGIS_HUB}{API}/datasets/{id}?fields[datasets]=id,name,metadata"

    print(query_url)
    response = requests.get(query_url)
    if response.status_code != 200:
        print(response)
        print(f"Id doesn't exist: {id}")
        return False

    data = response.json()

    #print(data["data"]['attributes']['metadata'])

    query_url: str = f"{ARCGIS_HUB}/datasets/{id}.geojson"
    response = requests.get(query_url)
    
    print(query_url)

    if response.status_code != 200:
        print(response)
        print(f"Couldn't download data with this id: {id}")
        return False


    data = response.json()
    data_list = []
    geo_list = {
        "type": data['type'],
        "features": []
    }

    for x in data['features']:
        data_list.append(x['properties'])
        geo_list['features'].append({"type": x['type'], 
                                    "id": x['properties']['OBJECTID'], 
                                    #"properties": {"name": x['properties']['NAME']},
                                    "geometry": x['geometry']})
        
    if token:
        github_api_upload(geo_list, f"test/geo/{data['name']}.json.gz", message, token)
        github_api_upload(data_list, f"test/data/{data['name']}.json.gz", message, token)
    else:    
        github_cmd_add(data_list, f"./test/data/{data['name']}.json.gz")
        github_cmd_add(geo_list, f"./test/geo/{data['name']}.json.gz")

    """for testing"""
    with open(f"./test/data/{data['name']}.json", 'w') as f:
        json.dump(data_list, f, indent=2)

    with open(f"./test/geo/{data['name']}.geojson", 'w') as f:
        json.dump(geo_list, f, indent=2)

    with open(f"./test/geo/{data['name']}_all.geojson", 'w') as f:
        json.dump(data, f, indent=2)

    return True



def search_download(id=None, search_name=None, amount=None, filters=None, aggs=None, message=None, token=None):
    if (id == None):
        if not search_name:
            search_name = ''
        else: 
            search_name = f'q={search_name}'

        filter_str = [f'filter[{key}]={value}' for key, value in filters.items()]
        filter_str = '&'.join(filter_str)

        agg_str = [f'agg[{key}]={value}' for key, value in aggs.items()]
        agg_str = '&'.join(agg_str)

        data = search_datasets(search_name, filter_str, agg_str)
        
        for i, x in enumerate(data['data'], start=1):
            download_dataset(x['id'], message, token)                
            if amount == i:
                break
    else:
        download_dataset(id, message, token)


    """commit after one specification"""
    if not token:
        github_cmd_commit(message)


def specifics_file(file, message, token):
    """function for getting specifics and managing downloading and saving geojson data"""

    f = open(file)
    file_data = json.load(f)
    f.close()    

    for x in file_data:
        search_download(x['id'], x['search_name'], x['amount'], x['filters'], x['aggs'], message, token)



def github_api_upload(data, path, message, token):
    github_data_base64 = base64.b64encode(gzip.compress(json.dumps(data, indent=2).encode('utf-8'))).decode()

    headers = {'Accept': 'application/vnd.github+json', 'Authorization': f'token {token}', 'X-GitHub-Api-Version': '2022-11-28'}
    url_data = f'{GITHUB_API}{path}'

    response = requests.get(url_data)

    github_data = {"message":f"{message}", "content": github_data_base64}

    if response.status_code == 200:
        github_data["sha"] = response.json()['sha']

    github_data = json.dumps(github_data)

    response = requests.put(url_data, data=github_data, headers=headers)

    if response.status_code != 200:
        print(response)
        print(response.reason)


def github_cmd_add(data, name):
    with open(name, 'wb') as f:
        f.write(gzip.compress(json.dumps(data, indent=2).encode('utf-8')))

    subprocess.run('echo "add"', shell = True, executable="/bin/bash")
    subprocess.run('git status -s', shell = True, executable="/bin/bash")
    subprocess.run(f'git add {name}', shell = True, executable="/bin/bash")


def github_cmd_commit(message):
    subprocess.run('echo "commit"', shell = True, executable="/bin/bash")
    subprocess.run(f'git commit -m {message}', shell = True, executable="/bin/bash")
    subprocess.run('git push', shell = True, executable="/bin/bash")








def main():
    today = date.today()


    parser = argparse.ArgumentParser(description='Script for dowloading datasets from ArcGIS Hub')
    parser.add_argument('-t', '--token', help='user token for github')      
    parser.add_argument('-m', '--message', help='message for github commit')      

    group1 = parser.add_argument_group('First option', 'download multiple datasets with specifics from file')
    group1.add_argument('-if', '--inputfile', help='input file with specifics (json file)')  

    group2 = parser.add_argument_group('Second option', 'download dataset by id')
    group2.add_argument('-id', help='id from arcgis hub for specific dataset')

    group3 = parser.add_argument_group('Third option', 'download datasets with specifics from terminal')
    group3.add_argument('-sn', '--search_name', help='name to search')
    group3.add_argument('-a', '--amount', help='amount of datasets to download', type=int)
    group3.add_argument('-f', '--filters', help='filters search setting', nargs='*')
    group3.add_argument('-ag', '--aggs', help='aggregation search setting', nargs='*')



    args = parser.parse_args()

    print(args)

    """for testing"""
    data_path = Path('./test/data')
    if data_path.exists():
        shutil.rmtree(data_path)
    
    data_path.mkdir()
    data_path = Path('./test/geo')
    if data_path.exists():
        shutil.rmtree(data_path)
    
    data_path.mkdir()

    if not args.message:
        message = f'{today}'
    else:
        message = args.message

    if args.inputfile:
        specifics_file(file=args.inputfile, message=message, token=args.token)
    elif args.id:
        search_download(id=args.id, message=message, token=args.token)
    else:
        filters = {}
        aggs = {}
        if args.filters:
            filters = dict(e.split('=') for e in args.filters)

        if args.aggs:
            aggs = dict(e.split('=') for e in args.aggs)

        search_download(search_name=args.search_name, amount=args.amount, filters=filters, aggs=aggs, message=message, token=args.token)

    """
    headers = {'Accept': 'application/vnd.github.raw+json', 'Authorization': 'Bearer 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', 'X-GitHub-Api-Version': '2022-11-28'}
    url_data = f'{GITHUB_API}/test1.json.gz'
    r = requests.get(url_data, headers=headers)

    print(r)
    print(gzip.decompress(r.content))
    """


if __name__ == "__main__":
    main()