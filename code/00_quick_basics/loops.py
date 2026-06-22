# 0.5 循环 — 代码示例 (Python 3.12+)

# ============================================================
# for 循环：遍历任何可迭代对象
# ============================================================

fruits = ["苹果", "香蕉", "橘子"]
for fruit in fruits:
    print(f"水果: {fruit}")

# range(start, stop, step)
for i in range(3):           # 0, 1, 2
    print(i, end=" ")
print()

for i in range(5, 0, -1):    # 5, 4, 3, 2, 1
    print(i, end=" ")
print()

# ============================================================
# enumerate —— 同时拿到索引和值
# ============================================================

for idx, fruit in enumerate(fruits):
    print(f"{idx}: {fruit}")

# 自定义起始序号
for idx, fruit in enumerate(fruits, start=1):
    print(f"第 {idx} 个: {fruit}")

# ============================================================
# zip —— 并行迭代多个序列
# ============================================================

names = ["张三", "李四", "王五"]
scores = [85, 92, 78]

for name, score in zip(names, scores):
    print(f"{name}: {score} 分")

# 长度不同时，zip 按最短的停止
short = [1, 2]
long = ["a", "b", "c", "d"]
print(f"zip 结果: {list(zip(short, long))}")

# 按最长的：用 zip_longest
from itertools import zip_longest
print(f"zip_longest: {list(zip_longest(short, long, fillvalue=None))}")

# ============================================================
# while 循环
# ============================================================

count = 3
while count > 0:
    print(f"倒计时: {count}")
    count -= 1
print("出发！")

# ============================================================
# 推导式初识（Comprehension）
# ============================================================

# list comprehension — 一行代替 for + append
squares = [x**2 for x in range(10)]
print(f"平方: {squares}")

# 带过滤
evens = [x for x in range(10) if x % 2 == 0]
print(f"偶数: {evens}")

# dict comprehension
word = "hello world"
char_count = {c: word.count(c) for c in set(word) if c != " "}
print(f"字符计数: {char_count}")
