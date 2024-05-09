# Geovisto Data server

Geovisto Data server is tool for Geovisto administrators for easy search and download of open geo datasets.

## Installation

Install requirements from file

```bash
pip install -r requirements.txt
```

## Setting 

Create file `token` with your GitHub personal access token (will be use for GitHub REST API)

If you need generate token, you can do it [here](https://docs.github.com/en/enterprise-server@3.9/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token)


## Usage

```bash
python3 downloader.py [-h] [-m MESSAGE] [-if INPUTFILE] [-id ID] [-sn SEARCH_NAME] [-a AMOUNT] [-f [FILTERS ...]] [-ag [AGGS ...]]

options:
  -h,  --help            show this help message and exit
  -m,  --message         message for github commit
  -if, --inputfile      input file with specifics (json file)
  -id                   id from arcgis hub for specific dataset
  -sn, --search_name    name to search
  -a,  --amount          amount of datasets to download
  -f,  --filters         filters search setting
  -ag, --aggs            aggregation search setting
```


### API

Hosted on [PythonAnywhere](https://www.pythonanywhere.com/)

Domain [http://avi278.pythonanywhere.com/](http://avi278.pythonanywhere.com/)

| Endpoints        | Description           | Example  |
|:------------- |:-------------|:-----|
| GET /search/<string:name>      | return JSON with best matched datasets | /search/cities - search for best matched datasets by name cities |
| GET /download/<string:id>      | return JSON with data and geometry    | /download/df827f607eb347d49a6cca071ce66d5e_11 - download dataset by id df827f607eb347d49a6cca071ce66d5e_11 |
| GET /files      | return JSON with files in resources  | /files - return geo, config and data |
| GET /file/<string:dir>/<string:subdir>/<string:file>      | return JSON content of file  | /file/resources/geo/country_polygons.json - return JSON content of country_polygons.json |

