from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from datetime import datetime
import importlib
importlib.reload(poolData.config)
from poolData.config import API_URL, API_URL_FREE
import requests


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''GraphQl client'''

def with_url(url):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(url, *args, **kwargs)
        return wrapper
    return decorator

def query_univ3(url,query_a,params):

    sample_transport=RequestsHTTPTransport(
       url=url,
       verify=True,
       retries=5,)
    client = Client(transport=sample_transport)
    query = gql(query_a)
    response = client.execute(query,variable_values=params)
    
    return response

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Query all swaps in a pool in a defined time range'''
@with_url(API_URL_FREE)
def query_swaps(url, begin, end, pool_id):

    query = '''
        query {
            swaps(where: {pool: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", timestamp_gt: 1672502400, timestamp_lt:1678809600}, orderby: timestamp) {
            id
            amount0
            amount1
            timestamp
            amountUSD
            sqrtPriceX96
            }
        }
    '''
    variables = {"begin": begin, 'end': end, "pool_id": pool_id }
    data = requests.post(url, json={'query': query, 'variables': variables})
    
    return data.json()


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_api_data(timestamp):
    apiUrl = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
    query = """ query uniswap($timestamp:Int)  {
                poolDayDatas(first:1000,where: 
                        {date:$timestamp},
                        orderBy: tvlUSD,
                        orderDirection: desc ){
                        date 
                        pool{
                          id
                          createdAtTimestamp
                          createdAtBlockNumber
                          token0{
                            symbol
                          }
                          token1{
                            symbol
                          }
                          feeTier
                        }
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
                } """
    variables = {'timestamp': timestamp}
    r = requests.post(apiUrl, json={'query': query , 'variables': variables})
    return r.json()