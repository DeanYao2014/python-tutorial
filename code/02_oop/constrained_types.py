"""2.7 约束型类型：Literal / Final / TypedDict / NotRequired"""

from typing import Literal, Final, TypedDict, NotRequired

# ── Literal：限定取值范围 ──
# 比 str 精确得多——IDE 会自动补全 "left" | "right" | "center"
def align_text(text: str, *, side: Literal["left", "right", "center"]) -> str:
    alignments = {"left": text, "center": f" {text} ", "right": f"  {text}"}
    return alignments[side]

print(align_text("标题", side="center"))
# align_text("标题", side="top")  # mypy 报错：不是合法值

# ── Final：阻止意外修改 ──
API_URL: Final = "https://api.example.com/v1"
# API_URL = "其他地址"  # mypy 报错：不能重新赋值 Final 变量

class Base:
    DEFAULT_TIMEOUT: Final[int] = 30

# class Sub(Base):
#     DEFAULT_TIMEOUT = 60  # mypy 报错：不能覆盖 Final 属性

# ── TypedDict：描述字典的"形状" ──
class User(TypedDict):
    name: str
    age: int
    email: NotRequired[str]  # 可选字段（3.11+ 推荐，替代 total=False）

def format_user(user: User) -> str:
    email = user.get("email", "未提供")
    return f"{user['name']}，{user['age']}岁，邮箱：{email}"

alice: User = {"name": "Alice", "age": 30}
print(format_user(alice))
# alice_bad: User = {"name": "Bob"}  # mypy 报错：缺少 age

# ── 与 @dataclass 对比：什么场景用哪个？ ──
# TypedDict：与 JSON/API 边界交互，已知结构的外部数据
# dataclass：内部业务对象，需要方法和可变状态
