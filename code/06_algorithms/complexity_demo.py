"""
6.1 算法基础与复杂度 — 代码示例
Python 3.12+
"""
import timeit
from collections import deque
from functools import lru_cache
import time

# ──────────────────────────────────────────────
# 1. Python 内置操作的复杂度直观对比
# ──────────────────────────────────────────────

def compare_list_vs_deque(n=100_000):
    """list.pop(0) O(n) vs deque.popleft() O(1)"""
    # 构造数据
    lst = list(range(n))
    dq = deque(range(n))

    # 测试 list.pop(0) — O(n)
    t1 = time.perf_counter()
    for _ in range(1000):
        lst.pop(0)
    t2 = time.perf_counter()
    list_time = t2 - t1

    # 测试 deque.popleft() — O(1)
    t1 = time.perf_counter()
    for _ in range(1000):
        dq.popleft()
    t2 = time.perf_counter()
    deque_time = t2 - t1

    print(f"list.pop(0) 1000次: {list_time:.4f}s (O(n), 每次移动 {n} 个元素)")
    print(f"deque.popleft() 1000次: {deque_time:.6f}s (O(1), 只改指针)")
    print(f"差距: {list_time / deque_time:.0f}x")
    print()


# ──────────────────────────────────────────────
# 2. 用 timeit 精确测量小段代码
# ──────────────────────────────────────────────

def timeit_demo():
    """timeit 自动多次执行并取最佳值，排除系统波动"""
    # 构建成员检查的测试
    setup = "data = list(range(10000))"
    stmt_list = "9999 in data"     # O(n) — 遍历到末尾
    stmt_set  = "9999 in set(data)"  # O(1)

    n = 1000
    t_list = timeit.timeit(stmt_list, setup, number=n)
    t_set  = timeit.timeit(stmt_set, setup, number=n)

    print("成员检查：list O(n) vs set O(1)")
    print(f"  list: {t_list:.6f}s ({n} 次)")
    print(f"  set:  {t_set:.6f}s ({n} 次)")
    print(f"  差距: {t_list / t_set:.0f}x")
    print()


# ──────────────────────────────────────────────
# 3. @lru_cache — 一行代码实现记忆化
# ──────────────────────────────────────────────

def fib_no_cache(n):
    """无缓存的斐波那契 — O(2^n)"""
    if n <= 1:
        return n
    return fib_no_cache(n - 1) + fib_no_cache(n - 2)


@lru_cache(maxsize=None)
def fib_cached(n):
    """有缓存的斐波那契 — O(n)"""
    if n <= 1:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)


def lru_cache_demo():
    print("@lru_cache 效果对比：")
    n = 35
    t1 = time.perf_counter()
    result1 = fib_cached(n)
    t2 = time.perf_counter()
    print(f"  fib_cached({n}) = {result1}, 耗时: {t2 - t1:.6f}s (O(n))")
    print(f"  缓存信息: {fib_cached.cache_info()}")

    # 无缓存版本 n=35 会非常慢，用 n=30 演示
    n2 = 30
    t1 = time.perf_counter()
    result2 = fib_no_cache(n2)
    t2 = time.perf_counter()
    print(f"  fib_no_cache({n2}) = {result2}, 耗时: {t2 - t1:.4f}s (O(2^n))")
    print()


# ──────────────────────────────────────────────
# 4. 常数因子不可忽视 — Python 函数调用开销
# ──────────────────────────────────────────────

def python_function_overhead():
    """函数调用在 Python 中不是免费的"""
    n = 10_000_000

    # 内联操作
    t1 = time.perf_counter()
    total = 0
    for i in range(n):
        total += i
    t2 = time.perf_counter()
    inline_time = t2 - t1

    # 通过函数调用
    def add(a, b):
        return a + b

    t1 = time.perf_counter()
    total = 0
    for i in range(n):
        total = add(total, i)
    t2 = time.perf_counter()
    func_time = t2 - t1

    print("Python 函数调用开销（1000万次循环）：")
    print(f"  内联操作: {inline_time:.3f}s")
    print(f"  函数调用: {func_time:.3f}s")
    print(f"  函数调用慢 {func_time / inline_time:.1f}x")
    print()


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("6.1 算法基础与复杂度 — 代码示例")
    print("=" * 60)
    print()

    compare_list_vs_deque()
    timeit_demo()
    lru_cache_demo()
    python_function_overhead()
