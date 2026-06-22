"""2.7 Self 类型（3.11+）：链式调用与继承的正确标注"""

from typing import Self, TypeVar

# ── 3.10 及以前：用 TypeVar 绕圈 ──
OldT = TypeVar('OldT', bound='OldShape')

class OldShape:
    def set_color(self: OldT, color: str) -> OldT:
        self.color = color
        return self

# ── 3.11+：直接用 Self ──
class Shape:
    color: str = "black"

    def set_color(self, color: str) -> Self:
        self.color = color
        return self

class Circle(Shape):
    radius: float = 1.0

    def set_radius(self, radius: float) -> Self:
        self.radius = radius
        return self

# 完美推断：Circle.set_color() 返回 Circle（不是 Shape！）
circle = Circle().set_color("red").set_radius(5.0)
print(f"color={circle.color}, radius={circle.radius}")
# color=red, radius=5.0
# mypy 知道 circle 是 Circle 类型，可以调用 set_radius

# ── 在类方法中 ──
class Database:
    name: str

    @classmethod
    def connect(cls, dsn: str) -> Self:
        db = cls()
        db.name = dsn
        return db

conn = Database.connect("postgresql://...")
# mypy 推断 conn 类型是 Database（不是 Shape 之类的）
