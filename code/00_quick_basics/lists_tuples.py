# 0.3 list 与 tuple — 代码示例 (Python 3.12+)

# ============================================================
# list：可变序列
# ============================================================

fruits = ["苹果", "香蕉", "橘子"]
print(f"原始: {fruits}")
print(f"第一个: {fruits[0]}, 最后一个: {fruits[-1]}")

# 切片：seq[start:stop:step]
print(f"前两个: {fruits[:2]}")
print(f"倒序: {fruits[::-1]}")

# 增删改
fruits.append("葡萄")
fruits.insert(1, "西瓜")
print(f"新增后: {fruits}")
fruits.remove("香蕉")
print(f"删除后: {fruits}")

# ============================================================
# tuple：不可变序列
# ============================================================

point = (3, 4)
# point[0] = 5  # TypeError! 不可修改

# "不可变"是指容器结构，不是元素内容
t = ([1, 2], [3, 4])  # tuple 包含两个 list
t[0].append(99)       # OK — 改的是 list 元素，不是 tuple 结构
print(f"修改后: {t}")

# 单元素 tuple 需要逗号
single = (42,)         # 这是 tuple
not_tuple = (42)       # 这只是一个带括号的 int
print(f"single 类型: {type(single)}, not_tuple 类型: {type(not_tuple)}")

# ============================================================
# 解包（Unpacking）
# ============================================================

a, b, c = [1, 2, 3]
print(f"a={a}, b={b}, c={c}")

# 用 * 收集剩余元素
first, *rest = "python"
print(f"first={first}, rest={rest}")

# 用 * 解包作为函数参数
nums = [1, 2, 3]
print([*nums, 4, 5])  # [1, 2, 3, 4, 5]

# ============================================================
# zip —— 并行迭代
# ============================================================

names = ["张三", "李四", "王五"]
scores = [85, 92, 78]
for name, score in zip(names, scores):
    print(f"{name}: {score}")
