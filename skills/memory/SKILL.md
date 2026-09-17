---
name: memory
description: "Use when reviewing C++ code for memory safety issues. 内存安全审查检查清单。"
version: 1.0.0
---

# 内存安全审查清单

## 检查项

1. **内存泄漏**：`new` 之后是否 `delete`（或用智能指针自动释放）
2. **空指针/悬垂指针**：裸指针是否有空指针解引用、悬垂指针（指向已释放内存）风险
3. **数组越界**：数组/缓冲区访问是否越界
4. **Rule of Three/Five**：管理资源的类是否定义析构/拷贝构造/拷贝赋值（避免浅拷贝导致 double free）
5. **智能指针**：是否该用 `unique_ptr`/`shared_ptr` 替代裸指针

## 修复建议

- 优先用 `std::string` 替代 `char*` 裸指针
- 用栈对象替代 `new`/`delete`
- 用智能指针管理堆资源
