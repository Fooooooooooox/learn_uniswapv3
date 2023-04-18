import math
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'''Utils'''
'''
price: 合约里的汇率(token1/token0)
sqrtPrice: 合约中记录的价格, 格式是sqrtX96
realPrice: 现实生活使用的价格(经过decimal转换)
'''

class utils:
    
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
    def calculateLiquidity(self, token0_amount, token1_amount, price_low, price_upper):
        l1 = (token0_amount * (price_low ** 0.5) * (price_upper ** 0.5)) / ((price_upper ** 0.5) - (price_low ** 0.5))
        l2 = token1_amount / ((price_upper ** 0.5) - (price_low ** 0.5))
        l = min(l1, l2)
        return l