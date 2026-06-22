---
title: 并发编程全景：API 与选择
order: 6.5
---

# 并发编程全景：API 与选择

## 线程 进程和协程类比

1. 进程：
想象成工厂里的独立车间。每个车间（进程）都有自己独立的围墙、独立的工具箱（内存空间）和专属的物料。车间之间是物理隔离的，A车间着火了一般不会直接烧到B车间。
2. 线程：
想象成车间里的工人。一个车间里至少得有一个工人，也可以有多个工人（多线程）。这些工人共享车间里的所有工具和物料（共享进程的内存），所以工人之间沟通非常方便，喊一嗓子就行。
3. 协程：
想象成工人手里正在处理的一个个具体任务（比如拧螺丝、贴标签）。一个工人（线程）同一时刻只能干一件事，但他可以非常聪明：在等胶水干（I/O等待）的这几秒钟里，他先不傻站着，而是立刻切换去处理下一个任务。这种在工人内部进行的、极其轻量级的任务切换，就是协程。

**层级关系**：一个操作系统（工厂）包含多个进程（车间），一个进程包含多个线程（工人），一个线程可以包含多个协程（任务）。

| 维度 | 进程 | 线程 | 协程 |
| :--- | :--- | :--- | :--- |
| 资源分配 | 资源分配的基本单位。拥有独立的内存空间（堆、栈、全局变量等）。 | CPU调度的基本单位。共享所属进程的内存和资源。 | 用户态的轻量级线程。共享线程的资源，几乎没有独立内存开销。 |
| 调度主体 | 操作系统内核。由内核决定哪个进程获得CPU。 | 操作系统内核。内核决定哪个线程上CPU。 | 用户程序（程序员/框架）。由代码逻辑决定何时切换（如遇到`await`）。 |
| 切换成本 | 极高。需要保存整个车间的状态，刷新内存页表，开销巨大。 | 中等。需要保存寄存器状态，但不需要动内存页表。 | 极低。只是函数级别的挂起和恢复，几乎无内核开销。 |
| 通信机制 | 复杂。需要IPC（管道、消息队列、共享内存等），因为有围墙隔离。 | 简单。直接读写共享的全局变量即可（但要注意加锁）。 | 最简单。本质是同一个线程内的变量传递，无需加锁。 |
| 隔离性 | 强。一个进程崩了，通常不影响其他进程。 | 弱。一个线程崩了（如非法内存访问），整个进程都会挂掉。 | 无。一个协程崩了，通常会导致所在的线程（工人）崩溃。 |

## 一句话本质

| 模型 | 一句话 | 在 Python 中 |
|------|--------|-------------|
| **进程（Process）** | 操作系统创建独立地址空间，各自运行 | 绕过 GIL，CPU 密集型首选 |
| **线程（Thread）** | 同一进程内共享内存的轻量执行流 | 受 GIL 限制，I/O 密集型适用 |
| **协程（Coroutine）** | 用户态协作式调度，"函数暂停再恢复" | 单线程高并发 I/O，纳秒级切换 |

---

## 进程：绕过 GIL 做并行计算

### API 一览

| 类/函数 | 用途 | 推荐度 |
|---------|------|--------|
| `multiprocessing.Process` | 创建单个子进程 | ⭐⭐ 低级，通常不直接用 |
| `multiprocessing.Pool` | 进程池，`map`/`apply`/`apply_async` | ⭐⭐⭐ 经典但 `concurrent.futures` 更好 |
| `multiprocessing.Queue` | 进程间安全队列 | ⭐⭐⭐ 生产者-消费者模式 |
| `multiprocessing.Pipe` | 双工管道（两个端点） | ⭐⭐ 简单场景 |
| `multiprocessing.Value` / `Array` | 共享内存（需要 Lock） | ⭐⭐ 低级别，容易出错 |
| `multiprocessing.Manager` | 代理进程管理的共享对象 | ⭐⭐ 灵活性高但慢 |
| `concurrent.futures.ProcessPoolExecutor` | **推荐** 进程池统一接口 | ⭐⭐⭐⭐⭐ |
| `multiprocessing.shared_memory` (3.8+) | 真正的共享内存块 | ⭐⭐ 高性能场景 |

### 经典案例
> Windows 上用多进程（ProcessPoolExecutor）：所有执行代码必须放在 if name == 'main': 里面！
```python-run
import time, math
from concurrent.futures import ProcessPoolExecutor

def cpu_bound(n: int) -> float:
    # 🔥 加重任务！让它真正耗 CPU！
    result = 0
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            result += 1
    # 额外加大量计算
    for _ in range(10_000_000):
        math.sqrt(12345.6789)
    return result

if __name__ == '__main__':
    numbers = [10_000_000 + i for i in range(20)]

    # 单进程
    start = time.perf_counter()
    results = [cpu_bound(n) for n in numbers]
    print(f"单进程: {time.perf_counter() - start:.3f}s")

    # 多进程
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(cpu_bound, numbers))
    print(f"多进程: {time.perf_counter() - start:.3f}s")
```

```python-run
# 案例 2: 进程间通信 — Queue 生产者-消费者
# 注意：Windows 上 target 必须是模块级函数（spawn 需要 pickle），Linux/Mac 无此限制

from multiprocessing import Process, Queue

def producer(q: Queue) -> None:
    for i in range(100):
        q.put(f"任务-{i}")
        print(f"生产: 任务-{i}")
    q.put(None)  # 哨兵：通知消费者结束

def consumer(q: Queue, name: str) -> None:
    while True:
        item = q.get()
        if item is None:  # 收到哨兵
            q.put(None)   # 传给下一个消费者
            break
        print(f"[{name}] 处理: {item}")

# Windows 运行多进程必须加这一行！
if __name__ == '__main__':
    q: Queue = Queue()
    p = Process(target=producer, args=(q,))
    # # A 和 B 就是两个抢任务的工人，谁快谁执行，完全随机、操作系统说了算！
    c1 = Process(target=consumer, args=(q, "A"))
    c2 = Process(target=consumer, args=(q, "B"))

    p.start(); c1.start(); c2.start()
    p.join(); c1.join(); c2.join()
```

```python-run
# 案例 3: 并行下载 —— 多线程 vs 协程 终极对比
# 结论：I/O 密集型场景下，协程效率 ＞＞ 线程（更轻、更快、无系统切换开销）

from concurrent.futures import ThreadPoolExecutor
import asyncio
import time

# ====================== 【多线程版本】======================
def download_thread(url: str) -> str:
    time.sleep(0.2)  # 模拟同步 I/O 等待（会自动释放 GIL）
    return f"{url} → OK (200)"

def run_thread():
    urls = [f"https://api.example.com/data/{i}" for i in range(30)]
    start = time.perf_counter()

    # 线程池：默认 max_workers = min(32, os.cpu_count() + 4)
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(download_thread, urls))

    print(f"【多线程】下载 {len(urls)} 个: {time.perf_counter() - start:.3f}s")
    # 优点：不用改代码，直接并发；缺点：线程切换有开销，占用资源更多

# ====================== 【协程版本】======================
async def download_async(url: str) -> str:
    # 协程必须使用 asyncio.sleep（非阻塞），不能用 time.sleep（会阻塞整个事件循环）
    await asyncio.sleep(0.2)
    return f"{url} → OK (200)"

async def run_async():
    urls = [f"https://api.example.com/data/{i}" for i in range(30)]
    start = time.perf_counter()

    # 创建 30 个协程任务，全部并发执行（单线程内切换，无内核开销）
    tasks = [download_async(url) for url in urls]
    results = await asyncio.gather(*tasks)  # 等待所有任务完成

    print(f"【协程】下载 {len(urls)} 个: {time.perf_counter() - start:.3f}s")
    # 优点：用户态切换，极轻量，无 GIL 争抢，高并发下优势巨大
    # 缺点：必须全程 async/await 异步写法，同步函数不能直接用

# ====================== 主程序运行 ======================
if __name__ == '__main__':
    # 运行多线程
    run_thread()

    # 运行协程
    asyncio.run(run_async())

    # 最终结论：I/O 密集型（网络/文件/DB）
    # 协程 ＞＞ 线程：更快、更省资源、支持更高并发
```

### 推荐 API（按优先级）

1. **`ProcessPoolExecutor.map()`** — 并行处理大量同质任务
2. **`ProcessPoolExecutor.submit()` + `as_completed()`** — 需要处理每个结果时
3. **`multiprocessing.Queue`** — 生产者-消费者、流水线模式
4. 只在高性能场景才用 `Value/Array` 或 `shared_memory`

> 🚫 **不要直接用 `Process()` 除非你真的需要精细控制**。`Pool` / `Executor` 帮你管理生命周期、限制并发数。

---

## 线程：共享内存搞 I/O 并发

### API 一览

| 类/函数 | 用途 | 推荐度 |
|---------|------|--------|
| `threading.Thread` | 创建线程 | ⭐⭐ 建议用 ThreadPoolExecutor |
| `threading.Lock` | 互斥锁 | ⭐⭐⭐⭐ 竞态条件必用 |
| `threading.RLock` | 可重入锁（同一线程可多次 acquire） | ⭐⭐⭐ |
| `threading.Semaphore` | 限制并发数量 | ⭐⭐⭐ 限流 |
| `threading.Event` | 线程间信号（等待事件发生） | ⭐⭐⭐⭐ |
| `threading.Condition` | 条件变量（等待某条件成立） | ⭐⭐⭐ |
| `threading.Timer` | 延迟执行（N 秒后运行） | ⭐⭐ |
| `threading.Barrier` | 所有线程到达后才继续 | ⭐⭐ |
| `threading.local()` | 线程局部存储 | ⭐⭐⭐⭐ Web 框架必备 |
| `queue.Queue` | 线程安全队列 | ⭐⭐⭐⭐⭐ |
| `concurrent.futures.ThreadPoolExecutor` | **推荐** 线程池统一接口 | ⭐⭐⭐⭐⭐ |

### 经典案例

```python-run
# 案例 1: Event 协调 — 等所有线程就绪再同时开始
import threading, time

def racer(name: str, ready: threading.Event, go: threading.Event):
    print(f"[{name}] 准备完成")
    ready.set()          # 告诉主线程：我准备好了
    go.wait()            # 等发令枪
    print(f"[{name}] GO!")

ready_events = [threading.Event() for _ in range(3)]
go_event = threading.Event()

racers = [
    threading.Thread(target=racer, args=(f"选手{i}", ready_events[i], go_event))
    for i in range(3)
]
for t in racers: t.start()

# 等所有人准备好
for e in ready_events: e.wait()
print("=== 所有人就绪，出发！ ===")
time.sleep(0.5)
go_event.set()  # 发令枪！

for t in racers: t.join()
```

```python-run
# 案例 2: Semaphore 限流 — 最多同时 2 个线程访问数据库
import threading, time, random

db_semaphore = threading.Semaphore(2)  # 最多 2 个并发

def query_db(query_id: int) -> None:
    with db_semaphore:  # 获取许可
        print(f"[查询 {query_id}] 正在执行...")
        time.sleep(random.uniform(0.2, 0.5))
        print(f"[查询 {query_id}] 完成 [OK]")

threads = [threading.Thread(target=query_db, args=(i,)) for i in range(6)]
for t in threads: t.start()
for t in threads: t.join()
# 你会看到最多两个"正在执行"同时出现
```

```python-run
# 案例 3: threading.local() — 每个线程的"私有全局变量"
import threading

# 类比：Flask 的 request 对象 —— 每个请求线程有自己的 request
thread_data = threading.local()

def handle_request(user: str) -> None:
    thread_data.user = user        # 只有当前线程能看到
    thread_data.request_id = id(threading.current_thread())
    print(f"  处理 {user} 的请求 (线程 {thread_data.request_id})")

threads = [threading.Thread(target=handle_request, args=(f"user-{i}",))
           for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
# 每个线程看到的是自己的 user，互不影响
```

### 推荐 API（按优先级）

1. **`ThreadPoolExecutor.map()`** — I/O 密集型批量任务
2. **`queue.Queue`** — 生产者-消费者、工作队列
3. **`threading.Event`** — 线程间一次性信号通知
4. **`threading.Lock`** — 保护共享可变状态（最小化临界区）
5. **`threading.local()`** — 替代全局变量，线程安全的方式

> 🚫 **别用裸 `Thread()` 管复杂并发。** 线程生命周期管理、异常处理、结果收集——`Executor` 都帮你做好了。

---

## 协程：单线程高并发 I/O

### API 一览

| 类/函数 | 用途 | 版本 | 推荐度 |
|---------|------|------|--------|
| `asyncio.create_task()` | 把协程提交给事件循环（并发） | 3.7 | ⭐⭐⭐⭐⭐ |
| `asyncio.gather()` | 并发执行多个协程，收集结果 | 3.7 | ⭐⭐⭐ |
| `asyncio.TaskGroup()` | **结构化并发**，自动取消兄弟任务 | 3.11+ | ⭐⭐⭐⭐⭐ |
| `asyncio.wait_for()` | 设置超时的 await | 3.7 | ⭐⭐⭐⭐ |
| `asyncio.as_completed()` | 哪个先完成先处理哪个 | 3.7 | ⭐⭐⭐ |
| `asyncio.to_thread()` | **把同步阻塞函数扔到线程池** | 3.11+ | ⭐⭐⭐⭐⭐ |
| `asyncio.timeout()` | **上下文管理器式超时** | 3.13+ | ⭐⭐⭐⭐⭐ |
| `asyncio.Queue` | 协程间安全队列 | 3.7 | ⭐⭐⭐⭐ |
| `asyncio.Semaphore` | 协程限流 | 3.7 | ⭐⭐⭐⭐ |
| `asyncio.Event` | 协程间信号 | 3.7 | ⭐⭐⭐ |
| `asyncio.Lock` | 协程互斥（保护临界区） | 3.7 | ⭐⭐⭐ |
| `asyncio.Barrier` | 所有协程到达后继续 | 3.11+ | ⭐⭐ |
| `asyncio.TaskGroup` | 结构化并发生命周期 | 3.11+ | ⭐⭐⭐⭐⭐ |
| `asyncio.eager_task_factory` | 任务创建时立即执行第一步 | 3.12+ | ⭐⭐ |

### 经典案例

```python-run
# 案例 1: TaskGroup 并发请求（替代 gather，推荐）
import asyncio

async def api_call(name: str, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"service": name, "status": 200}

async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(api_call("auth", 0.2))
        t2 = tg.create_task(api_call("db", 0.3))
        t3 = tg.create_task(api_call("cache", 0.1))
    # 出了 async with，所有 task 都已完成
    print(f"结果: {t1.result()}, {t2.result()}, {t3.result()}")

asyncio.run(main())
```

```python-run
# 案例 2: Semaphore 限流 — 最多同时 3 个并发请求
import asyncio

async def fetch_with_limit(sem: asyncio.Semaphore, url: str) -> str:
    async with sem:  # 获取许可
        print(f"  请求 {url}...")
        await asyncio.sleep(0.2)  # 模拟 I/O
        print(f"  {url} 完成 [OK]")
        return f"OK({url})"

async def rate_limited_fetch() -> None:
    sem = asyncio.Semaphore(3)  # 最多 3 个并发
    tasks = [asyncio.create_task(fetch_with_limit(sem, f"/api/data/{i}"))
             for i in range(10)]
    await asyncio.gather(*tasks)

asyncio.run(rate_limited_fetch())
# 你会看到最多 3 个"请求..."同时出现
```

```python-run
# 案例 3: 生产者-消费者 (asyncio.Queue)
import asyncio

async def producer(q: asyncio.Queue) -> None:
    for i in range(5):
        await asyncio.sleep(0.1)
        await q.put(f"数据-{i}")
        print(f"生产: 数据-{i}")
    await q.put(None)  # 哨兵

async def consumer(q: asyncio.Queue, name: str) -> None:
    while True:
        item = await q.get()
        if item is None:
            await q.put(None)  # 传给下一个消费者
            break
        print(f"[{name}] 处理: {item}")
        q.task_done()

async def pipeline() -> None:
    q: asyncio.Queue = asyncio.Queue(maxsize=3)  # 背压
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q))
        tg.create_task(consumer(q, "A"))
        tg.create_task(consumer(q, "B"))

asyncio.run(pipeline())
```

```python-run
# 案例 4: to_thread — 把同步阻塞代码变成 async（3.11+）
import asyncio, time

def sync_db_query(query: str) -> str:
    """模拟一个不能改写的同步数据库查询"""
    time.sleep(0.3)  # 阻塞！
    return f"结果: [{query}]"

async def handle_requests() -> None:
    # 坏写法：直接调用会让整个事件循环卡 0.3s
    # result = sync_db_query("SELECT ...")

    # 好写法：扔到线程池，不阻塞事件循环
    r1 = await asyncio.to_thread(sync_db_query, "SELECT * FROM users")
    r2 = await asyncio.to_thread(sync_db_query, "SELECT * FROM orders")
    print(r1, r2, sep="\n")

asyncio.run(handle_requests())
```

### 推荐 API（按优先级，3.11+ 视角）

1. **`asyncio.TaskGroup()`** — 替代 `gather()`，结构化并发（3.11+）
2. **`asyncio.create_task()` + `await`** — 基本并发单元
3. **`asyncio.to_thread()`** — 同步阻塞代码的桥梁（3.11+）
4. **`asyncio.Semaphore`** — 速率限制
5. **`asyncio.Queue`** — 生产者-消费者流水线
6. **`asyncio.timeout()`** — 上下文管理器超时（3.13+）

---

## 进程 vs 线程 vs 协程：API 对照表

同一个任务，三种写法：

```python-run
# ═══════ 同一个任务：并发下载多个 URL ═══════
import time, random, threading

URLS = [f"https://api.example.com/item/{i}" for i in range(6)]

# μ 模拟阻塞 I/O
def blocking_download(url: str) -> str:
    time.sleep(0.2)
    return f"OK({url})"

async def async_download(url: str) -> str:
    await asyncio.sleep(0.2)
    return f"OK({url})"

# ─── 方式 1: 多线程 ───
def demo_threads() -> None:
    from concurrent.futures import ThreadPoolExecutor
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(blocking_download, URLS))
    print(f"多线程: {time.perf_counter() - start:.3f}s")

# ─── 方式 2: 多进程（不推荐用于 I/O） ───
def demo_processes() -> None:
    from concurrent.futures import ProcessPoolExecutor
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(blocking_download, URLS))
    print(f"多进程: {time.perf_counter() - start:.3f}s  (慢，序列化开销)")

# ─── 方式 3: 协程（推荐） ───
async def demo_async() -> None:
    start = time.perf_counter()
    tasks = [asyncio.create_task(async_download(url)) for url in URLS]
    results = await asyncio.gather(*tasks)
    print(f"协程:   {time.perf_counter() - start:.3f}s  (最快)")

demo_threads()
demo_processes()
asyncio.run(demo_async())
```

---

## 选择指南：决策树

```
你面临什么任务？
│
├─ CPU 密集型（计算、图像处理、加密）
│   └─ 用 multiprocessing / ProcessPoolExecutor
│      因为 GIL 让多线程对 CPU 任务无效（甚至更慢）
│
├─ I/O 密集型（网络请求、文件读写、数据库查询）
│   │
│   ├─ 已有同步代码，不想大改
│   │   └─ 用 ThreadPoolExecutor
│   │      线程在 I/O 等待时自动释放 GIL
│   │
│   ├─ 新项目或可以用 async/await
│   │   └─ 用 asyncio
│   │      更少内存、更高并发、不需要锁
│   │
│   └─ 既有同步代码，也想用 asyncio
│       └─ asyncio.to_thread() 包裹同步函数（3.11+）
│
├─ 混合型（有 CPU 也有 I/O）
│   └─ asyncio + ProcessPoolExecutor 混合
│      CPU 部分走进程池，I/O 部分走协程
│
└─ 需要进程隔离（子任务崩溃不影响主程序）
    └─ 用 multiprocessing
```

### 场景对照表

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| Web 服务器（数千并发连接） | `asyncio` | 单线程万级并发，内存省 |
| 批量图片处理 | `ProcessPoolExecutor` | CPU 密集，绕过 GIL |
| 爬虫（大量网络 I/O） | `asyncio` + `aiohttp` | 协程是天然的网络并发模型 |
| 已有 Django/Flask 同步代码 | `ThreadPoolExecutor` | 最小改动获得并发 |
| 实时数据处理流水线 | `asyncio.Queue` | 协程间消息传递零开销 |
| 多个独立后台任务 | `multiprocessing.Process` | 进程隔离，崩溃不互相影响 |
| 数据库批量写入 | `ThreadPoolExecutor` | 线程 I/O 释放 GIL，连接池友好 |
| 科学计算、数值模拟 | `ProcessPoolExecutor` | GIL 下唯一真正的并行 |
| 延时任务/定时器 | `asyncio.create_task` + `asyncio.sleep` | 协程定时器比线程定时器轻量 |
| 混合：计算 + 网络 | `asyncio` + `run_in_executor` | 计算扔进程池，网络走协程 |

---

## 三条铁律

1. **CPU 密集走进程，I/O 密集走协程，同步老代码走线程**。记住这句话就够了。

2. **别设太多 worker。** 线程/进程数不是越多越好——线程切换有开销，进程间通信有序列化成本。起手用 `os.cpu_count()` 或 `min(32, os.cpu_count() + 4)`（Python 3.8+ `ThreadPoolExecutor` 默认）。

3. **协程里面别调用 `time.sleep()`**——那会把整个事件循环卡死。用 `await asyncio.sleep()`。不确定某个函数会不会阻塞？用 `await asyncio.to_thread(func, args)`。

---

## 混合使用：asyncio + 线程/进程

```python-run
import asyncio, time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def slow_sync_io(n: int) -> int:
    """模拟同步阻塞 I/O 或 CPU 计算"""
    time.sleep(0.2)
    return n * n

def heavy_cpu(n: int) -> int:
    """CPU 密集型：GIL 让你无法用线程并行"""
    total = 0
    for i in range(n * 1_000_000):
        total += i
    return total

async def mixed_workflow() -> None:
    loop = asyncio.get_running_loop()

    # 同步 I/O → 扔到线程池（asyncio.to_thread 是便捷封装）
    results_io = await asyncio.gather(
        asyncio.to_thread(slow_sync_io, 1),
        asyncio.to_thread(slow_sync_io, 2),
        asyncio.to_thread(slow_sync_io, 3),
    )
    print(f"I/O 结果: {results_io}")

    # CPU 密集 → 扔到进程池（必须用 run_in_executor，to_thread 走的是线程池）
    with ProcessPoolExecutor(max_workers=2) as pool:
        loop = asyncio.get_running_loop()
        results_cpu = await asyncio.gather(
            loop.run_in_executor(pool, heavy_cpu, 5),
            loop.run_in_executor(pool, heavy_cpu, 6),
        )
    print(f"CPU 结果: {results_cpu}")

asyncio.run(mixed_workflow())
```

---

## 总结：三类 API 优先级速查

```
# 进程
① ProcessPoolExecutor.map()          ← 首选
② ProcessPoolExecutor.submit()       ← 需要逐结果处理
③ multiprocessing.Queue              ← 生产者-消费者

# 线程
① ThreadPoolExecutor.map()           ← 首选
② queue.Queue                        ← 生产者-消费者
③ threading.Event / Lock             ← 协调和互斥

# 协程
① asyncio.TaskGroup()                ← 结构化并发 (3.11+)
② asyncio.create_task()              ← 基本并发单元
③ asyncio.to_thread()                ← 同步桥接 (3.11+)
④ asyncio.Semaphore / Queue          ← 限流和流水线
⑤ asyncio.timeout()                  ← 超时管理 (3.13+)
```

> 📖 官方文档：[concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html), [threading](https://docs.python.org/3/library/threading.html), [multiprocessing](https://docs.python.org/3/library/multiprocessing.html), [asyncio](https://docs.python.org/3/library/asyncio.html), [PEP 654 – Exception Groups](https://peps.python.org/pep-0654/), [PEP 703 – Optional GIL](https://peps.python.org/pep-0703/)

---

## 本章小结

- **CPU 密集走进程**——只有 `multiprocessing` 能绕过 GIL 做真正的并行计算
- **I/O 密集走协程**——`asyncio` 单线程万级并发，`TaskGroup` 是结构化并发的新标准（3.11+）
- **同步老代码走线程**——`ThreadPoolExecutor` 改动最小，线程在 I/O 等待时自动释放 GIL
- **别同时在协程里 `time.sleep()`**——用 `await asyncio.sleep()` 或 `asyncio.to_thread()` 包裹阻塞代码
- **统一接口优先**——`concurrent.futures` 的 `Executor.map()` / `submit()` 是线程/进程的统一入口，`asyncio.TaskGroup` 是协程的统一入口

## 思考题

1. 一个任务需要下载 100 个网页、解析 HTML、把结果写入数据库。你会用哪种并发模型？为什么？
2. `threading.Semaphore(2)` 和 `asyncio.Semaphore(2)` 在效果上一样，在"不阻塞什么"上完全不同。解释这个区别。
3. 为什么 `multiprocessing.Queue` 比 `queue.Queue` 慢得多？从底层原理解释。
4. 下面代码有什么问题？`async def main(): time.sleep(5); return await fetch()`。给出两种修复方案。
5. 假设你要做一个 Web 框架的请求处理管道：鉴权 → 参数校验 → 查数据库 → 调第三方 API → 返回。哪些步骤可能阻塞事件循环？怎么处理？
