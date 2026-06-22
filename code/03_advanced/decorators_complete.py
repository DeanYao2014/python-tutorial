"""
Chapter 3.2: 装饰器完全指南 — 代码示例
覆盖底层原理、高级模式、标准库、常见陷阱
"""

# ============================================================
# Part A: 装饰器底层
# ============================================================

# --- A1. 反糖: @ 语法到底做了什么 ---

def my_decorator(func):
    print(f"[定义时] 装饰器 {my_decorator.__name__} 收到 {func.__name__}")
    return func

# 写法一: @ 语法
@my_decorator
def hello():
    pass

# 写法二: 等价的手动写法 (名字不会进入命名空间, 仅演示)
def hello_manual():
    pass
hello_manual = my_decorator(hello_manual)

print("函数定义完成——装饰器已在定义时执行完毕\n")


# --- A2. 用 dis 看字节码 ---

import dis

def bare_decorator(f):
    return f

@bare_decorator
def sample(): pass

print("=== sample 函数自身的字节码 ===")
dis.dis(sample)

# 装饰器表达式在模块字节码中体现为:
# LOAD_NAME, LOAD_CONST, CALL_FUNCTION, STORE_NAME
print()

# --- A3. @wraps 的内部机制: update_wrapper 源码分析 ---

from functools import wraps, partial

# update_wrapper 的核心逻辑 (简化版):
# def update_wrapper(wrapper, wrapped):
#     wrapper.__name__ = wrapped.__name__
#     wrapper.__qualname__ = wrapped.__qualname__
#     wrapper.__doc__ = wrapped.__doc__
#     wrapper.__dict__.update(getattr(wrapped, '__dict__', {}))
#     wrapper.__wrapped__ = wrapped  # ← 链式引用
#     return wrapper
#
# @wraps 本身是这样的:
# def wraps(wrapped):
#     return partial(update_wrapper, wrapped=wrapped)

def show_chain(func):
    """展示 __wrapped__ 链"""
    current = func
    depth = 0
    while True:
        print(f"  第{depth}层: {current.__name__}")
        current = getattr(current, '__wrapped__', None)
        if current is None:
            break
        depth += 1

@wraps(hello)
def outer():
    pass

print("=== __wrapped__ 链式引用演示 ===")
print(f"outer.__name__ = {outer.__name__}")
print(f"outer.__wrapped__ is hello: {outer.__wrapped__ is hello}")
print()

# ============================================================
# Part B: 高级模式
# ============================================================

# --- B1. 可选参数装饰器: @log 或 @log(level="DEBUG") ---

import functools

def log(func=None, *, level="INFO"):
    """可选参数装饰器: 检测第一个参数是否为可调用对象"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            print(f"[{level}] 调用 {f.__name__}")
            return f(*args, **kwargs)
        return wrapper
    if func is None:
        # 调用形式: @log(level="DEBUG")
        return decorator
    else:
        # 调用形式: @log
        return decorator(func)

@log
def foo():
    return "foo"

@log(level="DEBUG")
def bar():
    return "bar"

print("=== 可选参数装饰器 ===")
foo()
bar()
print()


# --- B2. 带状态的装饰器: 计时统计 (min/max/avg) ---

import time

def timing_stats(func):
    """记录每次调用的耗时, 提供 min/max/avg 统计"""
    stats = []

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        result = func(*args, **kwargs)
        stats.append(time.perf_counter() - t)
        return result

    wrapper.stats = stats
    wrapper.report = lambda: (
        f"调用{len(stats)}次, min={min(stats):.6f}s, "
        f"max={max(stats):.6f}s, avg={sum(stats)/len(stats):.6f}s"
        if stats else "尚未调用"
    )
    return wrapper

@timing_stats
def slow_add(a, b):
    time.sleep(0.01)
    return a + b

slow_add(1, 2)
slow_add(3, 4)
print(f"=== 带状态的装饰器 ===\n{slow_add.report()}\n")


# --- B3. 修改参数的装饰器: 类型强制与默认注入 ---

def coerce_types(func):
    """根据类型注解自动强制类型转换"""
    import inspect
    hints = inspect.get_annotations(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        new_args = []
        for arg, (name, hint) in zip(args, list(hints.items())[:len(args)]):
            if hint is int and not isinstance(arg, int):
                arg = int(arg)
            elif hint is float and not isinstance(arg, float):
                arg = float(arg)
            new_args.append(arg)
        return func(*new_args, **kwargs)
    return wrapper

@coerce_types
def multiply(a: int, b: int) -> int:
    return a * b

print(f"=== 类型强制装饰器 ===\nmultiply('3', '4') = {multiply('3', '4')}\n")


def inject_defaults(**defaults):
    """为没有传入的关键字参数注入默认值"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, val in defaults.items():
                kwargs.setdefault(key, val)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@inject_defaults(timeout=30, retries=3)
def fetch(url, timeout=None, retries=None):
    return f"GET {url} timeout={timeout} retries={retries}"

print(f"=== 默认值注入装饰器 ===\n{fetch('/api/data')}\n")


# --- B4. 修改类的类装饰器: 自动 __repr__ ---

def auto_repr(cls):
    """为类添加自动生成的 __repr__"""
    def __repr__(self):
        fields = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({fields})"
    cls.__repr__ = __repr__
    return cls

@auto_repr
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

print(f"=== 修改类的类装饰器 ===\n{Point(1, 2)}\n")

# 带约束的类装饰器
def validate_fields(**validators):
    """强制 __init__ 后检查字段"""
    def decorator(cls):
        original_init = cls.__init__
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            for field, validator in validators.items():
                value = getattr(self, field, None)
                if not validator(value):
                    raise ValueError(f"{field}={value!r} 校验失败")
        cls.__init__ = new_init
        return cls
    return decorator

@validate_fields(age=lambda v: 0 <= v <= 150)
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

try:
    Person("Alice", 200)
except ValueError as e:
    print(f"=== 约束装饰器 ===\n{e}\n")


# --- B5. @singledispatch: 基于第一个参数类型的函数重载 ---

from functools import singledispatch

@singledispatch
def describe(obj):
    """根据第一个参数类型分发到不同实现"""
    return f"未知类型: {type(obj).__name__}"

@describe.register(int)
def _(obj):
    return f"整数: {obj}"

@describe.register(str)
def _(obj):
    return f"字符串 ({len(obj)}字符): {obj!r}"

@describe.register(list)
def _(obj):
    return f"列表 ({len(obj)}元素)"

print("=== singledispatch ===")
print(describe(42))
print(describe("hello"))
print(describe([1, 2, 3]))
print(describe(3.14))
print()

# singledispatchmethod: 用于类方法
from functools import singledispatchmethod

class Serializer:
    @singledispatchmethod
    def format(self, obj):
        return str(obj)

    @format.register(int)
    def _(self, obj):
        return hex(obj)

    @format.register(float)
    def _(self, obj):
        return f"{obj:.2f}"

s = Serializer()
print("=== singledispatchmethod ===")
print(s.format(255))
print(s.format(3.14159))
print(s.format("data"))
print()


# ============================================================
# Part C: 装饰器与元类
# ============================================================

# 场景: 对所有子类的方法自动计时
# 装饰器方案: 每个类手动加 @auto_timer

def auto_timer(cls):
    """类装饰器: 为类中所有自定义方法添加计时"""
    for name, method in list(cls.__dict__.items()):
        if callable(method) and not name.startswith('_'):
            @functools.wraps(method)
            def timed(self, *a, _m=method, _n=name, **kw):
                t = time.perf_counter()
                r = _m(self, *a, **kw)
                print(f"{_n}: {time.perf_counter()-t:.6f}s")
                return r
            setattr(cls, name, timed)
    return cls

@auto_timer
class Worker:
    def process(self):
        time.sleep(0.005)
        return "done"

w = Worker()
w.process()
print()

# 元类方案: 实例化时自动应用
class AutoTimerMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        return auto_timer(cls)  # 复用相同的逻辑

class Base(metaclass=AutoTimerMeta):
    pass

class AnotherWorker(Base):
    def process(self):
        time.sleep(0.005)
        return "done"

print("=== 装饰器 vs 元类对比 ===")
print(f"Worker是@auto_timer装饰的")
print(f"AnotherWorker是AutoTimerMeta元类自动装饰的\n")


# ============================================================
# Part D: 标准库中的装饰器
# ============================================================

# --- D1. lru_cache 工作原理和参数 ---

from functools import lru_cache

@lru_cache(maxsize=128, typed=False)
def fib(n):
    """lru_cache 内部维护一个有序字典, 记录 (args, kwargs) -> 返回值"""
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(f"=== lru_cache ===\nfib(30) = {fib(30)}")
print(f"缓存信息: {fib.cache_info()}")
print()

# --- D2. cached_property: 基于描述符的惰性计算 ---

from functools import cached_property

class DataSet:
    def __init__(self, data):
        self._data = data

    @cached_property
    def sorted_data(self):
        """首次访问时计算, 结果缓存在实例 __dict__ 中"""
        print("  > 正在排序...")
        return sorted(self._data)

ds = DataSet([3, 1, 2])
print("=== cached_property ===")
print(f"创建 DataSet, 尚未排序")
print(f"第一次: {ds.sorted_data}")
print(f"第二次: {ds.sorted_data}")  # 不打印 "正在排序..."
print()

# --- D3. total_ordering: 从 __eq__ + 一个比较方法自动生成其余 ---

from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)

v1 = Version(1, 0)
v2 = Version(2, 0)
print("=== total_ordering ===")
print(f"v1 < v2:  {v1 < v2}")
print(f"v1 > v2:  {v1 > v2}")
print(f"v1 <= v2: {v1 <= v2}")
print(f"v1 >= v2: {v1 >= v2}")
print(f"v1 != v2: {v1 != v2}")
print()

# --- D4. @dataclass: 终极类装饰器 ---

from dataclasses import dataclass, field, fields

@dataclass
class Product:
    name: str
    price: float = 0.0
    tags: list = field(default_factory=list)

# @dataclass 做了这些事:
# 1. 生成 __init__    2. 生成 __repr__
# 3. 生成 __eq__      4. (可选) __hash__, __lt__ 等

p = Product("Book", 29.9)
print(f"=== @dataclass ===\n{p}")
print(f"字段列表: {fields(Product)}")
print()


# ============================================================
# Part E: 常见陷阱
# ============================================================

# --- E1. 装饰器顺序影响最终行为 ---

def upper(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        return func(*a, **kw).upper()
    return wrapper

def exclaim(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        return func(*a, **kw) + "!!!"
    return wrapper

@upper
@exclaim
def greet_a():
    return "hello"

@exclaim
@upper
def greet_b():
    return "hello"

print("=== 装饰器顺序 ===")
print(f"@upper @exclaim: {greet_a()}")  # HELLO!!!
print(f"@exclaim @upper: {greet_b()}")  # HELLO!!!
print()


# --- E2. 方法装饰器丢失 self ---

def broken_log(func):
    """忘记 @wraps 且不用 classmethod 兼容"""
    def wrapper(self, *a, **kw):  # ← 如果没有 self, 崩
        print(f"调用 {func.__name__}")
        return func(self, *a, **kw)
    return wrapper  # ← 返回普通函数, 不是绑定方法

class Service:
    @broken_log
    def do_work(self):
        return "done"

try:
    Service().do_work()  # 这个能工作 (因为我们手动加了self)
except TypeError as e:
    print(f"错误: {e}")


# 正确做法: 使用类装饰器处理所有方法
def log_methods(cls):
    for name, method in list(cls.__dict__.items()):
        if callable(method) and not name.startswith('_'):
            @functools.wraps(method)
            def logged(self, *a, _m=method, _n=name, **kw):
                print(f"[LOG] {_n}")
                return _m(self, *a, **kw)
            setattr(cls, name, logged)
    return cls

@log_methods
class GoodService:
    def do_work(self):
        return "done"

    def do_other(self):
        return "also done"

gs = GoodService()
print(f"=== 方法装饰器正确写法 ===\ngs.do_work() -> {gs.do_work()}")
print(f"gs.do_other() -> {gs.do_other()}\n")

print("=" * 50)
print("全部示例运行完毕")
