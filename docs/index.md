---
# 首页使用独立的 hero 布局
layout: home

hero:
  name: "Python 进阶教程"
  text: "深入内部机制 · 现代用法 · 设计思想"
  tagline: 面向有基础的开发者，重新认识 Python 3.12+
  actions:
    - theme: brand
      text: 开始学习
      link: /00_快速基础/
    - theme: alt
      text: 教学计划
      link: /教学计划

features:
  - icon: 🚀
    title: 快速基础
    details: 给有其他语言经验的开发者：变量、字符串、容器、控制流、dict/set——15 分钟一节，零安装上手
    link: /00_快速基础/

  - icon: 🧠
    title: 重新认识基础
    details: 对象模型、名字绑定、描述符协议——纠正常见误解，建立准确的 Python 心智模型
    link: /01_基础/

  - icon: 🏗️
    title: 面向对象哲学
    details: Python 风格的 OOP：元类、MRO、数据类、类型系统进阶——理解语言设计者的意图
    link: /02_面向对象/

  - icon: ⚡
    title: 高级主题深度
    details: 迭代器/生成器、装饰器、asyncio、内存管理——掌握 Python 最强大的语言特性
    link: /03_高级主题/

  - icon: 📦
    title: 库与生态
    details: NumPy、FastAPI、SQLAlchemy、Pydantic——不讲 API 大全，讲设计思想与简化实现
    link: /04_库与生态/

  - icon: 🎯
    title: 设计与品味
    details: Pythonic 惯用法、SOLID 原则、设计模式、错误处理哲学——跳出语法，培养代码品味
    link: /05_设计与品味/

  - icon: 🔢
    title: Python 基础算法
    details: 排序、搜索、DP、图论——聚焦 Python 内置数据结构与模块的算法视角，而非翻译教科书
    link: /06_python的基础算法/

  - icon: ▶️
    title: 可运行示例
    details: 代码块内嵌 Python 3.12 运行时（Pyodide），点击即可编辑运行，零安装上手
---

## 关于本教程

本教程不同于市面上常见的 Python 入门书。它**不是参考手册**（查 API 去官方文档），而是帮你：

- **纠正常见误解**，建立正确的 Python 心智模型
- **理解设计思想**，知道每个特性"为什么存在"和"怎么用才对"
- **掌握现代用法**，紧跟 Python 3.10-3.13 的新特性
- **提升代码品味**，写出地道、可测试、有美感的 Python 代码

每个核心概念附带 **Python 官方文档**原文引用链接，每个框架章节提供 **50-80 行的简化实现**帮你理解底层原理。
