from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from datetime import datetime
import requests

API_URL_FREE = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'