# 装饰器深度解析 — 代码示例 (Python 3.12+)
import time
import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# ============================================================
# 1. 装饰器就是语法糖：func = decorator(func)
# ============================================================

def simple_decorator(func: F) -> F:
    """最简装饰器：原样返回函数（什么都没做）"""
    print(f"  装饰器执行: 包装 {func.__name__}")
    return func

@simple_decorator
def say_hello() -> None:
    print("Hello!")

# 上面等价于：
# say_hello = simple_decorator(say_hello)
# 装饰发生在**函数定义时**，不是在调用时

print("=== 1. 装饰器执行时机 ===")
say_hello()  # 调用时不触发装饰器代码

# ============================================================
# 2. 真正的装饰器：用闭包替换原函数
# ============================================================

def timer(func: F) -> F:
    """计时装饰器 —— 最经典的闭包应用"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] 耗时: {elapsed:.6f}s")
        return result
    return wrapper  # wrapper 闭包捕获了 func

@timer
def slow_add(a: int, b: int) -> int:
    """一个故意很慢的加法"""
    time.sleep(0.5)
    return a + b

print("\n=== 2. 计时装饰器 ===")
result = slow_add(3, 4)
print(f"结果: {result}")
# slow_add 实际上是 wrapper，但 @wraps 保留了 __name__ 和 __doc__
print(f"slow_add.__name__ = {slow_add.__name__}")  # 'slow_add' 而非 'wrapper'
print(f"slow_add.__doc__  = {slow_add.__doc__}")    # 保留了原文档

# ============================================================
# 3. 没有 @wraps 会怎样？
# ============================================================

def bad_decorator(func: F) -> F:
    def wrapper(*args, **kwargs):
        """wrapper 的文档"""
        return func(*args, **kwargs)
    return wrapper

@bad_decorator
def important_func() -> None:
    """重要函数的文档"""
    pass

print(f"\n=== 3. 没有 @wraps 的后果 ===")
print(f"important_func.__name__ = {important_func.__name__}")  # 'wrapper'！
print(f"important_func.__doc__  = {important_func.__doc__}")   # 'wrapper 的文档'！
# 这对调试、文档生成、IDE 智能提示都是灾难

# @wraps 做了什么？简化的等价实现：
# wrapper.__name__ = func.__name__
# wrapper.__doc__ = func.__doc__
# wrapper.__module__ = func.__module__
# wrapper.__wrapped__ = func
# 还要复制 __dict__ 中的属性

# ============================================================
# 4. 参数化装饰器：三层函数嵌套
# ============================================================

def retry(max_attempts: int = 3, delay: float = 1.0):
    """可配置的重试装饰器 —— 最外层接收参数"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise  # 最后一次也失败，传播异常
                    print(f"  第 {attempt} 次失败: {e}，{delay}s 后重试...")
                    time.sleep(delay)
            return None  # unreachable
        return wrapper
    return decorator

# 使用：
# @retry(max_attempts=3, delay=0.5)
# 等价于:
# func = retry(max_attempts=3, delay=0.5)(func)
# 第一步：retry(3, 0.5) → 返回 decorator
# 第二步：decorator(func) → 返回 wrapper

print("\n=== 4. 参数化装饰器 ===")
import random

@retry(max_attempts=3, delay=0.1)
def flaky_api_call() -> str:
    """模拟不稳定的 API 调用"""
    if random.random() < 0.6:
        raise ConnectionError("网络超时")
    return "成功!"

try:
    result = flaky_api_call()
    print(f"API 结果: {result}")
except ConnectionError:
    print("API 重试 3 次后仍失败")

# ============================================================
# 5. 装饰器叠加：从下往上执行
# ============================================================

def bold(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> str:
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper

def italic(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> str:
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper

@bold      # 第二步：bold(italic_wrapper) → bold_wrapper
@italic    # 第一步：italic(say_hi) → italic_wrapper
def say_hi(name: str) -> str:
    return f"Hi {name}"

print(f"\n=== 5. 装饰器叠加 ===")
print(say_hi("Dean"))  # <b><i>Hi Dean</i></b>
# 执行顺序：bold_wrapper → italic_wrapper → say_hi → italic 包裹 → bold 包裹

# ============================================================
# 6. 类装饰器 —— 用 __call__ 实现
# ============================================================

class CountCalls:
    """统计函数被调用次数（比闭包更清晰的方式）"""
    def __init__(self, func: Callable):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.count += 1
        print(f"  [{self.func.__name__}] 第 {self.count} 次调用")
        return self.func(*args, **kwargs)

@CountCalls
def compute() -> int:
    return 42

print(f"\n=== 6. 类装饰器 ===")
compute()  # 第 1 次
compute()  # 第 2 次
# 类装饰器的优势：状态管理更自然，可以用方法和属性

# ============================================================
# 7. 保留函数签名的装饰器（functools.wraps 也做不到的）
# ============================================================

# @wraps 复制 __name__/__doc__，但不复制参数签名
# 需要 typing.ParamSpec（Python 3.10+）来保留完整签名
from typing import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """这个装饰器保留了原始函数的完整类型签名"""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        all_args = ", ".join(args_repr + kwargs_repr)
        print(f"  调用 {func.__name__}({all_args})")
        return func(*args, **kwargs)
    return wrapper

@log_call
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

print(f"\n=== 7. ParamSpec 保留签名 ===")
print(greet("Dean", greeting="Hi"))
# 类型检查器知道 greet 接收 (name: str, greeting: str = "Hello") → str

# ============================================================
# 8. 装饰器实战模式汇总
# ============================================================

# 8a. 缓存（简化版 lru_cache）
def memoize(func: F) -> F:
    cache: dict = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        else:
            print(f"    缓存命中: {args}")
        return cache[args]
    return wrapper

@memoize
def fib(n: int) -> int:
    """斐波那契——不带缓存 O(2^n)，带缓存 O(n)"""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(f"\n=== 8. 实战模式 ===")
print(f"fib(10) = {fib(10)}")

# 8b. 注册表模式
handlers: dict[str, Callable] = {}

def register(name: str):
    """将函数注册到全局 handlers 表"""
    def decorator(func: Callable) -> Callable:
        handlers[name] = func
        return func  # 原样返回，不做修改
    return decorator

@register("add")
def handle_add(data: dict) -> str:
    return f"处理添加: {data}"

@register("delete")
def handle_delete(data: dict) -> str:
    return f"处理删除: {data}"

print(f"\n已注册的处理器: {list(handlers.keys())}")
print(handlers["add"]({"id": 1}))

# 8c. 前置/后置钩子
def with_hooks(before: Callable | None = None, after: Callable | None = None):
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if before:
                before()
            result = func(*args, **kwargs)
            if after:
                after()
            return result
        return wrapper
    return decorator

@with_hooks(
    before=lambda: print("  [前置] 开始处理..."),
    after=lambda: print("  [后置] 处理完成!")
)
def process_data(data: str) -> str:
    print(f"    处理: {data}")
    return data.upper()

print(f"\n{process_data('hello')}")

# ============================================================
# 9. 装饰器 vs 上下文管理器：何时用哪个？
# ============================================================

# 装饰器："每次调用都要做这件事"（横切关注点）
# 上下文管理器："这一段代码需要这个环境"（资源管理）

# 计时：装饰器更自然
@timer
def work() -> None:
    time.sleep(0.1)

# 文件操作：上下文管理器更自然
# with open("file.txt") as f:
#     data = f.read()

print(f"\n=== 9. 装饰器 vs 上下文管理器 ===")
work()
print("装饰器适合'横切关注点'，上下文管理器适合'资源生命周期'")
