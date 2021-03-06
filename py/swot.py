import os
import requests
import pandas as pd
from tqdm import tqdm
from io import StringIO
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor
tqdm.pandas()

GranuleUR = {
    'cycle':      "???",         # 3 digit cycle
    'pass':       "???",         # 3 digit pass
    'start_date': "????????",    # 8 digit date (yyyymmdd),
    'start_time': "??????",      # 6 digit date (hhmmss),
    'end_date':   "????????",    # 8 digit date (yyyymmdd),
    'end_time':   "??????",      # 6 digit date (hhmmss)
}

def pattern(**kwargs):
    """Format keyword arguments as required for GranuleUR query string"""
    return {**GranuleUR, **{k:(str(v).zfill(3) if type(v) is int else v) for k,v in kwargs.items()}}


data = "data"

def download(source: str, force: bool=False):
    target = os.path.join(data, os.path.basename(source.split("?")[0]))
    if force or not os.path.isfile(target):
        with requests.get(source, stream=True) as remote, open(target, 'wb') as local:
            if remote.status_code // 100 == 2: 
                for chunk in remote.iter_content(chunk_size=1024):
                    if chunk:
                        local.write(chunk)
    return target


def download_all(urls: list, max_workers: int=12):
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        workers = pool.map(download, urls)
        return list(tqdm(workers, total=len(urls)))


def nadir_query(ccid: str, cmr: str="cmr.earthdata.nasa.gov", **kwargs):
    # Format the 'GranuleUR' string to complete the parameters dictionary
    params = {
        'scroll': "true",
        'page_size': 2000,
        'collection_concept_id': ccid,
        'GranuleUR[]': "SWOT_GPR_2PTP{cycle}_{pass}_{start_date}_{start_time}_{end_date}_{end_time}".format(**pattern(**kwargs)),
        'options[GranuleUR][pattern]': "true",
    }
    # Download the granule metadata in csv format and load the records into a data frame
    with requests.get(f"https://{cmr}/search/granules.csv", params=params) as response:
        metadata = pd.read_csv(StringIO(response.text))
    return metadata


def karin_query(ccid: str, cmr: str="cmr.earthdata.nasa.gov", **kwargs):
    # Format the 'GranuleUR' string to complete the parameters dictionary
    params = {
        'scroll': "true",
        'page_size': 2000,
        'collection_concept_id': ccid,
        'GranuleUR[]': "SWOT_L2_LR_SSH_*_{cycle}_{pass}_{start_date}T{start_time}_{end_date}T{end_time}_????_??".format(**pattern(**kwargs)),
        'options[GranuleUR][pattern]': "true",
    }
    # Download the granule metadata in csv format and load the records into a data frame
    with requests.get(f"https://{cmr}/search/granules.csv", params=params) as response:
        metadata = pd.read_csv(StringIO(response.text))
    return metadata
