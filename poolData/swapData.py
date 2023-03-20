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
            feeGrowthGlobal1X128
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


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query all initialized ticks in a pool'''
@with_url(API_URL_FREE)
def query_ticks(url, poolAddress):

    query = '''
        query ($poolAddress: String!) {
            ticks(where: {poolAddress: $poolAddress}) {
                tickIdx
                liquidityGross
                liquidityNet
                price0
                price1
                volumeToken0
                volumeToken1
                volumeUSD
                untrackedVolumeUSD
                feesUSD
                collectedFeesToken0
                collectedFeesToken1
                collectedFeesUSD
                createdAtTimestamp
                liquidityProviderCount
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
        }
    '''
    variables = { "poolAddress": poolAddress}
    res = query_client(url, query, variables)
    data = pd.json_normalize(res['data']['ticks'])
    
    return data


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query all positions in a pool
Args:
    pool: pool address
    block_gte: query txs after the block number
    limit: the number of records you want
    block
    orderBy: check all available orderBy params here: https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3/graphql?query=query+%7B%0A++positions%28where%3A+%7Bpool%3A%220x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640%22%7D%2C+first%3A+10%2C+orderBy%3A+id%29%7B%0A++++id%0A++++%23+owner%0A++++%23+token0+%7B%0A++++%23+++id%0A++++%23+%7D%0A++++%23+token1+%7B%0A++++%23+++id%0A++++%23+%7D%0A++++%23+tickLower+%7B%0A++++%23+++id%0A++++%23+%7D%0A++++%23+tickUpper+%7B%0A++++%23+++id%0A++++%23+%7D%0A++++%23+liquidity%0A++++%23+depositedToken0%0A++++%23+depositedToken1%0A++++%23+withdrawnToken0%0A++++%23+withdrawnToken1%0A++++%23+collectedFeesToken0%0A++++%23+collectedFeesToken1%0A++++%23+transaction+%7B%0A++++%23+++id%0A++++%23+%7D%0A++++%23+feeGrowthInside0LastX128%0A++++%23+feeGrowthInside1LastX128%0A++%7D%0A%7D
        just named a few that are available here：
        id
        liquidity
        pool__liquidity
        pool__sqrtPrice
'''
@with_url(API_URL_FREE)
def query_positions(url, pool, block_gte=0, limit=None, orderBy=None):

    query = '''
        query ($pool: String!, $block_gte: Int, $first: Int, $orderBy: String) {
            positions(where: {pool: $pool, _change_block: {number_gte: $block_gte}}, first: $first, orderBy: $orderBy) {
                id
                owner
                token0 {
                id
                }
                token1 {
                id
                }
                tickLower {
                id
                }
                tickUpper {
                id
                }
                liquidity
                depositedToken0
                depositedToken1
                withdrawnToken0
                withdrawnToken1
                collectedFeesToken0
                collectedFeesToken1
                transaction {
                id
                }
                feeGrowthInside0LastX128
                feeGrowthInside1LastX128
            }
        }
    '''
    variables = { "pool": pool, "block_gte": block_gte, "first": limit, "orderBy": orderBy}
    res = query_client(url, query, variables)
    data = pd.json_normalize(res['data']['positions'])
    
    return data

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query a specific position by position_id'''

@with_url(API_URL_FREE)
def query_position(url, position_id):

    query = '''
        query ($position_id: Int) {
            position(id: $position_id){
                id
                owner
                token0 {
                id
                }
                token1 {
                id
                }
                tickLower {
                id
                }
                tickUpper {
                id
                }
                liquidity
                depositedToken0
                depositedToken1
                withdrawnToken0
                withdrawnToken1
                collectedFeesToken0
                collectedFeesToken1
                transaction {
                id
                }
                feeGrowthInside0LastX128
                feeGrowthInside1LastX128
            }
        }
    '''
    variables = { "position_id": position_id}
    res = query_client(url, query, variables)
    data = pd.json_normalize(res['data']['position'])
    
    return data


