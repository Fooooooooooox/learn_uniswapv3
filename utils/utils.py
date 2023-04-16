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