from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from datetime import datetime
import importlib
importlib.reload(poolData.config)
from poolData.config import API_URL, API_URL_FREE
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''GraphQl client'''

def with_url(url):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(url, *args, **kwargs)
        return wrapper
    return decorator

def query_client(url,query,variables):

    res = requests_retry_session().post(url, json={'query': query, 'variables': variables})

    return res.json()

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query all swaps in a pool in a defined time range'''
@with_url(API_URL_FREE)
def query_swaps(url, begin, end, pool_id):

    query = '''
        query ($pool: String!, $timestamp_gt: Int!, $timestamp_lt: Int!) {
            swaps(where: {pool: $pool, timestamp_gt: $timestamp_gt, timestamp_lt: $timestamp_lt}, orderby: timestamp) {
            id
            amount0
            amount1
            timestamp
            amountUSD
            sqrtPriceX96
            }
        }
    '''
    variables = { "pool": pool_id, "timestamp_gt": begin, 'timestamp_lt': end}
    res = query_client(url, query, variables)
    data = pd.json_normalize(res['data']['swaps'])
    
    return data


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query liquidity data for a pool'''
@with_url(API_URL_FREE)
def query_liquidity(url, begin, end, pool_id):
    query = '''
        query ($pool: String!, $periodStartUnix_gt: Int!, $periodStartUnix_lt: Int!) {
        poolHourDatas(where: {pool: $pool, periodStartUnix_gt: $periodStartUnix_gt, periodStartUnix_lt: $periodStartUnix_lt}, orderby: periodStartUnix) {
            periodStartUnix
            liquidity
            sqrtPrice
            token0Price
            token1Price
            tick
            feeGrowthGlobal0X128
            feeGrowthGlobal0X128
            tvlUSD
            volumeToken0
            volumeToken1
            volumeUSD
            feesUSD
            txCount
            open
            high
            low
            close
        }
        }
    '''
    variables = {"periodStartUnix_gt": begin, 'periodStartUnix_lt': end, "pool": pool_id }
    res = query_client(url, query, variables)
    data = pd.json_normalize(res['data']['poolHourDatas'])
    
    return data
