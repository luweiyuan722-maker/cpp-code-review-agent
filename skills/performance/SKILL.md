---
name: performance
description: "Use when reviewing C++ code for performance issues. 性能审查检查清单。"
version: 1.0.0
---

# 性能审查清单

## 检查项

1. **多余拷贝**：值传递/返回值是否导致不必要的深拷贝（应使用引用或移动语义）
2. **循环优化**：循环内是否有重复计算、不必要的函数调用、低效的字符串拼接
3. **移动语义**：是否该用 `std::move` / 右值引用避免拷贝
4. **缓存友好**：数据结构访问是否连续内存（`std::vector` vs 链表）

## 修复建议

- 传参用 `const&` 或「值 + std::move」
- 大对象返回走移动构造（而非拷贝）
- 优先用 `std::vector`（连续内存，缓存友好）
- 避免在循环内做不必要的堆分配
