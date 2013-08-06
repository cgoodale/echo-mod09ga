#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
"""

**NOTE:  THIS REQUIRES PYTHON 2.7.  Older version of Python might work
         but you will need to install the argparse module first.

This script will query the NASA ECHO Catalog REST API for MOD09GA hdf files
and will print out the resulting http:// urls.  Typically these outputs can
be piped into a text file for later downloading via wget.

Example Usage:

    $> python mod09ga_urls.py -t h11v03 > h11v03-urls.txt
    $> wget -i h11v03-urls.txt

"""

ECHO_GRANULE_BASE_URL = 'https://api.echo.nasa.gov/catalog-rest/echo_catalog/granules.json?'
PAGE_SIZE = 2000
# Due to the odd way that the API works we cannot use a Python dictionary to set up the
#  URL params easily. Instead we will be creating a really long string.
query_string = 'dataset_id=MODIS/Terra Surface Reflectance Daily L2G Global 1km and 500m SIN Grid V005'

# Python standard Library Imports
import argparse
import datetime
import re
import sys

# 3rd Party Modules
import requests

# Input Parameter Parsing
parser = argparse.ArgumentParser(description="Query ECHO for MOD09GA download urls. If no \
        start or end dates are given, the entire time range for the tileID will be returned")
parser.add_argument('tile', metavar='tile', type=str, help='TileID to fetch, format h##v## \
                    i.e. h09v05')
parser.add_argument('-s', dest='start_date', help='Start Date in format YYYYMMDD')
parser.add_argument('-e', dest='end_date', help='End Date in format YYYYMMDD')


def build_query_string(tile_id, start=None, end=None, query=query_string):
    # tile_id should be h##v## and we need to parse the ##'s for each 
    vert_tile = tile_id.split('v')[1]
    horiz_tile = tile_id.split('h')[1].split('v')[0]
    query = set_horizontal_tile(query, horiz_tile)
    query = set_vertical_tile(query, vert_tile)
    return query

def date_range_filter(hdf_urls, start, end):
    if start == None and end == None:
        return hdf_urls
    else:
        filtered_urls = []
        
        if start == None:
            end = datetime.datetime.strptime(end, "%Y%m%d")
            for url in hdf_urls:
                granule_datetime = granule_date(url)
                if granule_datetime <= end:
                    filtered_urls.append(url)
                else:
                    pass
        elif end == None:
            start = datetime.datetime.strptime(start, "%Y%m%d")
            for url in hdf_urls:
                granule_datetime = granule_date(url)
                if granule_datetime >= start:
                    filtered_urls.append(url)
                else:
                    pass
        else:
            end = datetime.datetime.strptime(end, "%Y%m%d")
            start = datetime.datetime.strptime(start, "%Y%m%d")
            for url in hdf_urls:
                granule_datetime = granule_date(url)
                if granule_datetime <= end and granule_datetime >= start:
                    filtered_urls.append(url)
                else:
                    pass
    return filtered_urls

def generate_all_download_urls(url, page_size=PAGE_SIZE):
    """ This will take in a query URL and use pagination with the Requests
    module to print all the urls out, until the ECHO api has no more pages
    of data to return
    """
    all_urls = []
    page_count = 1
    page_param = 'page_size=%s' % page_size
    while page_count:
        page_num_param = 'page_num=%s' % page_count
        paged_url = '&'.join([url, page_param, page_num_param])
        r = requests.get(paged_url)
        if r.status_code != 200:
            print('Unable to fetch %s\n Return status code: %s' % (paged_url, r.status_code))
            page_count += 1
            pass
        else:
            hdfs = parse_hdf_paths(r)
            all_urls += hdfs
            # If we ar not at the end, increase page count for next page
            if r.headers['echo-cursor-at-end'] == 'false':
                page_count += 1
            else:
                page_count = False

    return all_urls

def granule_date(url):
    """
    Input::
        url (string) http url to an HDF file
    Output::
        granule_date (datetime object) represents the DAY that the granule represents
    """
    # Typical URL:
    # http://e4ftl01.cr.usgs.gov/MODIS_Dailies_A/MOLT/MOD09GA.005/2013.08.03/MOD09GA.A2013215.h10v03.005.2013217100343.hdf
    url_date_string = url.split('/MOD09GA.005/')[1].split('/MOD09GA.A')[0]
    granule_date = datetime.datetime.strptime(url_date_string, '%Y.%m.%d')
    return granule_date

def parse_hdf_paths(request):
    hdfs = []
    json = request.json()
    entries = json['feed']['entry']
    for entry in entries:
        links = entry['links']
        for link in links:
            if link['href'].endswith('.hdf'):
                hdfs.append(link['href'])
            else:
                pass

    return hdfs

def set_horizontal_tile(query, value):
    att_value = 'attribute[][value]=%s' % value
    att_name = 'attribute[][name]=HORIZONTALTILENUMBER'
    att_type = 'attribute[][type]=int'
    new_query = '&'.join([query, att_name, att_type, att_value])
    return new_query

def set_vertical_tile(query, value):
    att_value = 'attribute[][value]=%s' % value
    att_name = 'attribute[][name]=VERTICALTILENUMBER'
    att_type = 'attribute[][type]=int'
    new_query = '&'.join([query, att_name, att_type, att_value])
    return new_query

if __name__ == "__main__":
    
    args = parser.parse_args()
    r = re.compile('h\d{2}v\d{2}')
    if r.match(args.tile) is not None:
        query_params = build_query_string(args.tile)
        initial_URL = "".join([ECHO_GRANULE_BASE_URL, query_params])
        hdf_urls = generate_all_download_urls(initial_URL)
    else:
        print "%s does not match the h##v## tileID format" % args.tile
        sys.exit()

    hdf_urls = date_range_filter(hdf_urls, start=args.start_date, end=args.end_date)

    for url in hdf_urls:
        print url