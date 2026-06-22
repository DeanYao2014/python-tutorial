"""2.3 魔术方法全景 —— Vector2D 综合示例 + 各项独立演示

展示的魔术方法：
- __repr__ / __str__ (3.1 标识)
- __eq__ / __hash__ (3.2 相等与哈希)
- __bool__ / __len__ (3.3 真值)
- __add__ / __radd__ / __iadd__ (3.4 运算符)
- __contains__ (3.5)
- __enter__ / __exit__ (3.6 上下文)
- __getitem__ / __setitem__ (3.7 下标)
- __iter__ / __neg__ / __abs__ (贯穿综合示例)
"""

import math


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 综合示例：Vector2D —— 魔术方法全景
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Vector2D:
    """二维向量——整合多种魔术方法的实际场景"""
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x, self.y = float(x), float(y)

    # ── 3.1 标识：__repr__ 给开发者，__str__ 给用户 ──
    def __repr__(self) -> str:
        return f"Vector2D({self.x!r}, {self.y!r})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    # ── 3.2 相等与哈希 ──
    def __eq__(self, other) -> bool:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)

    def __hash__(self) -> int:
        # round 到 10 位消除浮点误差对哈希一致性的影响
        return hash((round(self.x, 10), round(self.y, 10)))

    # ── 3.3 真值：零向量 → False ──
    def __bool__(self) -> bool:
        return self.x != 0.0 or self.y != 0.0

    def __len__(self) -> int:
        return 2  # 始终有 2 个分量

    # ── 3.4 运算符重载 ──
    def __add__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        if isinstance(other, (int, float)):
            return Vector2D(self.x + other, self.y + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if isinstance(other, Vector2D):
            self.x += other.x
            self.y += other.y
        elif isinstance(other, (int, float)):
            self.x += other
            self.y += other
        else:
            return NotImplemented
        return self

    def __sub__(self, other):
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        return NotImplemented

    def __neg__(self):
        return Vector2D(-self.x, -self.y)

    def __abs__(self):
        return math.hypot(self.x, self.y)

    # ── 3.5 / 3.7 容器：包含、索引、迭代 ──
    def __contains__(self, item: float) -> bool:
        return item == self.x or item == self.y

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError(f"下标 {index} 超出范围，Vector2D 只支持 0 和 1")

    def __iter__(self):
        yield self.x
        yield self.y


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 独立演示：各魔术方法的常见陷阱与正确写法
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 3.1 repr vs str 的对比 ──
def demo_repr_vs_str():
    """展示 __repr__ 和 __str__ 在不同上下文中的调用选择"""
    v = Vector2D(3.0, 4.0)
    print("str(v):   ", str(v))
    print("repr(v):  ", repr(v))
    print("print(v): ", end=""); print(v)
    print("f-string: ", f"{v}")
    print("f!r:      ", f"{v!r}")  # !r 强制走 __repr__


# ── 3.2 eq/hash 契约 —— 只覆盖 __eq__ 的危险 ──
class PersonBroken:
    """只覆盖 __eq__，没有 __hash__ —— Python 会将 __hash__ 设为 None"""
    def __init__(self, name: str): self.name = name
    def __eq__(self, other) -> bool:
        return isinstance(other, PersonBroken) and self.name == other.name


class PersonFixed:
    """同时覆盖 __eq__ 和 __hash__，且用同一组字段"""
    def __init__(self, name: str, age: int): self.name, self.age = name, age

    def __eq__(self, other) -> bool:
        if not isinstance(other, PersonFixed):
            return NotImplemented
        return self.name == other.name and self.age == other.age

    def __hash__(self) -> int:
        return hash((self.name, self.age))


def demo_eq_hash():
    """展示 __eq__ / __hash__ 契约"""
    # PersonBroken：不能放入 set
    try:
        s = {PersonBroken("Alice")}
    except TypeError as e:
        print(f"PersonBroken 放入 set 失败: {e}")

    # PersonFixed：正确实现，可哈希
    p1 = PersonFixed("Alice", 30)
    p2 = PersonFixed("Alice", 30)
    p3 = PersonFixed("Bob", 25)
    print(f"p1 == p2: {p1 == p2}")            # True
    print(f"hash(p1) == hash(p2): {hash(p1) == hash(p2)}")  # True
    people = {p1, p3}
    print(f"set 中有 {len(people)} 个人")       # 2（p1 和 p2 视为同一）


# ── 3.3 真值测试优先顺序 ──
class WithBoolAndLen:
    def __bool__(self): return False
    def __len__(self): return 999

class WithLenOnly:
    def __len__(self): return 0

class WithoutBoth:
    pass


def demo_bool():
    """__bool__ 优先于 __len__，两者都没有则永远为 True"""
    print(f"WithBoolAndLen: {bool(WithBoolAndLen())}")  # False（__bool__ 说了算）
    print(f"WithLenOnly:    {bool(WithLenOnly())}")     # False（__len__ 返回 0）
    print(f"WithoutBoth:    {bool(WithoutBoth())}")      # True（没有任何覆盖）


# ── 3.4 反射运算符完整演示 ──
def demo_operator_chain():
    """展示 a + b 的完整查找链"""
    v = Vector2D(1, 2)

    # 正常情况：Vector2D + Vector2D
    print(f"v + Vector2D(3,4): {v + Vector2D(3, 4)}")  # (4.0, 6.0)

    # Vector2D + int：正向 __add__ 不认识 int → 返回 NotImplemented
    # Python 接着调 int.__radd__(v) → 不认识 → 调 Vector2D.__radd__(v)
    print(f"v + 5: {v + 5}")      # (6.0, 7.0)

    # int + Vector2D：int.__add__ 不认识 → 调 Vector2D.__radd__(5)
    print(f"5 + v: {5 + v}")      # (6.0, 7.0)


# ── 3.5 contains 的 O(1) 优势 ──
class SlowLookup:
    """没有 __contains__——in 退化为遍历"""
    def __init__(self, data): self.data = data
    def __iter__(self): return iter(self.data)

class FastLookup:
    """有 __contains__——O(1) 成员查找"""
    def __init__(self, data): self._set = set(data)
    def __contains__(self, item): return item in self._set


# ── 3.6 上下文管理器协议 ──
class ManagedFile:
    """展示 __enter__ / __exit__ 的完整生命周期"""
    def __init__(self, filename: str): self.filename = filename

    def __enter__(self):
        self.file = open(self.filename, 'w')
        print(f"[enter] 文件打开: {self.filename}")
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        print(f"[exit]  文件关闭: {self.filename}")
        # 返回 True 吞掉异常——实际代码应谨慎使用
        if exc_type is not None:
            print(f"[exit]  捕获异常: {exc_type.__name__}: {exc_val}")
        return False  # 不吞异常


# ── 3.7 下标访问 + 切片演示 ──
class SliceInspector:
    """展示 slice 对象传给 __getitem__ 的细节"""
    def __getitem__(self, index):
        if isinstance(index, slice):
            return (
                f"slice: start={index.start}, "
                f"stop={index.stop}, step={index.step}"
            )
        return f"index: {index}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主入口：运行所有演示
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    print("=" * 50)
    print("3.1 repr vs str")
    print("=" * 50)
    demo_repr_vs_str()

    print("\n" + "=" * 50)
    print("3.2 eq 与 hash 契约")
    print("=" * 50)
    demo_eq_hash()

    print("\n" + "=" * 50)
    print("3.3 bool vs len 真值测试")
    print("=" * 50)
    demo_bool()

    print("\n" + "=" * 50)
    print("3.4 运算符 + radd 完整链路")
    print("=" * 50)
    demo_operator_chain()

    print("\n" + "=" * 50)
    print("3.7 切片")
    print("=" * 50)
    si = SliceInspector()
    print(si[5])
    print(si[1:10:2])
