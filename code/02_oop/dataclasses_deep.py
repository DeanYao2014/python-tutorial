"""2.6 数据类：@dataclass 深度解析"""

import sys
import json
import re
from dataclasses import dataclass, field, fields, asdict, astuple, KW_ONLY


# ══════════════════════════════════════════════════════════════════════
# 1. @dataclass 基础：消灭样板代码
# ══════════════════════════════════════════════════════════════════════

# ── 没有 dataclass ──
class PointManual:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"PointManual(x={self.x}, y={self.y})"

    def __eq__(self, other):
        if not isinstance(other, PointManual):
            return NotImplemented
        return self.x == other.x and self.y == other.y

# ── 有 dataclass ──
@dataclass
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0)
print("基础:", p1, "| eq:", p1 == p2)


# ══════════════════════════════════════════════════════════════════════
# 2. field() 定制
# ══════════════════════════════════════════════════════════════════════

@dataclass
class User:
    name: str
    email: str
    # default_factory：每个实例独立的可变默认值
    tags: list[str] = field(default_factory=list)
    # init=False：不在 __init__ 中出现
    _id: int = field(default=0, init=False, repr=False)
    # compare=False：不参与 __eq__
    login_count: int = field(default=0, compare=False)

u1 = User("Alice", "alice@a.com")
u2 = User("Alice", "alice@a.com", login_count=999)
print("\nfield() 定制:")
print(f"  u1: {u1}")
print(f"  u1 == u2: {u1 == u2}  ← login_count 不参与比较")
u1.tags.append("vip")
print(f"  u1.tags: {u1.tags}")
print(f"  u2.tags: {u2.tags}  ← 不受影响")


# ══════════════════════════════════════════════════════════════════════
# 3. __post_init__ 验证与派生
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Customer:
    name: str
    email: str
    age: int
    # 派生字段，不在 init 中
    is_adult: bool = field(init=False)
    created_from: str = field(default="", init=False, repr=False)

    def __post_init__(self):
        # 验证
        if self.age < 0:
            raise ValueError(f"年龄不能为负: {self.age}")
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError(f"邮箱格式无效: {self.email}")
        # 派生
        self.is_adult = self.age >= 18
        self.created_from = "manual"

print("\n__post_init__:")
try:
    Customer("Bad", "not-an-email", -5)
except ValueError as e:
    print(f"  校验失败: {e}")

c = Customer("Alice", "alice@example.com", 25)
print(f"  {c.name} adult={c.is_adult}")


# ══════════════════════════════════════════════════════════════════════
# 4. slots=True：内存优化（3.10+）
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Normal:
    x: float
    y: float
    name: str

@dataclass(slots=True)
class Slotted:
    x: float
    y: float
    name: str

n = Normal(1.0, 2.0, "hello")
s = Slotted(1.0, 2.0, "hello")

print("\nslots=True 内存对比:")
print(f"  Normal  size: {sys.getsizeof(n) + sys.getsizeof(n.__dict__)} 字节")
print(f"  Slotted size: {sys.getsizeof(s)} 字节")

# 动态属性限制
n.new_attr = "surprise"   # OK：有 __dict__
try:
    s.new_attr = "fail"   # AttributeError：没 __dict__
except AttributeError as e:
    print(f"  Slotted 不能加动态属性: {e}")


# ══════════════════════════════════════════════════════════════════════
# 5. kw_only 和 KW_ONLY（3.10+）
# ══════════════════════════════════════════════════════════════════════

@dataclass(kw_only=True)
class Book:
    title: str
    author: str
    pages: int = 0

b = Book(title="Python编程", author="Guido", pages=500)
# b = Book("Python编程", "Guido", 500)  # TypeError!
print("\nkw_only:")
print(f"  {b}")

@dataclass
class SearchQuery:
    keyword: str              # 位置参数
    _: KW_ONLY                # 此后全是 keyword-only
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"

q = SearchQuery("python教程", page=1, sort_by="date")
print(f"  SearchQuery: {q}")


# ══════════════════════════════════════════════════════════════════════
# 6. 对比：dataclass vs NamedTuple vs TypedDict
# ══════════════════════════════════════════════════════════════════════

from typing import NamedTuple, TypedDict

# NamedTuple：不可变、可解包
class PointNT(NamedTuple):
    x: float
    y: float

pnt = PointNT(1.0, 2.0)
x, y = pnt                     # 可解包
# pnt.x = 3.0                  # AttributeError：不可变

# TypedDict：只是类型提示
class PointTD(TypedDict):
    x: float
    y: float

td: PointTD = {"x": 1.0, "y": 2.0}  # 就是普通 dict

# dataclass：可变、可加方法
@dataclass
class PointDC:
    x: float
    y: float
    label: str = "point"

    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

print("\n三种方案对比:")
print(f"  NamedTuple  解包: {x}, {y}")
print(f"  TypedDict   type: {type(td).__name__}")
print(f"  dataclass   距离: {PointDC(3.0, 4.0).distance_from_origin()}")


# ══════════════════════════════════════════════════════════════════════
# 7. 工具函数：fields(), asdict(), astuple()
# ══════════════════════════════════════════════════════════════════════

@dataclass
class Person:
    name: str
    age: int
    email: str = field(default="", repr=False)
    _secret: str = field(default="hidden", repr=False)

print("\nfields() 遍历:")
for f in fields(Person):
    print(f"  {f.name}: type={f.type.__name__}, default={f.default!r}")

p = Person("Alice", 30, email="alice@example.com")
print(f"\nasdict():  {asdict(p)}")
print(f"astuple(): {astuple(p)}")

# 配合 json
print(f"\njson: {json.dumps(asdict(p), ensure_ascii=False)}")


# ══════════════════════════════════════════════════════════════════════
# 8. 实战：应用配置类
# ══════════════════════════════════════════════════════════════════════

@dataclass(kw_only=True)
class AppConfig:
    env: str
    app_name: str = "my-app"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = ""

    _started_at: float = field(default=0.0, init=False, repr=False)
    _is_secure: bool = field(init=False, repr=False)

    def __post_init__(self):
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"无效端口: {self.port}")
        if not self.database_url:
            env_db = {
                "dev": "sqlite:///dev.db",
                "staging": "postgresql://localhost:5432/staging",
                "production": "postgresql://prod-db:5432/main",
            }
            self.database_url = env_db.get(self.env, "sqlite:///dev.db")
        self._is_secure = "postgresql" in self.database_url

    def to_json(self) -> str:
        public = {k: v for k, v in asdict(self).items()
                  if not k.startswith('_')}
        return json.dumps(public, indent=2, ensure_ascii=False)

    @property
    def connection_info(self) -> str:
        return f"{self.host}:{self.port} ({self.env})"

print("\n实战——配置类:")
config = AppConfig(env="staging")
print(f"  连接: {config.connection_info}")
print(f"  JSON:\n{config.to_json()}")


# ══════════════════════════════════════════════════════════════════════
# 9. (可选) order=True：自动比较
# ══════════════════════════════════════════════════════════════════════

@dataclass(order=True)
class Score:
    value: int
    label: str = ""

scores = [Score(85, "B"), Score(95, "A"), Score(72, "C")]
print("\norder=True 排序:")
for s in sorted(scores):
    print(f"  {s}")
