from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from importlib import reload

# 导入 Config 类
import poolData.config
config = poolData.config.Config()

reload(poolData.config)
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''GraphQl client'''

class QueryClient:
    def with_url(url):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(url, **kwargs)
            return wrapper
        return decorator

    def query_client(url,query,variables):
        res = QueryClient.requests_retry_session().post(url, json={'query': query, 'variables': variables})

        return res.json()

    def query_with_pagination(url, base_query, variables, data_key, cursor_key, page_size=1000):
        all_data = []
        cursor = None
        variables.update({"first": page_size})

        while True:
            query = f'''
                query {base_query}
            '''
            if cursor is not None:
                variables.update({cursor_key + "_gt": cursor})

            res = QueryClient.query_client(url, query, variables)

            if res.get('errors'):
                error_message = res['errors'][0]['message']
                print(f"Error: {error_message}")
                break

            data = pd.json_normalize(res['data'][data_key])
            if len(data) > 0:
                all_data.append(data)
                cursor_type = type(variables[cursor_key + "_gt"])
                cursor = cursor_type(data.iloc[-1][cursor_key])
                print("this is the cursor:", cursor)
                time.sleep(1)  # 添加延迟以防止对 API 的过多请求
            else:
                break

        if len(all_data) == 0:
            return pd.DataFrame()
        elif len(all_data) == 1:
            return all_data[0]
        else:
            return pd.concat(all_data, ignore_index=True)

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
'''Query'''
class SwapDataQuery:
    api_url_free = config.get_api_url_free()

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '''Query all swaps in a pool in a defined time range'''
    @QueryClient.with_url(api_url_free)
    # sqrtPriceX96_gte and sqrtPriceX96_lte are set to max range: (0, 2^192)
    def query_swaps(url, begin, end, pool_id, sqrtPriceX96_gte="0", sqrtPriceX96_lte="6277101735386680763835789423207666416102355444464034512896"):

        base_query = '''
            query ($pool: String!, $timestamp_gt: Int!, $timestamp_lt: Int!, $sqrtPriceX96_gte: String, $sqrtPriceX96_lte: String, $first: Int, $id_gt: String) {
                swaps(where: {pool: $pool, timestamp_gt: $timestamp_gt, timestamp_lt: $timestamp_lt, sqrtPriceX96_gte: $sqrtPriceX96_gte, sqrtPriceX96_lte: $sqrtPriceX96_lte, id_gt: $id_gt}, orderby: id, orderDirection: asc, first: $first) {
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

        variables = { "pool": pool_id, "timestamp_gt": begin, 'timestamp_lt': end, "sqrtPriceX96_gte": sqrtPriceX96_gte, "sqrtPriceX96_lte": sqrtPriceX96_lte, "id_gt": ""}
        data_key = 'swaps'
        cursor_key = 'id'
        return QueryClient.query_with_pagination(url, base_query, variables, data_key, cursor_key)


    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '''Query liquidity data for a pool'''
    @QueryClient.with_url(api_url_free)
    def query_liquidity(url, begin, end, pool_id, sqrtPrice_gt="0", sqrtPrice_lt="6277101735386680763835789423207666416102355444464034512896"):
        base_query = '''
            query ($pool: String!, $periodStartUnix_gt: Int!, $periodStartUnix_lt: Int!, $sqrtPrice_gt: String, $sqrtPrice_lt: String, $first: Int) {
            poolHourDatas(where: {pool: $pool, periodStartUnix_gt: $periodStartUnix_gt, periodStartUnix_lt: $periodStartUnix_lt, sqrtPrice_gt: $sqrtPrice_gt, sqrtPrice_lt: $sqrtPrice_lt}, orderby: periodStartUnix, orderDirection: asc, first: $first) {
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
        data_key = 'poolHourDatas'
        cursor_key = 'periodStartUnix'
        return QueryClient.query_with_pagination(url, base_query, variables, data_key, cursor_key)


    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '''Query all initialized ticks in a pool'''
    @QueryClient.with_url(api_url_free)
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
        res = QueryClient.query_client(url, query, variables)
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
            just named a few that are available here:
            id
            liquidity
            pool__liquidity
            pool__sqrtPrice
    '''
    @QueryClient.with_url(api_url_free)
    def query_positions(url, pool_id, block_gte=0, limit=None, orderBy=None):

        query = '''
            query ($pool_id: String!, $block_gte: Int, $first: Int, $orderBy: String) {
                positions(where: {pool: $pool_id, _change_block: {number_gte: $block_gte}}, first: $first, orderBy: $orderBy) {
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
        print(f"pool_id: {pool_id} - type: {type(pool_id)}")

        variables = { "pool_id": pool_id, "block_gte": block_gte, "first": limit, "orderBy": orderBy}
        res = QueryClient.query_client(url, query, variables)
        if res.get('errors'):
            error_message = res['errors'][0]['message']
            print(f"Error: {error_message}")
            return error_message
        data = pd.json_normalize(res['data']['positions'])
        
        return data

    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '''Query a specific position by position_id'''

    @QueryClient.with_url(api_url_free)
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
        res = QueryClient.query_client(url, query, variables)
        if res.get('errors'):
            error_message = res['errors'][0]['message']
            print(f"Error: {error_message}")
            return error_message
        data = pd.json_normalize(res['data']['position'])
        
        return data


    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    '''Query position snapshots by position_id'''
    @QueryClient.with_url(api_url_free)
    def query_position_snaps(url, position_id, begin_block, current_block=0):
        position_id_begin = position_id + "#" + begin_block
        if current_block == 0:
            current_block = begin_block
        position_id_current = position_id + "#" + current_block
        query = '''
            query ($position_id_begin: String, $position_id_current: String) {
            positionSnapshots(id: $position_id_current, where: {id: $position_id_begin}) {
                id
                position {
                id
                liquidity
                depositedToken0
                depositedToken1
                }
                blockNumber
                timestamp
                liquidity
                depositedToken0
                depositedToken1
            }
            }

        '''
        variables = { "position_id_begin": position_id_begin, "position_id_current": position_id_current}
        res = QueryClient.query_client(url, query, variables)
        if res.get('errors'):
            error_message = res['errors'][0]['message']
            print(f"Error: {error_message}")
            return error_message
        data = pd.json_normalize(res['data']['positionSnapshots'])
        
        return data