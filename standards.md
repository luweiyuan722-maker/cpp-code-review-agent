# C++ 编码规范

## 1. 内存管理
禁止使用裸指针管理资源，必须用智能指针（unique_ptr/shared_ptr）或栈对象。
违反示例：char *name; 应改用 std::string。

## 2. RAII 原则
所有资源（内存、文件、锁）应在构造函数获取、析构函数释放。
违反示例：new 了对象却不 delete。

## 3. Rule of Three/Five
管理资源的类必须定义析构函数、拷贝构造、拷贝赋值（或显式禁用拷贝）。

## 4. const 正确性
不修改成员变量的成员函数必须声明为 const。

## 5. 头文件
头文件必须有 include guard（#pragma once 或 #ifndef）。
不得在头文件使用 using namespace std;