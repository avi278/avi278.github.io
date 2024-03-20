import sys
import urllib
import requests
import json
import base64
import gzip
import argparse
from datetime import date
import os.path
from prettytable import PrettyTable

ARCGIS_HUB = 'https://hub.arcgis.com'
API = '/api/v3'

GITHUB_API = 'https://api.github.com/repos/avi278/avi278.github.io'
GITHUB_CONTENT = '/contents/'
GITHUB_TREE = '/git/trees/'
GITHUB_BRANCHES = '/branches/master'

def get_github_files():
    """function will return names of geo, config and data files in resources"""

    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    url = f'{GITHUB_API}{GITHUB_BRANCHES}'

    response = requests.get(url, headers)
    
    url = f'{GITHUB_API}{GITHUB_TREE}{response.json()["commit"]["sha"]}?recursive=1'
    response = requests.get(url, headers)

    data = []
    config = []
    geo = []
    for x in response.json()['tree']:
        if x['type'] == 'blob' and  x['path'].startswith('resources'):
            if x['path'].startswith('resources/config'):
                config.append(x['path'].replace('resources/config/', ''))
            if x['path'].startswith('resources/data'):
                data.append(x['path'].replace('resources/data/', ''))
            if x['path'].startswith('resources/geojson'):
                geo.append(x['path'].replace('resources/geojson/', ''))

    return config, data, geo



def choose_datasets(data):
    """user choose dataset/s to download"""

    t = PrettyTable(['X', 'Name', 'Source'])
    for i, x in enumerate(data['data'], start=1):
        t.add_row([i, x['attributes']['name'], x['attributes']['source']])
    print(t)

    while True:
        try:
            chosen = [int(item) for item in input("Enter the list of chosen datasets (1 2 3): ").split()]    
        except ValueError:
            print('Wrong format')
            continue
        else:
            break

    return chosen


def search_datasets(name: str, filters='', agg=''):
    """function for searching datasets"""

    query_url: str = f"{ARCGIS_HUB}{API}/search?{name}&filter[openData]=true&filter[tags]=any(esri,boundaries)&{filters}&{agg}&fields[datasets]=id,name,owner,description,source"

    print(query_url)

    response = requests.get(query_url)

    if response.status_code != 200:
        print(response)
        print(response.reason)
        return

    data = response.json()
    return data


def download_dataset(id, message='', token=''):
    """function for downloading and saving geojson data"""

    query_url: str = f"{ARCGIS_HUB}{API}/datasets/{id}?fields[datasets]=id,name,metadata"

    response = requests.get(query_url)
    if response.status_code != 200:
        print(f"Id doesn't exist: {id}")
        print(response)
        print(response.reason)
        return

    data = response.json()

    query_url: str = f"{ARCGIS_HUB}/datasets/{id}.geojson"
    response = requests.get(query_url)
    
    print(query_url)

    if response.status_code != 200:
        print(f"Couldn't download data with this id: {id}")
        print(response)
        print(response.reason)
        return


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
        
    if not token == '':
        print(token)
        github_api_upload(geo_list, f"test/geo/{data['name']}.json.gz", message, token)
        github_api_upload(data_list, f"test/data/{data['name']}.json.gz", message, token)


    return data_list, geo_list


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
        
        chosen = choose_datasets(data)            

        for x in chosen:
            if 0 <= (x-1) < len(data):
                download_dataset(data['data'][x-1]['id'], message, token)

    else:
        download_dataset(id, message, token)




def specifics_file(file, message, token):
    """function for getting specifics and managing downloading and saving geojson data"""

    f = open(file)
    file_data = json.load(f)
    f.close()    

    for x in file_data:
        search_download(x['id'], x['search_name'], x['amount'], x['filters'], x['aggs'], message, token)



def github_api_upload(data, path, message, token):
    """function for upload on github"""

    github_data_base64 = base64.b64encode(gzip.compress(json.dumps(data, indent=2).encode('utf-8'))).decode()

    headers = {'Accept': 'application/vnd.github+json', 'Authorization': f'token {token}', 'X-GitHub-Api-Version': '2022-11-28'}
    url_data = f'{GITHUB_API}{GITHUB_CONTENT}{path}'

    response = requests.get(url_data)

    github_data = {"message":f"{message}", "content": github_data_base64}

    if response.status_code == 200:
        github_data["sha"] = response.json()['sha']

    github_data = json.dumps(github_data)

    response = requests.put(url_data, data=github_data, headers=headers)

    print(response)
    if response.status_code != 200 and response.status_code != 201:
        print(f"githuhb error")
        print(response.reason)





def main():
    today = date.today()

    parser = argparse.ArgumentParser(description='Script for dowloading datasets from ArcGIS Hub')
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

    if not os.path.exists('token'):
        print('Token file doesn`t exists')
        return

    token = open('token').read()
    

    if not args.message:
        message = f'{today}'
    else:
        message = args.message

    if args.inputfile:
        specifics_file(file=args.inputfile, message=message, token=token)
    if args.id:
        search_download(id=args.id, message=message, token=token)
    if args.search_name or args.filters or args.aggs:
        filters = {}
        aggs = {}
        if args.filters:
            filters = dict(e.split('=') for e in args.filters)

        if args.aggs:
            aggs = dict(e.split('=') for e in args.aggs)

        search_download(search_name=args.search_name, amount=args.amount, filters=filters, aggs=aggs, message=message, token=token)

if __name__ == "__main__":
    main()