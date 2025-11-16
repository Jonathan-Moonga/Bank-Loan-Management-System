# bank_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
import hashlib
from math import isfinite

# -----------------------------
# Configuration & constants
# -----------------------------
USERS_FILE = "users.csv"
LOANS_FILE = "loan_records.csv"

LOAN_OPTIONS = {
    "Housing Loan": {"rate": 5.2, "max_term": 25},
    "Auto Loan": {"rate": 7.5, "max_term": 6},
    "Personal Loan": {"rate": 9.6, "max_term": 10},
}

# -----------------------------
# Utility & Data Layer
# -----------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def ensure_files_exist():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash", "email", "income", "user_type", "balance"])
        print("No admin account found. Please create one now.")
        admin_user = input("Enter admin username: ").strip()
        admin_pw = input("Enter admin password: ").strip()
        admin_email = input("Enter admin email: ").strip()
        with open(USERS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                admin_user,
                hash_password(admin_pw),
                admin_email,
                "0",
                "admin",
                "0.0"
            ])
        print(f"Admin account '{admin_user}' created successfully.")

    # loan_records.csv header: id,username,loan_type,amount,interest_rate,term_years,monthly_payment,total_interest,status
    if not os.path.exists(LOANS_FILE):
        with open(LOANS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id","username","loan_type","amount","interest_rate","term_years","monthly_payment","total_interest","status"])

def load_users_to_dict():
    """Load users into dict for O(1) lookup: {username: {fields...}}"""
    users = {}
    if not os.path.exists(USERS_FILE):
        return users
    with open(USERS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            users[r["username"]] = {
                "password_hash": r["password_hash"],
                "email": r["email"],
                "income": float(r["income"]) if r["income"] else 0.0,
                "user_type": r["user_type"],
                "balance": float(r.get("balance", 0.0)),
            }
    return users

def write_users_from_dict(users):
    with open(USERS_FILE, "w", newline="") as f:
        fieldnames = ["username", "password_hash", "email", "income", "user_type", "balance"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for u, meta in users.items():
            writer.writerow({
                "username": u,
                "password_hash": meta["password_hash"],
                "email": meta["email"],
                "income": meta["income"],
                "user_type": meta["user_type"],
                "balance": meta["balance"],
            })

def append_loan_record(record: dict):
    # record keys: id,username,loan_type,amount,interest_rate,term_years,monthly_payment,total_interest,status
    with open(LOANS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([record[k] for k in ["id","username","loan_type","amount","interest_rate","term_years","monthly_payment","total_interest","status"]])

def load_loans():
    loans = []
    if not os.path.exists(LOANS_FILE):
        return loans
    with open(LOANS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # convert numeric fields
            r["amount"] = float(r["amount"])
            r["interest_rate"] = float(r["interest_rate"])
            r["term_years"] = float(r["term_years"])
            r["monthly_payment"] = float(r["monthly_payment"])
            r["total_interest"] = float(r["total_interest"])
            loans.append(r)
    return loans

def next_loan_id():
    # simple id generator by counting rows in file
    if not os.path.exists(LOANS_FILE):
        return "1"
    with open(LOANS_FILE, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # subtract header
        return str(max(1, len(rows)))  # not perfect but simple for prototype

# -----------------------------
# Loan Calculation Logic
# -----------------------------
def calculate_monthly_payment(principal, annual_rate, term_years):
    """Return monthly payment using standard formula."""
    if term_years <= 0 or principal <= 0:
        return None
    r = annual_rate / 100.0 / 12.0
    n = term_years * 12
    if r == 0:
        return principal / n
    # formula:
    numerator = principal * r * (1 + r) ** n
    denominator = (1 + r) ** n - 1
    if denominator == 0:
        return None
    M = numerator / denominator
    return M

def total_interest_paid(monthly_payment, principal, term_years):
    n = term_years * 12
    return monthly_payment * n - principal

# -----------------------------
# GUI Application
# -----------------------------
class BankApp:
    def __init__(self, root):
        ensure_files_exist()
        self.root = root
        self.root.title("Bank Loan System - Prototype")
        self.users = load_users_to_dict()
        self.loans = load_loans()
        self.current_user = None  # username
        self.create_welcome_screen()

    # -------------------------
    # Welcome Screen
    # -------------------------
    def create_welcome_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text="WELCOME TO CHASE (Prototype)", font=("Helvetica", 18))
        title.grid(row=0, column=0, columnspan=3, pady=(0,20))

        # Login button and dropdown for admin login alternative
        login_lbl = ttk.Label(frame, text="Login:")
        login_lbl.grid(row=1, column=0, sticky=tk.W)
        login_btn = ttk.Button(frame, text="Login", command=lambda: self.open_login_dropdown(role_choice=None))
        login_btn.grid(row=1, column=1, sticky=tk.W)
        # small arrow -> dropdown
        login_menu_btn = ttk.Menubutton(frame, text="▾")
        login_menu = tk.Menu(login_menu_btn, tearoff=0)
        login_menu.add_command(label="Login as Admin", command=lambda: self.open_login_dropdown(role_choice="admin"))
        login_menu.add_command(label="Login as User", command=lambda: self.open_login_dropdown(role_choice="client"))
        login_menu_btn["menu"] = login_menu
        login_menu_btn.grid(row=1, column=2, sticky=tk.W)

        # Create account and dropdown to create as admin
        create_lbl = ttk.Label(frame, text="Create Account:")
        create_lbl.grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        create_btn = ttk.Button(frame, text="Create Account", command=lambda: self.open_create_account_dropdown(role_choice=None))
        create_btn.grid(row=2, column=1, sticky=tk.W, pady=(10,0))
        create_menu_btn = ttk.Menubutton(frame, text="▾")
        create_menu = tk.Menu(create_menu_btn, tearoff=0)
        create_menu.add_command(label="Create account as Admin", command=lambda: self.open_create_account_dropdown(role_choice="admin"))
        create_menu.add_command(label="Create account as User", command=lambda: self.open_create_account_dropdown(role_choice="client"))
        create_menu_btn["menu"] = create_menu
        create_menu_btn.grid(row=2, column=2, sticky=tk.W, pady=(10,0))

        # Forgot password area
        forgot = ttk.Button(frame, text="Forgot Password", command=self.forgot_password_flow)
        forgot.grid(row=4, column=0, columnspan=3, pady=(30,0))

        # Small footer
        footer = ttk.Label(frame, text="Prototype - balances reflect approved loans only", font=("Helvetica", 8))
        footer.grid(row=5, column=0, columnspan=3, pady=(20,0))

    def open_login_dropdown(self, role_choice=None):
        # role_choice can be 'admin' or 'client' or None (ask)
        if role_choice is None:
            role_choice = simpledialog.askstring("Login type", "Login as ('admin' or 'client')? Leave blank for user.")
            if role_choice is None:
                return
            role_choice = role_choice.strip().lower()
            if role_choice not in ("admin", "client", ""):
                messagebox.showerror("Error", "Please enter 'admin' or 'client' or leave blank.")
                return
            if role_choice == "":
                role_choice = "client"

        # now open login dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Login")
        ttk.Label(dialog, text=f"Login ({role_choice})").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(dialog, text="Username:").grid(row=1, column=0)
        user_entry = ttk.Entry(dialog)
        user_entry.grid(row=1, column=1)
        ttk.Label(dialog, text="Password:").grid(row=2, column=0)
        pw_entry = ttk.Entry(dialog, show="*")
        pw_entry.grid(row=2, column=1)

        def attempt_login():
            username = user_entry.get().strip()
            pw = pw_entry.get().strip()
            if username not in self.users:
                messagebox.showerror("Login failed", "No such user.")
                return
            stored = self.users[username]
            if stored["password_hash"] != hash_password(pw):
                messagebox.showerror("Login failed", "Incorrect password.")
                return
            if stored["user_type"] != role_choice:
                messagebox.showerror("Login failed", f"User type mismatch. You tried to login as {role_choice}.")
                return
            self.current_user = username
            dialog.destroy()
            if role_choice == "admin":
                self.open_admin_dashboard()
            else:
                self.open_client_dashboard()

        ttk.Button(dialog, text="Login", command=attempt_login).grid(row=3, column=0, columnspan=2, pady=10)

    def open_create_account_dropdown(self, role_choice=None):
        if role_choice is None:
            role_choice = simpledialog.askstring("Create Account", "Create account as ('admin' or 'client')? Leave blank for user.")
            if role_choice is None:
                return
            role_choice = role_choice.strip().lower()
            if role_choice not in ("admin", "client", ""):
                messagebox.showerror("Error", "Please enter 'admin' or 'client' or leave blank.")
                return
            if role_choice == "":
                role_choice = "client"

        dialog = tk.Toplevel(self.root)
        dialog.title("Create Account")
        ttk.Label(dialog, text=f"Create Account ({role_choice})").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(dialog, text="Username:").grid(row=1, column=0)
        user_entry = ttk.Entry(dialog)
        user_entry.grid(row=1, column=1)
        ttk.Label(dialog, text="Email:").grid(row=2, column=0)
        email_entry = ttk.Entry(dialog)
        email_entry.grid(row=2, column=1)
        ttk.Label(dialog, text="Password:").grid(row=3, column=0)
        pw_entry = ttk.Entry(dialog, show="*")
        pw_entry.grid(row=3, column=1)
        ttk.Label(dialog, text="Monthly Income:").grid(row=4, column=0)
        income_entry = ttk.Entry(dialog)
        income_entry.grid(row=4, column=1)

        def create_account():
            username = user_entry.get().strip()
            email = email_entry.get().strip()
            pw = pw_entry.get().strip()
            try:
                income = float(income_entry.get().strip() or 0.0)
            except:
                messagebox.showerror("Error", "Please enter a valid income")
                return
            if not username or not pw:
                messagebox.showerror("Error", "Username and password required")
                return
            if username in self.users:
                messagebox.showerror("Error", "Username already exists")
                return
            self.users[username] = {
                "password_hash": hash_password(pw),
                "email": email,
                "income": income,
                "user_type": role_choice,
                "balance": 0.0
            }
            write_users_from_dict(self.users)
            messagebox.showinfo("Success", f"Account '{username}' created as {role_choice}")
            dialog.destroy()

        ttk.Button(dialog, text="Create", command=create_account).grid(row=5, column=0, columnspan=2, pady=10)

    def forgot_password_flow(self):
        # Ask whether user or admin
        kind = simpledialog.askstring("Account Recovery", "Are you recovering a 'user' or 'admin' account? (type user/admin)")
        if not kind:
            return
        kind = kind.strip().lower()
        if kind not in ("user", "admin"):
            messagebox.showerror("Error", "Please enter 'user' or 'admin'")
            return
        username = simpledialog.askstring("Recover", f"Enter username for {kind}:")
        if not username:
            return
        if username not in self.users or self.users[username]["user_type"] != ("admin" if kind=="admin" else "client"):
            messagebox.showerror("Error", "No matching account found.")
            return
        newpw = simpledialog.askstring("New Password", "Enter new password:", show="*")
        if not newpw:
            return
        self.users[username]["password_hash"] = hash_password(newpw)
        write_users_from_dict(self.users)
        messagebox.showinfo("Success", "Password updated. You can now login.")

    # -------------------------
    # Client Dashboard
    # -------------------------
    def open_client_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        user_meta = self.users[self.current_user]

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        topbar = ttk.Frame(main)
        topbar.pack(fill=tk.X)
        ttk.Label(topbar, text=f"Client Dashboard - {self.current_user}", font=("Helvetica", 14)).pack(side=tk.LEFT)
        ttk.Button(topbar, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        # Overhead menus row
        menu_frame = ttk.Frame(main, padding=(0,10))
        menu_frame.pack(fill=tk.X)
        for label in ["Send || Zelle", "Deposit", "Pay Bills", "Get Loan"]:
            ttk.Button(menu_frame, text=label).pack(side=tk.LEFT, padx=8)

        # Salary / Balance big section
        balance_frame = ttk.LabelFrame(main, text="Salary & Balance", padding=10)
        balance_frame.pack(fill=tk.X, pady=10)
        bal = user_meta.get("balance", 0.0)
        income = user_meta.get("income", 0.0)
        ttk.Label(balance_frame, text=f"Available balance: ${bal:,.2f}", font=("Helvetica", 12)).pack(anchor=tk.W)
        ttk.Label(balance_frame, text=f"Monthly Salary: ${income:,.2f}", font=("Helvetica", 10)).pack(anchor=tk.W)

        # Account summary area
        summary_frame = ttk.LabelFrame(main, text="Account Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        # We'll show last 5 loans
        loans = load_loans()
        user_loans = [l for l in loans if l.get("username")==self.current_user]
        ttk.Label(summary_frame, text=f"Loans (last {min(5,len(user_loans))}):").pack(anchor=tk.W)
        for l in user_loans[-5:]:
            ttk.Label(summary_frame, text=f"{l['loan_type']} ${l['amount']:.2f} - {l['status']} - ${l['monthly_payment']:.2f}/mo").pack(anchor=tk.W)

        # Big Take Loan section
        take_loan_frame = ttk.LabelFrame(main, text="Take a Loan", padding=10)
        take_loan_frame.pack(fill=tk.X, pady=10)
        ttk.Label(take_loan_frame, text="Click below to start a new loan application").pack(anchor=tk.W)
        ttk.Button(take_loan_frame, text="Start Loan Application", command=self.open_loan_application).pack(anchor=tk.W)

    def open_loan_application(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Loan Application")

        ttk.Label(dialog, text="Select Loan Type:").grid(row=0, column=0, sticky=tk.W, pady=4)
        loan_type_cb = ttk.Combobox(dialog, values=list(LOAN_OPTIONS.keys()), state="readonly")
        loan_type_cb.current(0)
        loan_type_cb.grid(row=0, column=1, pady=4)

        ttk.Label(dialog, text="Loan Amount:").grid(row=1, column=0, sticky=tk.W)
        amount_e = ttk.Entry(dialog)
        amount_e.grid(row=1, column=1)

        ttk.Label(dialog, text="Term (years):").grid(row=2, column=0, sticky=tk.W)
        term_e = ttk.Entry(dialog)
        term_e.grid(row=2, column=1)

        ttk.Label(dialog, text="Monthly Income (for debt check):").grid(row=3, column=0, sticky=tk.W)
        income_e = ttk.Entry(dialog)
        income_e.insert(0, str(self.users[self.current_user]["income"]))
        income_e.grid(row=3, column=1)

        def preview_and_submit():
            loan_type = loan_type_cb.get()
            try:
                amount = float(amount_e.get())
                term = float(term_e.get())
                income = float(income_e.get())
            except:
                messagebox.showerror("Error", "Please enter valid numeric values.")
                return
            opt = LOAN_OPTIONS[loan_type]
            if term <= 0 or term > opt["max_term"]:
                messagebox.showerror("Error", f"Term must be >0 and <= {opt['max_term']} years for {loan_type}.")
                return
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive.")
                return

            monthly = calculate_monthly_payment(amount, opt["rate"], term)
            if monthly is None or not isfinite(monthly):
                messagebox.showerror("Error", "Could not compute monthly payment.")
                return
            tot_interest = total_interest_paid(monthly, amount, term)
            # Debt ratio check
            if monthly > 0.5 * income:
                # suggest increasing term if possible
                allow = messagebox.askyesno("Debt ratio exceeded", 
                    f"Monthly payment ${monthly:.2f} exceeds 50% of income (${0.5*income:.2f}).\nWould you like to increase term (if possible) or reduce amount?")
                if not allow:
                    return
            # Show summary and ask to submit (this will become PENDING)
            summary = (f"Loan Type: {loan_type}\nAmount: ${amount:.2f}\nTerm: {term} years\n"
                       f"Rate: {opt['rate']}%\nMonthly payment: ${monthly:.2f}\nTotal interest: ${tot_interest:.2f}\n\n"
                       "Proceed to submit application? (It will be pending until admin approval)")
            if messagebox.askyesno("Confirm Loan Application", summary):
                rec = {
                    "id": next_loan_id(),
                    "username": self.current_user,
                    "loan_type": loan_type,
                    "amount": amount,
                    "interest_rate": opt["rate"],
                    "term_years": term,
                    "monthly_payment": round(monthly,2),
                    "total_interest": round(tot_interest,2),
                    "status": "pending"
                }
                append_loan_record(rec)
                messagebox.showinfo("Submitted", "Loan application submitted and is pending approval.")
                dialog.destroy()

        ttk.Button(dialog, text="Preview & Submit", command=preview_and_submit).grid(row=4, column=0, columnspan=2, pady=10)

    # -------------------------
    # Admin Dashboard
    # -------------------------
    def open_admin_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        topbar = ttk.Frame(main)
        topbar.pack(fill=tk.X)
        ttk.Label(topbar, text=f"Admin Dashboard - {self.current_user}", font=("Helvetica", 14)).pack(side=tk.LEFT)
        ttk.Button(topbar, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        # Loans table
        loans_frame = ttk.LabelFrame(main, text="Loan Applications (Pending)", padding=10)
        loans_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tree = ttk.Treeview(loans_frame, columns=("id","username","type","amount","term","monthly","status"), show="headings")
        for c, heading in [("id","ID"),("username","Username"),("type","Type"),("amount","Amount"),("term","Term (yrs)"),("monthly","Monthly"),("status","Status")]:
            tree.heading(c, text=heading)
            tree.column(c, width=100)
        tree.pack(fill=tk.BOTH, expand=True)

        # populate
        loans = load_loans()
        pending = [l for l in loans if l["status"].lower()=="pending"]
        for l in pending:
            tree.insert("", tk.END, values=(l["id"], l["username"], l["loan_type"], f"${l['amount']:.2f}", l["term_years"], f"${l['monthly_payment']:.2f}", l["status"]))

        # Approve / Reject buttons
        def approve_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Select a pending loan first")
                return
            item = tree.item(sel[0])["values"]
            loan_id = str(item[0])
            # load file, update status
            loans_all = load_loans()
            modified = False
            for row in loans_all:
                if row["id"] == loan_id:
                    row["status"] = "approved"
                    # credit user balance
                    username = row["username"]
                    # load users dict (in-memory)
                    self.users = load_users_to_dict()
                    if username in self.users:
                        # Add funds to balance
                        self.users[username]["balance"] = float(self.users[username].get("balance",0.0)) + float(row["amount"])
                        write_users_from_dict(self.users)
                    modified = True
            if modified:
                # overwrite loans file with updated statuses
                # simple rewrite approach:
                with open(LOANS_FILE, "w", newline="") as f:
                    fieldnames = ["id","username","loan_type","amount","interest_rate","term_years","monthly_payment","total_interest","status"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in loans_all:
                        writer.writerow({k: r[k] for k in fieldnames})
                messagebox.showinfo("Approved", f"Loan {loan_id} approved and funds credited to user.")
                self.open_admin_dashboard()
            else:
                messagebox.showerror("Error", "Loan not found.")

        def reject_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Select a pending loan first")
                return
            item = tree.item(sel[0])["values"]
            loan_id = str(item[0])
            loans_all = load_loans()
            modified = False
            for row in loans_all:
                if row["id"] == loan_id:
                    row["status"] = "rejected"
                    modified = True
            if modified:
                with open(LOANS_FILE, "w", newline="") as f:
                    fieldnames = ["id","username","loan_type","amount","interest_rate","term_years","monthly_payment","total_interest","status"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in loans_all:
                        writer.writerow({k: r[k] for k in fieldnames})
                messagebox.showinfo("Rejected", f"Loan {loan_id} rejected.")
                self.open_admin_dashboard()
            else:
                messagebox.showerror("Error", "Loan not found.")

        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Approve Selected", command=approve_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reject Selected", command=reject_selected).pack(side=tk.LEFT, padx=5)

    def logout(self):
        self.current_user = None
        self.create_welcome_screen()

# -----------------------------
# App entrypoint
# -----------------------------
def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = BankApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
