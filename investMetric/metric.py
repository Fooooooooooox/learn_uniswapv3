import sys
sys.path.append("../utils") 
import numpy as np
from utils.utils import utils
from tabulate import tabulate

my_utils = utils()


def roi(amount_begin, amount_end, duration_days):
    roi = (amount_end - amount_begin) / amount_begin
    anualized_roi = (1 + roi) ** (365 / duration_days) - 1
    return roi, anualized_roi

def volatility(value_series):
    return value_series.std()

def sharpRatio(roi_amount, volatility_amount, rf = 0):
    return roi_amount - rf / volatility_amount

def maxDrawdown(value_series):
    drawdowns = []
    max_so_far = value_series[0]
    for price in value_series:
        if price > max_so_far:
            max_so_far = price
        drawdowns.append((max_so_far - price) / max_so_far)
    return np.max(drawdowns)

def metric(merged_data, begin, end, decimal0, decimal1, rf, l):
    # calculate fee0_sum and fee1_sum
    merged_data["fee0_sum"] = merged_data['fee0'].cumsum()
    merged_data["fee1_sum"] = merged_data['fee1'].cumsum()

    # calculate current position
    merged_data["price"] = merged_data["tick"].apply(lambda x: my_utils.sqrtPrice2Price(x))
    merged_data["current_position0"] = merged_data["price"].apply(lambda x: my_utils.calculate_current_position0(liquidity=l, price=x)) / (10 ** decimal0)
    merged_data["current_position1"] = merged_data["price"].apply(lambda x: my_utils.calculate_current_position1(liquidity=l, price=x)) / (10 ** decimal1)

    # transform X86 into normal number
    merged_data["real_price"] = merged_data["tick"].apply(lambda x: 1/ (my_utils.price2RealPrice(my_utils.tickIndex2Price(x), decimal0=decimal0, decimal1=decimal1)))
    merged_data["position_value"] = (merged_data["current_position0"]  + merged_data["fee0_sum"]) + (merged_data["current_position1"] + merged_data["fee1_sum"]) * merged_data["real_price"]
    # merged_data["position_value0"] = (token0_amount  + merged_data["fee0_sum"])
    # merged_data["position_value1"] = (token1_amount + merged_data["fee1_sum"]) * merged_data["real_price"]
    my_volatility = volatility(merged_data["position_value"])
    print("** volatility = ", my_volatility)
    my_roi = roi(merged_data["position_value"][0], merged_data["position_value"].iloc[-1], (end - begin).days)[1]
    print("** roi = ", my_roi)
    sharpe_ratio = sharpRatio(roi_amount=my_roi, volatility_amount=my_volatility, rf=rf)
    print("** sharpe_ratio = ", sharpe_ratio)
    max_drawdown = maxDrawdown(merged_data["position_value"])
    print("** max_drawdown = ", max_drawdown)
    data = [['volatility', my_volatility], ['roi', my_roi], ['sharpe_ratio', sharpe_ratio], ['max_drawdown', max_drawdown]]
    print(tabulate(data, headers=['Output', 'Value'], tablefmt='orgtbl'))

