# 0.6 dict 与 set — 代码示例 (Python 3.12+)

# ============================================================
# dict（字典）—— 键值对容器
# ============================================================

# 创建
person = {"name": "张三", "age": 25, "city": "北京"}
print(person["name"])          # 直接取值（key 不存在会 KeyError）
print(person.get("gender", "未知"))  # get 安全取值，支持默认值

# 增改删
person["job"] = "工程师"       # 新增键值对
person["age"] = 26             # 修改已有键
print(f"更新后: {person}")

popped = person.pop("city")    # 删除并返回
print(f"删除 city={popped}, 剩余: {person}")

# 遍历 dict
for k, v in person.items():
    print(f"{k}: {v}")

# ============================================================
# dict comprehension — 一行构建字典
# ============================================================

squares = {x: x**2 for x in range(6)}
print(f"平方表: {squares}")

# 翻转键值对
reversed_dict = {v: k for k, v in squares.items()}
print(f"翻转: {reversed_dict}")

# ============================================================
# setdefault 和 defaultdict — 处理缺失键
# ============================================================

word = "mississippi"
# 用 get 计数（不用先判断 key 是否存在）
counts = {}
for c in word:
    counts[c] = counts.get(c, 0) + 1
print(f"计数: {counts}")

# 更简单的方法：defaultdict
from collections import defaultdict
counts2: defaultdict[str, int] = defaultdict(int)
for c in word:
    counts2[c] += 1
print(f"defaultdict 版本: {dict(counts2)}")

# ============================================================
# set（集合）—— 无重复、无序的元素容器
# ============================================================

nums = [3, 1, 2, 3, 1, 4, 2]
unique = set(nums)
print(f"去重: {unique}")

# 集合运算
a, b = {1, 2, 3}, {2, 3, 4}
print(f"交集: {a & b}")   # 共同元素
print(f"并集: {a | b}")   # 所有元素
print(f"差集: {a - b}")   # 在 a 不在 b
print(f"对称差: {a ^ b}") # 只在一边的

# 成员检查 — O(1) 时间复杂度
print(f"'z' 在 set 中？{ 'z' in {1, 2, 3} }")

# set comprehension
even_set = {x for x in range(10) if x % 2 == 0}
print(f"偶数集合: {even_set}")
