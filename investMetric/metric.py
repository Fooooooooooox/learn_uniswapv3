import sys
sys.path.append("../utils") 
from utils.utils import utils

my_utils = utils()


def roi(amount_begin, amount_end, duration_days):
    roi = (amount_end - amount_begin) / amount_begin
    anualized_roi = (1 + roi) ** (365 / duration_days) - 1
    return roi, anualized_roi

def volatility(value_series):
    return value_series.std()

def sharpRatio(roi_amount, volatility_amount, rf = 0):
    return roi_amount - rf / volatility_amount

def metric(merged_data, token0_amount, token1_amount, begin, end, decimal0, decimal1, rf):
    merged_data["fee0_sum"] = merged_data['fee0'].cumsum()
    merged_data["fee1_sum"] = merged_data['fee1'].cumsum()
    # transform X86 into normal number
    merged_data["real_price"] = merged_data["tick"].apply(lambda x: 1/ (my_utils.price2RealPrice(my_utils.tickIndex2Price(merged_data["tick"][0]), decimal0=decimal0, decimal1=decimal1)))
    merged_data["position_value"] = (token0_amount  + merged_data["fee0_sum"]) + (token1_amount + merged_data["fee1_sum"]) * merged_data["real_price"]
    merged_data["position_value0"] = (token0_amount  + merged_data["fee0_sum"])
    merged_data["position_value1"] = (token1_amount + merged_data["fee1_sum"]) * merged_data["real_price"]
    my_volatility = volatility(merged_data["position_value"])
    print("** volatility = ", my_volatility)
    my_roi = roi(merged_data["position_value"][0], merged_data["position_value"].iloc[-1], (end - begin).days)
    print("** roi = ", my_roi)
    sharpe_ratio = sharpRatio(roi_amount=my_roi, volatility_amount=my_volatility, rf=rf)
    print("** sharpe_ratio = ", sharpe_ratio)

