---
title: 数据结构与算法
order: 6
---

# 第六部分：数据结构与算法

**不是《算法导论》的 Python 翻译版。** 关注 Python 如何表达数据结构，标准库提供了哪些开箱即用的算法工具，以及经典算法背后的设计思想。

---

## 学习路线图：先读这里

本节内容按"**数据结构 → 算法策略**"分为上下两篇，但**章节编号 ≠ 推荐学习顺序**。它们之间存在一条清晰的依赖链——跳过前置章节直接学后面的内容，会事倍功半。

### 核心认知：数据结构是算法的"基础设施"

**算法**（排序、搜索、动态规划、图算法、递归分治）依赖**数据结构**来承载状态：

```
Array / Linked List ──→ Stack / Queue ──→ Hash Table
      │                    │                  │
      └──────→ Tree / Binary Tree ←──────────┘
                        │
                        ├──→ Heap (Complete Binary Tree + Array)
                        │
                        └──→ Graph (dict + set / list)
                             ↑
                   The most complex structure —
                   depends on Stack, Queue, Heap, and Hash simultaneously
```

**关键洞察**：图算法之所以"难"，不是图本身复杂——而是它**同时调用**了几乎所有基础数据结构。学图之前，必须先把工具磨利。

### 每个图算法背后站着一个数据结构

| 算法 | 依赖的数据结构 | 为什么 |
|------|:------------:|--------|
| BFS | **队列** (`deque`) | 逐层扩散 = FIFO，先来的先处理 |
| DFS | **栈** (`list` / 递归) | 一路到底 = LIFO，后来的先处理 |
| visited 集合 | **哈希表** (`set`) | O(1) 判断"这个节点来过没有" |
| Dijkstra | **堆** (`heapq`) | 每次取出"当前距离最短"的节点 |
| Prim / Kruskal | **堆** + **并查集** | 贪心选最小边 + 判环 |
| 拓扑排序 | **栈** / **队列** | 记录完成顺序或入度为零的节点 |
| Kosaraju | **栈** + 逆序 | 两次 DFS，后序记录完成时间 |
| A\* | **堆** | Dijkstra + 启发式估价函数 |

### 数据结构之间的依赖链

```
6.2 Array / Linked List
 │
 ├─→ 6.3 Stack / Queue      Stack = list (append/pop), Queue = deque (append/popleft)
 │     │                     BFS / DFS basic operations live here
 │
 ├─→ 6.4 Hash Table         Open addressing relies on Array
 │     │                     visited set, dict keys, Counter — all depend on it
 │
 └─→ 6.5 Tree / Binary Tree Linked List = degenerate Tree (single child per node)
       │
       ├─→ 6.6 Heap          Heap = Complete Binary Tree stored in Array
       │     Used by Dijkstra, Prim, Top-K
       │
       └─→ 6.7 Graph         Adjacency list = dict + set/list
              │
              └─→ 6.12 Graph Algorithms (Dijkstra / Prim / Kruskal / A*)
```

### 推荐学习路径（按依赖关系排序，不是按章节编号）

```
Step 1   6.1 Algorithm Basics & Complexity    Big O, O(n) vs O(n²)
              │
Step 2   6.2 Array & Linked List              Contiguous memory vs pointer chains
              │
Step 3   6.3 Stack & Queue                    LIFO vs FIFO — the "OS" of BFS/DFS
              │                               Master this, then BFS/DFS become obvious
Step 4   6.5 Tree & Binary Tree               Tree traversal = cycle-free graph traversal
              │                               Pre/In/Post-order are all special cases of DFS
Step 5   6.8 Recursion & Divide-and-Conquer   Recursive thinking = DFS mindset
              │                               Understand "go deep" and "backtrack" call stack
Step 6   6.6 Heap & Priority Queue            Complete binary tree + array, prep for Dijkstra
              │
Step 7   6.7 Graph Structure (Part 1)         1.1~1.6: BFS/DFS, connected components, cycles
              │                               Everything you learned so far converges here
Step 8   6.4 Hash Table Internals             Hash function, collision resolution, load factor
              │                               You've used dict/set — now understand the inside
Step 9   6.9 Sorting Algorithms               Timsort, quicksort, mergesort — applied divide-and-conquer
              │
Step 10  6.10 Search Algorithms               Binary search (needs sorted array), backtracking = DFS + pruning
              │
Step 11  6.11 Dynamic Programming             Top-down = recursion + memo, Bottom-up = fill the table
              │
Step 12  6.7 Graph Structure (Part 2)         1.7~1.10: Topological sort, Dijkstra, Prim, Kruskal
              │
Step 13  6.12 Graph & String Algorithms       A*, Union-Find, KMP, Trie — comprehensive applications
```

### 为什么这个顺序？

**核心原则：每个新概念只依赖你已经知道的东西。**

1. **栈和队列必须先学（第 3 步）**：BFS/DFS 说到底就是"用队列还是用栈来存待访问节点"。如果对 `pop()` vs `popleft()` 没有直觉，学图遍历就像蒙着眼走路。

2. **树必须早于图（第 4 步）**：树没有环 → 不需要 `visited` 集合 → 遍历逻辑更纯粹。先学树的三种遍历（前序/中序/后序 = DFS），再看图的 BFS/DFS，会发现只是多了一步"去重"。

3. **堆必须早于 Dijkstra（第 6 步）**：Dijkstra = BFS + 优先队列。BFS 按"层"扩散，Dijkstra 按"距离"扩散——把普通队列换成堆，就是 Dijkstra。

4. **图结构分两次学（第 7 + 12 步）**：第一次掌握基础和遍历，把图当成"比树多了一个 visited 的结构"来理解。第二次再学经典算法，在有遍历基础的前提下学最短路径、最小生成树。

5. **哈希表可以后置（第 8 步）**：日常已经用了大量 `dict`/`set`，先把它当黑盒用，等理解了其它结构后再回来拆解底层原理，会有"原来如此"的感觉。

### 学习方法建议

- **写 > 读**：每个概念配 15-20 行最简代码，手敲一遍比读十遍有用。
- **对比学**：BFS vs DFS、堆 vs 二叉搜索树、邻接表 vs 邻接矩阵——成对比较，差异就是理解。
- **可视化**：遍历类算法（BFS/DFS/树遍历）用纸画或用 `visualize_dfs_bfs.py` 单步跟踪。
- **回到实际**：学完一个算法后，想一个你项目中真实的场景可以用它解决。比如 BFS 连通分量 → 管线连通性分析。

---

## 数据结构可视化速览

在学习具体章节之前，先在脑海中建立每种数据结构的"形状记忆"——知道它长什么样，才能理解它为什么那样工作。

> 🎬 **强烈推荐**：[VisuAlgo.net](https://visualgo.net/zh) — 新加坡国立大学开发的交互式可视化平台，每种数据结构都有**可步进的动画演示**，边看代码边看动图。

---

### 数组（Array）= 一排连续编号的格子

```
Index:  0     1     2     3     4     5
      ┌─────┬─────┬─────┬─────┬─────┬─────┐
      │  2  │  4  │  8  │ 16  │ 32  │ 64  │
      └─────┴─────┴─────┴─────┴─────┴─────┘
      Continuous memory, each element same size

      arr[3] → O(1)   Calculate address offset directly
      insert/delete → O(n)   Shift all trailing elements
```

| Python 表达 | 本质 |
|-------------|------|
| `[1, 2, 3]` | 动态数组（自动扩容，均摊 O(1) append） |
| `list` | C 层面是 `PyObject**` 指针数组 |

> 🎬 [VisuAlgo: Array 动画](https://visualgo.net/zh/array) | 📖 [Python TimeComplexity](https://wiki.python.org/moin/TimeComplexity)

---

### 链表（Linked List）= 用指针串起来的节点链

单向链表（每个节点存"数据 + 下一个节点的地址"）:

```
    Head
     ↓
   ┌───┬───┐    ┌───┬───┐    ┌───┬───┐    ┌───┬──────┐
   │ 1 │ ●─┼───→│ 2 │ ●─┼───→│ 3 │ ●─┼───→│ 4 │ NIL  │
   └───┴───┘    └───┴───┘    └───┴───┘    └───┴──────┘
    data next    data next    data next    data next

双向链表（多一个 prev 指针，可以往回走）:

   NIL ←──┼───┬───┼───→ ←──┼───┬───┼───→ ←──┼───┬───┼──→ NIL
          │ 1 │ ● │      │ 2 │ ● │      │ 3 │ ● │
          └───┴───┘      └───┴───┘      └───┴───┘
           prev data next
```

| 操作 | 数组 | 链表 |
|------|:--:|:--:|
| 按索引访问 | O(1) ✅ | O(n) ❌ |
| 头部插入/删除 | O(n) ❌ | O(1) ✅ |
| 末尾插入 | O(1) ✅ | O(1) ✅ |
| 内存占用 | 连续，紧凑 | 分散，多一个指针 |

**关键直觉**：数组知道门牌号直接推门进去；链表必须从第一家挨个找过去。

> 🎬 [VisuAlgo: Linked List 动画](https://visualgo.net/zh/list)

---

### 栈（Stack）= 一摞盘子，后进先出（LIFO）

```
    push(3) →  ┌───┐
               │ 3 │  ← Top (last in)
               ├───┤
    push(2) →  │ 2 │
               ├───┤
    push(1) →  │ 1 │  ← Bottom (first in)
               └───┘
                   ← pop() always takes the top one (3)
```

```python
# list = natural stack in Python
stack = []
stack.append(1)     # push
stack.append(2)
stack.append(3)
stack.pop()         # → 3 (LIFO!)
stack.pop()         # → 2
```

**关键直觉**：你写递归时，函数的调用和返回就是"压栈→弹栈"。DFS 用栈来记住"我一会儿要回来处理的分支"。

> 🎬 [VisuAlgo: Stack 动画](https://visualgo.net/zh/stack)

---

### 队列（Queue）= 排队买票，先进先出（FIFO）

```
  Dequeue ←        ┌───┬───┬───┬───┬───┐        ← Enqueue
  (exit head)      │ 1 │ 2 │ 3 │ 4 │ 5 │      (enter tail)
                   └───┴───┴───┴───┴───┘
                   Head              Tail
                   (first in)        (last in)
```

```python
from collections import deque

queue = deque()
queue.append('A')      # enqueue (add to tail)
queue.append('B')
queue.append('C')
queue.popleft()        # → 'A' (FIFO!)
queue.popleft()        # → 'B'
```

**关键直觉**：BFS 用队列来"暂存下一层的所有节点"。先发现先处理，就是一层一层扩散。

> 🎬 [VisuAlgo: Queue 动画](https://visualgo.net/zh/queue)

---

### 哈希表（Hash Table）= 有"万能索引"的字典

```
         Key               Hash Function            Buckets
   ┌────────────┐                            ┌───┬─────────────┐
   │  "apple"   │──→  hash("apple")  ──→     [0] │             │
   │  "banana"  │──→  hash("banana") ──→     [1] │ ("banana",7)│
   │  "cherry"  │──→  hash("cherry") ──→     [2] │ ("cherry",3)│
   │  "date"    │──→  hash("date")   ──→ ┐   [3] │ ("date",9)  │
   └────────────┘                         └→  [4] │ ("apple",5) │
                                             └───┴─────────────┘
                Collision: two keys map to same bucket
                → resolved by Linked List chaining
```

```python
# dict and set are both hash tables
d = {'apple': 5, 'banana': 7}   # key→value, O(1) lookup
s = {'A', 'B', 'C'}             # set, O(1) membership test

d['cherry'] = 3    # O(1) insert
d['apple']         # O(1) lookup → 5
'A' in s           # O(1) → True
```

**关键直觉**：哈希表 = 字典的"部首检字法"。你知道读音，直接翻到那一页，不需要从第一页开始找。这就是 O(1) 的魔法。

> 🎬 [VisuAlgo: Hash Table 动画](https://visualgo.net/zh/hashtable) | 📖 [Python dict 实现](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)

---

### 树（Tree）= 有"父子"层次关系的结构，无环

```
                     (A)              Root
                    /   \
                  (B)   (C)          B, C = children of A
                  / \     \
                (D) (E)   (F)        D, E, F = leaves (no children)
                    / \
                  (G) (H)            Depth = edges from root to node
                                     D=2, G=3, C=1
```

```python
# Python: Node class + references
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

# Or use dict for "node → children list"
tree = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [], 'E': ['G', 'H'], 'F': [], 'G': [], 'H': [],
}
```

**树的三种遍历 = 处理节点的时机不同**：

| 遍历方式 | 顺序 | 结果 |
|----------|------|------|
| Pre-order | Root → Left → Right | A, B, D, E, G, H, C, F |
| In-order | Left → Root → Right | D, B, G, E, H, A, F, C |
| Post-order | Left → Right → Root | D, G, H, E, B, F, C, A |

**关键直觉**：树的遍历 = 图的 DFS，但树没有环，不需要 `visited` 去重。**先学树遍历，再学图遍历，会发现只是加了 visited。**

> 🎬 [VisuAlgo: BST 动画](https://visualgo.net/zh/bst) | 📖 [hello-algo: 二叉树](https://www.hello-algo.com/chapter_tree/binary_tree/)

---

### 堆（Heap）= 用数组存的完全二叉树，父节点总是 ≤ 子节点

最小堆（Min-Heap），`heap[k] <= heap[2k+1]` and `heap[k] <= heap[2k+2]`：

```
          (1)              Top = minimum
         /   \
       (3)   (2)
       / \   / \
     (7) (5)(4)

     Stored in array:  [1, 3, 2, 7, 5, 4]
     Index:              0  1  2  3  4  5

     Node 3 (idx=1) → left child = idx 3 (7),  right child = idx 4 (5)
     Node 5 (idx=4) → parent = idx 1 (3)
```

```python
import heapq

heap = []
heapq.heappush(heap, 3)    # insert, auto-maintain heap property
heapq.heappush(heap, 1)
heapq.heappush(heap, 2)
heapq.heappop(heap)        # → 1 (always pop the smallest)
heapq.heappop(heap)        # → 2
```

**关键直觉**：堆不保证"所有元素排好序"，只保证"最小的在最上面"。这就是为什么 push/pop 都是 O(log n)，比全排序 O(n log n) 快。

> 🎬 [VisuAlgo: Heap 动画](https://visualgo.net/zh/heap) | 📖 [Python heapq](https://docs.python.org/3/library/heapq.html)

---

### 图（Graph）= 节点 + 边，万物皆可图

```
 Undirected (edges = bidirectional)     Directed (edges = one-way)

     (A)──────(B)                        (A)──────→(B)
      │        │                          │         │
      │        │                          ↓         ↓
     (C)──────(D)                        (C)←──────(D)

   "We are friends" (mutual)           "I follow you" (directional)
```

```python
# Adjacency list = dict + set/list (most Pythonic)
undirected = {
    'A': {'B', 'C'},
    'B': {'A', 'D'},
    'C': {'A', 'D'},
    'D': {'B', 'C'},
}

directed = {
    'A': ['B', 'C'],       # A → B, A → C
    'B': ['D'],            # B → D
    'C': [],               # C has no outgoing edges
    'D': ['C'],            # D → C
}

# BFS = Queue + visited   (expand layer by layer)
# DFS = Stack + visited   (go deep first, then backtrack)
```

**关键直觉**：你之前做的**管线连通性分析**，本质就是：把水源点当起点，BFS 找出所有能到达的节点，剩下的就是孤立管段。图算法就在你身边。

> 🎬 [VisuAlgo: Graph 动画](https://visualgo.net/zh/graphds) | 📖 [Python collections](https://docs.python.org/3/library/collections.html)

---

### 七种结构关系总览

```
                      ┌───────────────────────┐
                      │       Array            │
                      │   Continuous memory    │
                      │   Python: list         │
                      └───────────┬────────────┘
                                  │
         ┌──────────┬──────────┬──┴──────┬──────────┬──────────┐
         ▼          ▼          ▼         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐
    │ Stack  │ │ Queue  │ │  Hash  │ │ Heap │ │ Dynamic│
    │  LIFO  │ │  FIFO  │ │ Table  │ │MinTop│ │ Array  │
    │append/ │ │append/ │ │  O(1)  │ │heapq │ │O(1)app.│
    │  pop   │ │popleft │ └───┬────┘ └──┬───┘ └────────┘
    └───┬────┘ └───┬────┘     │         │
        │          │          │         │
        │    ┌─────┘          │         │
        ▼    ▼                ▼         ▼
    ┌──────────┐   ┌─────────────────────────────┐
    │  Linked  │   │           Tree               │
    │  List    │   │    Acyclic connected graph   │
    │Node+next │   │    Python: class Node        │
    └──────────┘   └─────────────┬───────────────┘
                                 │
                      ┌──────────┼──────────┐
                      ▼          ▼          ▼
                 ┌────────┐ ┌────────┐ ┌────────┐
                 │ Binary │ │  Heap  │ │  Trie  │
                 │  Tree  │ │Complete│ │Prefix  │
                 │ ≤2 ch. │ │BinTree │ │  Tree  │
                 └────────┘ └────────┘ └────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │       Graph         │  ← The capstone
                      │  Python: dict+set   │
                      │  Nodes + Edges      │
                      │  (can have cycles)  │
                      └─────────────────────┘
```

> 🎬 **一站式交互学习**：[VisuAlgo](https://visualgo.net/zh) 支持上述所有结构的动画演示 · [hello-algo](https://www.hello-algo.com/) 提供精美插图的算法教程（开源免费）

---

## 数据结构篇

- [6.1 算法基础与复杂度](6.1_算法基础)
- [6.2 数组与链表](6.2_数组与链表)
- [6.3 栈与队列](6.3_栈与队列)
- [6.4 哈希表原理](6.4_哈希表原理)
- [6.5 树与二叉树](6.5_树与二叉树)
- [6.6 堆与优先队列](6.6_堆与优先队列)
- [6.7 图结构](6.7_图结构)

## 算法篇

- [6.8 递归与分治](6.8_递归与分治)
- [6.9 排序算法](6.9_排序算法)
- [6.10 搜索算法](6.10_搜索算法)
- [6.11 动态规划](6.11_动态规划)
- [6.12 图算法与字符串算法](6.12_图算法与字符串算法)
