#include <iostream>
#include "student.h"
using namespace std;

int main() {
    Student *s = new Student("张三", 20);
    s->print();
    // 忘了 delete s  ← 内存泄漏
    return 0;
}
