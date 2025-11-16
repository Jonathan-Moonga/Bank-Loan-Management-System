Bank Loan Management System (Python + Tkinter)

This project is a GUI-based **Bank Loan Management System** written in Python using **Tkinter**.  
It simulates core banking features such as:

- Admin & User login
- Account creation with password hashing
- Loan application & automated amortization calculations
- Loan approval / rejection workflows (admin-controlled)
- Balance crediting upon approval
- CSV-based persistent storage (for users and loans)

The system is built as a **prototype** meant for Data Structures & Algorithms (DSA) learning, GUI design practice, and full-stack Python fundamentals.

---

# 🚀 Features Overview

### 👤 **User (Client) Features**
- Create user account (username, email, income)
- Secure login using hashed passwords (SHA-256)
- View available balance & monthly income
- Apply for:
  - Housing Loan
  - Auto Loan
  - Personal Loan
- Loan application preview (monthly payments, interest, term, total interest)
- Income-based debt ratio checks (warns if payment > 50% of income)
- View recent loan applications

### 🛠️ **Admin Features**
- Admin-privileged login
- View all **pending** loan applications in a sortable table
- Approve or reject loan applications
- When approved:
  - User balance is credited with loan amount
  - Loan status updated in `loan_records.csv`

### 💾 **Persistent Storage**
Data is stored in local `.csv` files:

| File | Purpose |
|------|---------|
| `users.csv` | Account data (username, password hash, balance, income, role) |
| `loan_records.csv` | All loan applications and statuses |

Files are automatically created if missing.

---

# 🧠 Data Structures Used in This Project

This system uses Python’s built-in data structures to implement efficient lookups, updates, and workflow logic.

### **1. Dictionaries (`dict`) — O(1) Average Lookup**
Used to store and manage user accounts:

```python
users = {
    "john": {
        "password_hash": "...",
        "email": "...",
        "income": 4500.0,
        "user_type": "client",
        "balance": 0.0
    }
}
