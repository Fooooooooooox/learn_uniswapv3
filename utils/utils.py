import math
import numpy as np
import pandas as pd

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Utils'''
'''
price: 合约里的汇率(token1/token0)
sqrtPrice: 合约中记录的价格, 格式是sqrtX96
realPrice: 现实生活使用的价格(经过decimal转换)
'''

class utils:
    @staticmethod
    def sqrtPrice2Price(self, sqrtPrice):
        price = (sqrtPrice / (2**96) ) ** 2
        return price

    def price2sqrtPrice(self, price):
        sqrtPrice = (price ** 0.5) * (2 ** 96)
        return sqrtPrice

    def tickIndex2Price(self, tickIndex):
        price = 1.0001 ** tickIndex
        return price

    def price2RealPrice(self, price, decimal0, decimal1):
        realPrice = price * (10 ** (decimal0 - decimal1))
        return realPrice

    def realPrice2Price(self, realPrice, decimal0, decimal1):
        price = realPrice / (decimal0 - decimal1)
        return price

    def price2TickIndex(self, price):
        index = math.log(price, 1.0001)
        return index

    def nearestTick(self, currentTick, tickSpacing):
        modulus = currentTick // tickSpacing
        remainder = currentTick % tickSpacing
        nearestTick = modulus*tickSpacing if remainder < (tickSpacing/2) else (modulus+1)*tickSpacing
        return nearestTick

    # price 是未经过decimal转换的，正常形式的价格（可以用tickIndex2Price计算出来）
    def calculateLiquidity(self, token0_amount, token1_amount, price_low, price_upper, decimal0, decimal1):
        l1 = ((token0_amount * (10 ** decimal0)) * (price_low ** 0.5) * (price_upper ** 0.5)) / ((price_upper ** 0.5) - (price_low ** 0.5))
        l2 = (token1_amount * (10 ** decimal1)) / ((price_upper ** 0.5) - (price_low ** 0.5))
        l = np.minimum(l1, l2)
        return l
    
    def moving_average(self, data, window_size):
        ma_data = data.rolling(window=window_size).mean()
        # 去掉NaN值
        ma_data = ma_data.dropna()
        return ma_data

    def calculate_bollinger_bands(self, price_series, window_size=20, num_std=2):
        """
        计算布林带
        :param price_series: 包含价格时间序列数据的Series
        :param window_size: 移动平均窗口大小
        :param num_std: 标准差倍数
        :return: 包含中轨、上轨、下轨价格的dataframe
        """
        # 将价格数据转换为dataframe，并计算移动平均和标准差
        df = pd.DataFrame({'price': price_series}, index=price_series.index)
        rolling_mean = df['price'].rolling(window=window_size).mean()
        rolling_std = df['price'].rolling(window=window_size).std()

        # 计算上轨和下轨价格
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)

        # 保存中轨、上轨、下轨价格到dataframe中
        df['middle_band'] = rolling_mean
        df['upper_band'] = upper_band
        df['lower_band'] = lower_band

        return df
    
    def calculate_current_position0(self, liquidity, price):
        return liquidity / (price ** 0.5)
    
    def calculate_current_position1(self, liquidity, price):
        return liquidity * (price ** 0.5)
    
    def calculate_fullRange_liquidity(self, token0_amount, token1_amount, decimal0, decimal1):
        return (token0_amount * (10 ** decimal0) * token1_amount * (10 ** decimal1)) ** 0.5