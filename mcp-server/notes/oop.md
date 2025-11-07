

# 🧠 Object-Oriented Programming (OOP) in Java

## 1. Introduction

Object-Oriented Programming (OOP) is a programming paradigm centered around **objects** rather than functions or logic.  
It allows you to model real-world entities in code, making programs more modular, reusable, and scalable.

### 🌟 Key Benefits
- **Reusability:** Code can be reused via inheritance and polymorphism.  
- **Modularity:** Code is organized into objects and classes.  
- **Maintainability:** Easier to update and debug.  
- **Scalability:** Complex systems can be managed using OOP structure.

The **four main pillars** of OOP are:
1. **Encapsulation**
2. **Inheritance**
3. **Polymorphism**
4. **Abstraction**

---

## 2. Classes and Objects

### What is a Class?
A **class** is a blueprint for creating objects.  
It defines **fields** (data) and **methods** (behavior).

```java
class Car {
    String brand;
    int year;

    void displayInfo() {
        System.out.println("Brand: " + brand + ", Year: " + year);
    }
}
