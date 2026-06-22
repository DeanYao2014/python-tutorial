# 0.4 条件判断与模式匹配 — 代码示例 (Python 3.12+)

# ============================================================
# if / elif / else — 经典分支
# ============================================================

score = 85
if score >= 90:
    grade = "优秀"
elif score >= 80:
    grade = "良好"
elif score >= 60:
    grade = "及格"
else:
    grade = "不及格"
print(f"{score} 分: {grade}")

# Python 独有的链式比较
x = 5
print(f"3 < x < 10: {3 < x < 10}")  # True
# 等价于 3 < x and x < 10

# ============================================================
# match case（Python 3.10+）—— 模式匹配
# ============================================================

# 1. 字面量匹配
def http_status(code):
    match code:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case 500:
            return "Server Error"
        case _:                     # _ 是通配符
            return "Unknown"

print(http_status(200))  # OK
print(http_status(418))  # Unknown

# 2. 序列解构匹配
def describe_seq(seq):
    match seq:
        case []:
            return "空序列"
        case [first]:
            return f"单元素: {first}"
        case [first, *rest]:
            return f"首元素: {first}, 剩余 {len(rest)} 个"

print(describe_seq([1]))
print(describe_seq([1, 2, 3]))

# 3. 守卫（Guard）—— 匹配 + 条件
def classify(n):
    match n:
        case 0:
            return "零"
        case n if n > 0:
            return "正数"
        case n if n < 0:
            return "负数"

print(classify(42))

# 4. 映射匹配
def handle_event(event):
    match event:
        case {"type": "click", "x": x, "y": y}:
            return f"点击位置: ({x}, {y})"
        case {"type": "keypress", "key": key}:
            return f"按下键: {key}"
        case _:
            return "未知事件"

print(handle_event({"type": "click", "x": 10, "y": 20}))
