"""2.7 泛型三剑客：TypeVar / ParamSpec / TypeVarTuple"""

from typing import TypeVar, ParamSpec, TypeVarTuple, reveal_type

# ── TypeVar：单一类型的泛化 ──
T = TypeVar('T')

def first(items: list[T]) -> T:
    return items[0]

n = first([1, 2, 3])         # n: int
s = first(['a', 'b', 'c'])   # s: str
# reveal_type(n)  # mypy: Revealed type is "int"

# ── TypeVar 边界约束 ──
from collections.abc import Sized

B = TypeVar('B', bound=Sized)  # B 必须实现了 __len__

def longest(a: B, b: B) -> B:
    return a if len(a) >= len(b) else b

longest([1, 2], [3, 4, 5])  # OK: list 实现了 __len__
# longest(1, 2)              # mypy 报错: int 没有 __len__

# ── ParamSpec（3.10+）：捕获函数签名 ──
P = ParamSpec('P')

from typing import Callable

def log_call(func: Callable[P, T]) -> Callable[P, T]:
    """装饰器：保留原函数的完整签名"""
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"调用 {func.__name__}({args}, {kwargs})")
        return func(*args, **kwargs)
    return wrapper

@log_call
def greet(name: str, *, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}"

print(greet("Python", greeting="Hi"))
# 调用 greet(('Python',), {'greeting': 'Hi'})
# Hi, Python

# ── TypeVarTuple（3.11+）：变长类型参数 ──
Ts = TypeVarTuple('Ts')

def make_tuple(*args: *Ts) -> tuple[*Ts]:
    return args

result = make_tuple(1, "hi", 3.14)
# result 类型: tuple[int, str, float]  ← 精确！
print(result)
