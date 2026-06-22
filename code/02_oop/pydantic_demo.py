"""2.7 Pydantic v2 用法示例

安装：pip install pydantic
"""

from pydantic import BaseModel, field_validator, model_validator, ValidationError
from typing import Self


class User(BaseModel):
    name: str
    age: int
    email: str

    # ── field_validator：单字段校验 ──
    @field_validator('age')
    @classmethod
    def age_must_be_reasonable(cls, v: int) -> int:
        if v < 0:
            raise ValueError('年龄不能为负数')
        if v > 150:
            raise ValueError('年龄不太可能超过 150')
        return v

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('名字不能为空')
        return v.strip()

    # ── model_validator：跨字段校验 ──
    @model_validator(mode='after')
    def check_email_format(self) -> Self:
        if '@' not in self.email:
            raise ValueError('邮箱格式无效')
        return self


# 正常创建
user = User(name="Alice", age=30, email="alice@example.com")
print(f"创建成功: {user.model_dump()}")
# 创建成功: {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}

# 校验失败——显示所有错误
try:
    User(name="", age=-5, email="bad_email")
except ValidationError as e:
    print(f"\n校验失败（共 {e.error_count()} 个错误）：")
    for err in e.errors():
        print(f"  字段 {err['loc']}: {err['msg']}")


# ── Settings 管理 ──
from pydantic_settings import BaseSettings  # pip install pydantic-settings


class AppSettings(BaseSettings):
    """从环境变量 / .env 文件读取配置"""
    database_url: str
    api_key: str
    max_connections: int = 10  # 有默认值

    class Config:
        env_file = '.env'  # 可选
        env_prefix = 'APP_' # APP_DATABASE_URL, APP_API_KEY ...
