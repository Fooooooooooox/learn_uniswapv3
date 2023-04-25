from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

def roi(amount_begin, amount_end, duration_days):
    roi = (amount_end - amount_begin) / amount_begin
    anualized_roi = (1 + roi) ** (365 / duration_days) - 1
    return roi, anualized_roi

def volatility(value_series):
    return value_series.std()

def sharpRatio(roi, volatility, rf = 0):
    return roi - rf / volatility

# def calculateValueSeries(merged_data):

