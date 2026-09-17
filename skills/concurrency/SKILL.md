---
name: concurrency
description: "Use when reviewing C++ code for concurrency safety issues. 并发安全审查检查清单。"
version: 1.0.0
---

# 并发安全审查清单

## 检查项

1. **数据竞争**：共享数据是否加锁（未加锁的共享读写是 UB）
2. **死锁**：多个锁的获取顺序是否一致（避免锁顺序反转）
3. **竞态条件**：检查-再操作（check-then-act）是否有竞态
4. **原子操作**：简单共享变量是否该用 `std::atomic` 替代锁

## 修复建议

- 共享可变状态用 `std::mutex` + `std::lock_guard` 保护
- 避免持锁做 I/O（易引发锁顺序反转）
- 只读共享用 `const` 表达"可安全并发读"
