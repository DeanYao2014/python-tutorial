# 3.1 迭代器与生成器深度 —— 代码示例 (Python 3.12+)
"""
涵盖：
- for 循环脱糖：iter() + next() + StopIteration
- 迭代器协议全实现（Iterable vs Iterator 分离）
- 生成器内部状态：gi_frame, gi_code, gi_running
- 生成器表达式 vs 列表推导式：内存对比
- yield from 委托与展平
- send(), throw(), close() 双向通信管道
- 生成器状态机：TCP 握手模拟
- 惰性无限序列：fibonacci + 素数筛
- iter(callable, sentinel) 模式
"""

import sys
import traceback
from types import GeneratorType


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. for 循环脱糖：iter + next + StopIteration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_for_desugaring():
    """for x in obj 的完整展开"""
    nums = [1, 2, 3]

    # for x in nums: print(x)
    # 等价于：
    it = iter(nums)                          # it = nums.__iter__()
    while True:
        try:
            x = next(it)                     # x = it.__next__()
            print(f"  取值: {x}")
        except StopIteration:
            print("  StopIteration → 循环结束")
            break

    # 验证：for 会自动捕获 StopIteration，不会传播给调用者
    print("  for 循环正常结束，没有异常外溢")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 迭代器协议全实现：Iterable vs Iterator 严格分离
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MyRangeIterator:
    """迭代器：记住了遍历进度，只能用一次"""
    def __init__(self, start: int, end: int):
        self.current = start
        self.end = end

    def __iter__(self):
        return self                              # 迭代器返回自身

    def __next__(self):
        if self.current >= self.end:
            raise StopIteration
        value = self.current
        self.current += 1
        return value


class MyRange:
    """可迭代对象：每次 iter() 返回全新的迭代器"""
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __iter__(self):
        return MyRangeIterator(self.start, self.end)  # 每次新建迭代器

    def __repr__(self):
        return f"MyRange({self.start}, {self.end})"


def demo_iterable_vs_iterator():
    """Iterable vs Iterator：核心区别演示"""
    r = MyRange(1, 4)

    # r 是可迭代对象，不是迭代器
    print("MyRange 有 __iter__:", hasattr(r, '__iter__'))
    print("MyRange 有 __next__:", hasattr(r, '__next__'))

    # 每次 iter() 返回全新迭代器 → 可以多次遍历
    print("第一次遍历:", list(r))                  # [1, 2, 3]
    print("第二次遍历:", list(r))                  # [1, 2, 3] — 还是满的

    # 迭代器本身只能消费一次
    it = iter(r)
    print("迭代器第一次:", list(it))               # [1, 2, 3]
    print("迭代器第二次:", list(it))               # [] — 已耗尽

    # 迭代器就是它自己的__iter__返回
    it2 = iter(r)
    print("迭代器 __iter__ 返回自己:", it2.__iter__() is it2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. iter(callable, sentinel)：C 风格哨兵模式的 Python 化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_iter_sentinel():
    """iter(func, sentinel) 的两种经典用法"""
    import io

    # 用法 1：分块读取直到文件末尾
    data = b"hello world this is a test"
    buf = io.BytesIO(data)

    print("分块读取 (4 bytes):")
    for chunk in iter(lambda: buf.read(4), b''):
        print(f"  {chunk!r}")

    # 用法 2：读取用户输入直到 'quit'
    # for line in iter(input, 'quit'):
    #     print(f"> {line}")
    print("(iter(input, 'quit') 需交互环境，此处省略)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 生成器函数：yield 的本质——保存整个栈帧
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def simple_gen():
    """最小生成器"""
    print("  生成器开始")
    yield 1
    print("  yield 1 之后")
    yield 2
    print("  yield 2 之后")
    yield 3
    print("  生成器结束")


def demo_generator_internals():
    """窥探生成器对象的内部状态"""
    g = simple_gen()
    print("simple_gen 类型:", type(g))
    print("是否是生成器:", isinstance(g, GeneratorType))

    # gi_frame: 当前执行帧（挂起时为 yield 所在帧，耗尽后为 None）
    # gi_code:  编译后的字节码对象
    # gi_running: 是否正在执行（0=未运行/挂起, 1=正在运行）
    # gi_yieldfrom: 如果正在从子生成器 yield from，指向它

    print("\n创建后:")
    print("  gi_running:", g.gi_running)
    print("  gi_frame 存在:", g.gi_frame is not None)
    print("  gi_code.co_name:", g.gi_code.co_name)

    print("\n第一次 next():")
    val = next(g)
    print(f"  yield 返回值: {val}")
    print(f"  gi_running: {g.gi_running}")
    print(f"  gi_frame.f_lineno (挂起行): {g.gi_frame.f_lineno}")

    print("\n第二次 next():")
    val = next(g)
    print(f"  yield 返回值: {val}")

    print("\n第三次 next()——拿最后一个值:")
    val = next(g)
    print(f"  yield 返回值: {val}")

    print("\n第四次 next()——触发 StopIteration:")
    try:
        next(g)
    except StopIteration:
        print("  StopIteration 被触发")
        print(f"  gi_frame: {g.gi_frame}")      # None — 帧已清除
        print(f"  gi_running: {g.gi_running}")  # 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 生成器表达式 vs 列表推导式：内存对决
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_memory_comparison():
    """生成器表达式：零初始内存开销"""
    n = 1_000_000

    # 列表推导式：一次性创建 100 万个元素
    # list_comp = [x * 2 for x in range(n)]  # ~8MB 内存

    # 生成器表达式：零起始内存，惰性求值
    gen_expr = (x * 2 for x in range(n))

    print(f"生成器表达式大小: {sys.getsizeof(gen_expr)} bytes")
    # 典型输出：~200 bytes —— 只存了帧信息，不存数据

    # 计算前 5 个时不必先生成 100 万
    first_five = [next(gen_expr) for _ in range(5)]
    print(f"前 5 个值: {first_five}")
    print("(剩下 999,995 个值从未被计算)")

    # 何时用哪种？
    # 生成器表达式：数据量大、只需要遍历一次、管道处理
    # 列表推导式：需要索引、多次遍历、数据量小


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. yield from：委托子生成器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sub_generator(start: int, end: int):
    """子生成器：产出一段连续整数"""
    for i in range(start, end):
        print(f"  [子生成器] 产出 {i}")
        received = yield i
        print(f"  [子生成器] 收到: {received}")


def delegating_gen():
    """委托生成器：用 yield from 把控制权交给子生成器"""
    print("[委托] 开始，委托 0..2")
    result = yield from sub_generator(0, 3)   # result = 子生成器的 return 值
    print(f"[委托] 子生成器返回: {result}")
    print("[委托] 产出自己的值")
    yield "done"


def demo_yield_from():
    """展示 yield from 的委托与双向通信"""
    g = delegating_gen()
    print("启动:")
    val = next(g)                               # 启动，自动进入 sub_generator
    print(f"  next() → {val}\n")

    print("send('AAA'):")
    val = g.send("AAA")                         # send 直接送到子生成器
    print(f"  g.send('AAA') → {val}\n")

    print("send('BBB'):")
    try:
        val = g.send("BBB")                     # 最后一次 send 到子生成器
        print(f"  g.send('BBB') → {val}")
    except StopIteration:
        pass                                    # 委托生成器会继续


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. yield from 展平嵌套结构
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def flatten(nested):
    """用 yield from 优雅展平任意嵌套"""
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. send(), throw(), close() —— 双向通信
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def echo_gen():
    """一个能接收、能产出的生成器——协程的雏形"""
    print("  [echo] 初始化")
    while True:
        received = yield                          # 等待 send 送值过来
        print(f"  [echo] 收到: {received!r}")
        if received == "STOP":
            return "Bye"                          # return 值放入 StopIteration.value
        yield f"ECHO: {received}"                # 返回加工后的值


def demo_send():
    """generator.send(value) —— 把值送入生成器内部"""
    g = echo_gen()
    next(g)                                       # 必须先启动到第一个 yield

    print("send('hello'):")
    val = g.send("hello")
    print(f"  得到: {val}\n")

    print("send('world'):")
    val = g.send("world")
    print(f"  得到: {val}\n")

    print("send('STOP'):")
    try:
        g.send("STOP")
    except StopIteration as e:
        print(f"  StopIteration.value = {e.value!r}")


def demo_throw():
    """generator.throw(exc) —— 在 yield 点注入异常"""
    def fragile_gen():
        try:
            yield 1
        except ValueError as e:
            print(f"  生成器内捕获: {e}")
            yield "recovered"
        yield 2

    g = fragile_gen()
    print("next():", next(g))                    # 1

    print("throw(ValueError):")
    val = g.throw(ValueError, "注入的异常")
    print(f"  throw() 返回: {val}")               # "recovered"

    print("next():", next(g))                    # 2


def demo_close():
    """generator.close() —— 优雅关闭生成器"""
    def cleanup_gen():
        try:
            while True:
                yield "working"
        finally:
            print("  [清理] 释放资源，关闭连接")

    g = cleanup_gen()
    print("next():", next(g))                    # "working"
    print("调用 close():")
    g.close()
    # finally 块被执行，GeneratorExit 不会传播
    print("  close() 返回，生成器已终止")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 模式：生成器作为轻量状态机
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tcp_state_machine():
    """用生成器模拟 TCP 三次握手状态机"""
    state = "CLOSED"
    print(f"[状态机] 初始: {state}")

    # CLOSED → LISTEN
    event = yield state
    if event == "listen":
        state = "LISTEN"
        print(f"[状态机] → {state}")

    # LISTEN → SYN_RCVD
    event = yield state
    if event == "syn":
        state = "SYN_RCVD"
        print(f"[状态机] → {state}")

    # SYN_RCVD → ESTABLISHED (收到 ACK)
    event = yield state
    if event == "ack":
        state = "ESTABLISHED"
        print(f"[状态机] → {state}")

    yield state  # 最终状态

    # 对比：传统写法需要 class + 多个 if/elif 分支 + self.state 字段
    # 生成器写法：状态就是当前执行位置，事件就是 send 的值


def demo_state_machine():
    sm = tcp_state_machine()
    next(sm)                        # 初始化，拿到 CLOSED
    sm.send("listen")               # CLOSED → LISTEN
    sm.send("syn")                  # LISTEN → SYN_RCVD
    final = sm.send("ack")          # SYN_RCVD → ESTABLISHED（send 返回 yield 的值）
    print(f"  最终状态: {final}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 惰性无限序列
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fibonacci():
    """用生成器实现的斐波那契数列——无限、惰性"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def demo_fibonacci():
    fib = fibonacci()
    print("前 10 个 Fibonacci:")
    print([next(fib) for _ in range(10)])


def primes():
    """埃拉托斯特尼筛法生成素数——惰性无限序列"""
    known_primes: list[int] = []
    n = 2
    while True:
        # 检查 n 是否被已有素数整除
        if all(n % p != 0 for p in known_primes):
            known_primes.append(n)
            yield n
        n += 1


def demo_primes():
    p = primes()
    print("前 10 个素数:")
    print([next(p) for _ in range(10)])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("=" * 60)
    print("1. for 循环脱糖")
    print("=" * 60)
    demo_for_desugaring()

    print("\n" + "=" * 60)
    print("2. Iterable vs Iterator 严格分离")
    print("=" * 60)
    demo_iterable_vs_iterator()

    print("\n" + "=" * 60)
    print("3. iter(callable, sentinel)")
    print("=" * 60)
    demo_iter_sentinel()

    print("=" * 60)
    print("4. 生成器内部状态")
    print("=" * 60)
    demo_generator_internals()

    print("\n" + "=" * 60)
    print("5. 生成器表达式 vs 列表推导式内存对比")
    print("=" * 60)
    demo_memory_comparison()

    print("\n" + "=" * 60)
    print("6. yield from 委托")
    print("=" * 60)
    demo_yield_from()

    print("\n" + "=" * 60)
    print("7. yield from 展平嵌套")
    print("=" * 60)
    result = list(flatten([1, [2, [3, 4]], 5, [6, [7, [8]]]]))
    print(f"flatten 结果: {result}")

    print("\n" + "=" * 60)
    print("8. send() 双向通信")
    print("=" * 60)
    demo_send()

    print("=" * 60)
    print("9. throw() 注入异常")
    print("=" * 60)
    demo_throw()

    print("=" * 60)
    print("10. close() 优雅关闭")
    print("=" * 60)
    demo_close()

    print("\n" + "=" * 60)
    print("11. 状态机 —— 生成器模拟 TCP 握手")
    print("=" * 60)
    demo_state_machine()

    print("\n" + "=" * 60)
    print("12. 惰性无限序列")
    print("=" * 60)
    demo_fibonacci()
    demo_primes()
