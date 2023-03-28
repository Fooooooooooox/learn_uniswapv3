from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from datetime import datetime
import importlib
import config
importlib.reload(config)
from poolData.config import API_URL_FREE
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time


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

def query_with_pagination(url, base_query, variables, data_key, page_size=1000):
    all_data = []
    cursor = None

    while True:
        query = f'''
            query {base_query}
        '''
        if cursor is not None:
            variables.update({"timestamp_gt": cursor})

        variables.update({"first": page_size})
        res = query_client(url, query, variables)

        if res.get('errors'):
            error_message = res['errors'][0]['message']
            print(f"Error: {error_message}")
            break
        
        data = pd.json_normalize(res['data'][data_key])

        if len(data) > 0:
            all_data.append(data)
            cursor = int(data.iloc[-1]['timestamp'])
            # print("this is the cursor:", cursor)
            time.sleep(1)  # 添加延迟以防止对 API 的过多请求
        else:
            break

    if len(all_data) > 2:
        return pd.concat(all_data, ignore_index=True)
    else:
        all_data

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
# sqrtPriceX96_gte and sqrtPriceX96_lte are set to max range: (0, 2^192)
def query_swaps(url, begin, end, pool_id, sqrtPriceX96_gte="0", sqrtPriceX96_lte="6277101735386680763835789423207666416102355444464034512896"):

    base_query = '''
        query ($pool: String!, $timestamp_gt: Int!, $timestamp_lt: Int!, $sqrtPriceX96_gte: String, $sqrtPriceX96_lte: String, $first: Int) {
            swaps(where: {pool: $pool, timestamp_gt: $timestamp_gt, timestamp_lt: $timestamp_lt, sqrtPriceX96_gte: $sqrtPriceX96_gte, sqrtPriceX96_lte: $sqrtPriceX96_lte}, orderby: timestamp, orderDirection: asc, first: $first) {
            id
            transaction
            timestamp
            pool
            token0
            token1
            sender
            recipient
            origin
            amount0
            amount1
            amountUSD
            sqrtPriceX96
            tick
            logIndex
            }
        }
    '''

    variables = { "pool": pool_id, "timestamp_gt": begin, 'timestamp_lt': end, "sqrtPriceX96_gte": sqrtPriceX96_gte, "sqrtPriceX96_lte": sqrtPriceX96_lte}
    data_key = 'swaps'
    return query_with_pagination(url, base_query, variables, data_key)


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query liquidity data for a pool'''
@with_url(API_URL_FREE)
def query_liquidity(url, begin, end, pool_id, sqrtPrice_gt=None, sqrtPrice_lt=None):
    query = '''
        query ($pool: String!, $periodStartUnix_gt: Int!, $periodStartUnix_lt: Int!, $sqrtPrice_gt: String, $sqrtPrice_lt: String) {
        poolHourDatas(where: {pool: $pool, periodStartUnix_gt: $periodStartUnix_gt, periodStartUnix_lt: $periodStartUnix_lt, sqrtPrice_gt: $sqrtPrice_gt, sqrtPrice_lt: $sqrtPrice_lt}, orderby: periodStartUnix) {
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
    variables = {"periodStartUnix_gt": begin, 'periodStartUnix_lt': end, "pool": pool_id, "sqrtPrice_gt": sqrtPrice_gt, "sqrtPrice_lt":sqrtPrice_lt}
    res = query_client(url, query, variables)
    if res.get('errors'):
        error_message = res['errors'][0]['message']
        print(f"Error: {error_message}")
        return error_message
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
    if res.get('errors'):
        error_message = res['errors'][0]['message']
        print(f"Error: {error_message}")
        return error_message
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
    if res.get('errors'):
        error_message = res['errors'][0]['message']
        print(f"Error: {error_message}")
        return error_message
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
    if res.get('errors'):
        error_message = res['errors'][0]['message']
        print(f"Error: {error_message}")
        return error_message
    data = pd.json_normalize(res['data']['position'])
    
    return data


