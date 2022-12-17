## 什么是tick spacing？

tick spacing的存在是为了减少合约的精度，否则存储所有的tick和价格会非常耗费gas。

对于汇率波动很小的币对来说，价格一点点的波动就会带来很大的改变。比如usdt和usdc币对，由于他们都是锚定美元的稳定币，所以汇率波动非常小，这时候就需要价格变化的精度特别高，tick spacing需要设置的很小。
对于汇率波动率大的币对，他们对价格精度的要求比较低，tick spacing可以很大，来简化合约，减少gas。

另外，汇率波动小的币对的手续费也小，因为风险低


## tick spacing  如何运作？

摘自白皮书：

```
Not every tick can be initialized. The pool is instantiated with a
parameter, tickSpacing (𝑡𝑠 ); only ticks with indexes that are divisible by tickSpacing can be initialized. For example, if tickSpacing
is 2, then only even ticks (...-4, -2, 0, 2, 4...) can be initialized. Small
choices for tickSpacing allow tighter and more precise ranges, but
may cause swaps to be more gas-intensive (since each initialized
tick that a swap crosses imposes a gas cost on the swapper).
```

spacing就是跳过某些tick，不是tick-spacing的整数倍的tick就跳过，不会被初始化。

