"""2.4 可迭代与可调用对象 —— 完整演示

涵盖：
- 迭代器协议：__iter__ + __next__（4.1）
- Iterable vs Iterator 区别（4.1）
- __getitem__ 降级路径（4.2）
- 生成器 vs 手写迭代器（4.3）
- __call__ 让实例可调用（4.4）
- 类装饰器（4.4）
- StringIO 实战——类文件对象（4.5）
- iter(func, sentinel) 模式（4.6）
"""

import functools
import time
import random


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.1 迭代器协议：手写 Countdown 迭代器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Countdown:
    """倒计时迭代器——展示 __iter__ + __next__"""
    def __init__(self, start: int):
        self.current = start

    def __iter__(self):
        return self            # 迭代器返回自身

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1


def demo_iterator_protocol():
    """展示迭代器的完整协议和 Iterable vs Iterator 区别"""
    print("Countdown(3):", list(Countdown(3)))  # [3, 2, 1]

    # 列表是可迭代对象，不是迭代器
    nums = [1, 2, 3]
    print("list 有 __iter__:", hasattr(nums, '__iter__'))    # True
    print("list 有 __next__:", hasattr(nums, '__next__'))    # False

    # 每次 iter(list) 返回新迭代器——可以多次遍历
    it1 = iter(nums)
    it2 = iter(nums)
    print("it1:", list(it1))    # [1, 2, 3]
    print("it2:", list(it2))    # [1, 2, 3] — it2 未受影响

    # 迭代器自身只能消费一次
    it3 = iter(nums)
    print("第一次:", list(it3))  # [1, 2, 3]
    print("第二次:", list(it3))  # [] — 迭代器已经耗尽


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.2 __getitem__ 降级路径
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OldStyleIterable:
    """没有 __iter__——Python 降级到 __getitem__"""
    def __init__(self, data):
        self.data = data

    def __getitem__(self, index: int):
        if index >= len(self.data):
            raise IndexError    # Python 靠 IndexError 判断结束
        return self.data[index]


def demo_getitem_fallback():
    """展示没有 __iter__ 时 Python 用 __getitem__ 遍历"""
    obj = OldStyleIterable(['a', 'b', 'c'])
    result = []
    for item in obj:
        result.append(item)
    print("__getitem__ 降级遍历:", result)  # ['a', 'b', 'c']

    # 同时实现二者的优先顺序
    class Both:
        data = [1, 2, 3]

        def __getitem__(self, i):
            return f"getitem_{self.data[i]}"

        def __iter__(self):
            return iter(f"iter_{x}" for x in self.data)

    print("__iter__ 优先:", list(Both()))  # ['iter_1', 'iter_2', 'iter_3']


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.3 生成器——最简单的迭代器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 手写迭代器（对比基准）
class CountdownClass:
    def __init__(self, start):
        self.current = start
    def __iter__(self):
        return self
    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

# 生成器函数——语义完全等价
def countdown_gen(start: int):
    while start > 0:
        yield start
        start -= 1


def flatten(nested):
    """yield from 递归展平嵌套结构"""
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item


def demo_generators():
    """展示生成器与手写迭代器的等价性"""
    print("手写类:  ", list(CountdownClass(3)))   # [3, 2, 1]
    print("生成器:  ", list(countdown_gen(3)))      # [3, 2, 1]

    # yield from 展平
    data = [1, [2, 3], [[4, 5], 6]]
    print("展平结果:", list(flatten(data)))         # [1, 2, 3, 4, 5, 6]

    # 生成器表达式
    squares = (x * x for x in range(5))
    print("生成器表达式:", list(squares))           # [0, 1, 4, 9, 16]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.4 __call__：让实例成为"函数"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Counter:
    """有状态的"函数"——每调一次计数加一"""
    def __init__(self, start: int = 0):
        self.count = start
    def __call__(self) -> int:
        self.count += 1
        return self.count


class RateLimiter:
    """限流器——基于 __call__ 维护状态"""
    def __init__(self, max_calls: int, per_seconds: float = 1.0):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self._calls: list[float] = []

    def __call__(self) -> bool:
        now = time.time()
        self._calls = [t for t in self._calls if now - t < self.per_seconds]
        if len(self._calls) < self.max_calls:
            self._calls.append(now)
            return True
        return False


# 用 __call__ 实现的装饰器——实例属性保存配置
class Retry:
    """装饰器：失败自动重试"""
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    print(f"  第 {attempt + 1} 次失败: {e}")
            raise last_exc  # type: ignore
        return wrapper


def demo_callable():
    """展示 __call__ 的各种用法"""
    c = Counter(10)
    print("Counter:", [c() for _ in range(3)])  # [11, 12, 13]

    # 限流器
    limiter = RateLimiter(max_calls=3, per_seconds=1.0)
    results = [limiter() for _ in range(5)]
    print("RateLimiter:", results)  # 前 3 True, 后 2 False

    # 类装饰器
    @Retry(max_attempts=3)
    def flaky_func():
        if random.random() < 0.6:
            raise ConnectionError("网络故障")
        return "成功"

    for i in range(3):
        try:
            print(f"调用 flaky_func #{i}:", flaky_func())
        except ConnectionError:
            print(f"调用 flaky_func #{i}: 最终失败")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.5 实战：StringIO —— 类文件对象
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StringIO:
    """一个文件对象的简化实现——支持 for 迭代 + read()"""
    def __init__(self, content: str):
        self._lines = content.splitlines(keepends=True)
        self._pos = 0

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if self._pos >= len(self._lines):
            self._pos = 0     # 重置以便复用——实际文件需要 seek(0)
            raise StopIteration
        line = self._lines[self._pos]
        self._pos += 1
        return line

    def read(self, size: int = -1) -> str:
        remaining = ''.join(self._lines[self._pos:])
        if size == -1 or size >= len(remaining):
            result, self._pos = remaining, len(self._lines)
        else:
            result, self._pos = remaining[:size], self._pos
        return result

    def __repr__(self) -> str:
        visible = self._lines[self._pos:self._pos + 2]
        return f"StringIO({visible!r}, pos={self._pos})"


def demo_stringio():
    """展示类文件对象的迭代器用法"""
    text = "hello\nworld\npython"
    io = StringIO(text)
    print("逐行迭代:")
    for line in io:
        print(f"  {repr(line)}")

    # 一次性读取
    io2 = StringIO(text)
    print(f"read() 一次性: {repr(io2.read())}")

    # 迭代器耗尽
    io3 = StringIO(text)
    print("第一次遍历:", [line.strip() for line in io3])
    print("第二次遍历:", [line.strip() for line in io3])  # 空——已耗尽


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.6 iter(func, sentinel) 模式
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_sentinel():
    """展示 iter(callable, sentinel) 用法"""
    # 模拟：从数据源逐条读取，直到读到 None
    data_source = iter([10, 20, 30, None, 40])
    results = []
    for item in iter(lambda: next(data_source), None):
        results.append(item)
    print("iter sentinel 模式:", results)  # [10, 20, 30]

    # 另一个例子：生成递增序号直到 5
    counter_state = 0

    def next_counter():
        nonlocal counter_state
        counter_state += 1
        return counter_state

    print("计数到 5:", list(iter(next_counter, 5)))  # [1, 2, 3, 4]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("=" * 55)
    print("4.1 迭代器协议：__iter__ + __next__")
    print("=" * 55)
    demo_iterator_protocol()

    print("\n" + "=" * 55)
    print("4.2 __getitem__ 降级路径")
    print("=" * 55)
    demo_getitem_fallback()

    print("\n" + "=" * 55)
    print("4.3 生成器——最简单的迭代器")
    print("=" * 55)
    demo_generators()

    print("\n" + "=" * 55)
    print("4.4 __call__：让实例成为'函数'")
    print("=" * 55)
    demo_callable()

    print("\n" + "=" * 55)
    print("4.5 实战：StringIO 类文件对象")
    print("=" * 55)
    demo_stringio()

    print("\n" + "=" * 55)
    print("4.6 iter(func, sentinel) 模式")
    print("=" * 55)
    demo_sentinel()
