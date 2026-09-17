#include <iostream>
#include <cstring>
using namespace std;

class Student {
public:
    char *name;   // 裸指针，没有正确管理
    int age;
    Student(const char *n, int a);
    ~Student();   // 声明了析构，但没实现
    void print();
};
