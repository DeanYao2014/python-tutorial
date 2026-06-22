"""2.7 Protocol：鸭子类型的静态表达"""

from typing import Protocol

# ── 定义一个 Protocol：声明"会叫"的对象 ──
class Quackable(Protocol):
    def quack(self) -> str: ...

# ── 这两个类都不继承 Quackable，但 mypy 认为它们"是" Quackable ──
class Duck:
    def quack(self) -> str:
        return "嘎嘎"

class DuckPerson:
    def quack(self) -> str:
        return "我学鸭叫"
    def walk(self) -> None: ...

# ── 函数要求 Quackable，但接受任何有 quack() 的对象 ──
def make_quack(animal: Quackable) -> str:
    return animal.quack()

print(make_quack(Duck()))       # 嘎嘎
print(make_quack(DuckPerson())) # 我学鸭叫

# ── Protocol 支持泛型 ──
T_contra = __import__('typing').TypeVar('T_contra', contravariant=True)

class SupportsWrite(Protocol[T_contra]):
    def write(self, data: T_contra) -> None: ...

def save(data: str, writer: SupportsWrite[str]) -> None:
    writer.write(data)

import io
save("hello", io.StringIO())  # OK: StringIO.write(str) -> int 兼容

# ── 对比 ABC：需要显式继承或 register ──
from abc import ABC, abstractmethod

class QuackableABC(ABC):
    @abstractmethod
    def quack(self) -> str: ...

class DuckABC(QuackableABC):  # 必须显式继承
    def quack(self) -> str:
        return "嘎嘎"

# Duck 无法传给 make_quack_abc，因为它没有继承 QuackableABC
# Protocol 的优势就在这里：不需要修改已有类的继承关系
