from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from io import StringIO
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import csv

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)


# MODELS
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(120))


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), nullable=False, default="Pending")


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80))
    designation = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    date_of_joining = db.Column(db.String(20))  # e.g. "2023-05-01"
    status = db.Column(db.String(30), default="Active")
    salary = db.Column(db.Float, default=0.0)  # monthly salary

    # bank details
    bank_name = db.Column(db.String(120))
    bank_account = db.Column(db.String(50))
    bank_ifsc = db.Column(db.String(20))


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    status = db.Column(db.String(20), default="Present")  # Present / Absent / Leave
    remarks = db.Column(db.String(200))

    employee = db.relationship('Employee', backref=db.backref('attendance_records', lazy=True))


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed


# AUTH HELPERS
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def seed_demo_data():
    # Inventory
    if not InventoryItem.query.first():
        items = [
            InventoryItem(sku="SKU-001", name="A4 Paper Pack", category="Stationery", quantity=130, reorder_level=20),
            InventoryItem(sku="SKU-002", name="Ink Cartridge 912XL", category="Printing", quantity=18, reorder_level=10),
            InventoryItem(sku="SKU-003", name="Office Chair", category="Furniture", quantity=6, reorder_level=3),
        ]
        db.session.add_all(items)

    # Customers
    if not Customer.query.first():
        customers = [
            Customer(name="Saneesa Retail Pvt. Ltd.", email="info@saneesa.com", phone="9876543210", company="Saneesa"),
            Customer(name="Brightway Traders", email="sales@brightway.in", phone="9988776655", company="Brightway"),
        ]
        db.session.add_all(customers)

    # Orders
    if not Order.query.first():
        orders = [
            Order(order_number="SO-1048", customer_name="Saneesa Retail Pvt. Ltd.", amount=42300.0, status="Paid"),
            Order(order_number="SO-1047", customer_name="Brightway Traders", amount=15900.0, status="Overdue"),
        ]
        db.session.add_all(orders)

    # Employees
    if not Employee.query.first():
        employees = [
            Employee(
                emp_code="EMP-001",
                name="Riya Sharma",
                department="HR",
                designation="HR Manager",
                email="riya.sharma@example.com",
                phone="9876543210",
                date_of_joining="2022-01-10",
                status="Active",
                salary=60000,
                bank_name="HDFC Bank",
                bank_account="50100234567890",
                bank_ifsc="HDFC0001234"
            ),
            Employee(
                emp_code="EMP-002",
                name="Aditya Verma",
                department="Sales",
                designation="Sales Executive",
                email="aditya.verma@example.com",
                phone="9988776655",
                date_of_joining="2021-09-05",
                status="Active",
                salary=45000,
                bank_name="State Bank of India",
                bank_account="12345678901",
                bank_ifsc="SBIN0005678"
            )
        ]
        db.session.add_all(employees)

    # Some demo attendance (this month)
    if not Attendance.query.first():
        e1 = Employee.query.filter_by(emp_code="EMP-001").first()
        e2 = Employee.query.filter_by(emp_code="EMP-002").first()
        if e1 and e2:
            today = date.today()
            records = []
            for i in range(1, 6):
                d = date(today.year, today.month, i)
                records.append(Attendance(
                    employee_id=e1.id,
                    date=d,
                    check_in=datetime.strptime("09:30", "%H:%M").time(),
                    check_out=datetime.strptime("18:00", "%H:%M").time(),
                    status="Present"
                ))
                records.append(Attendance(
                    employee_id=e2.id,
                    date=d,
                    check_in=datetime.strptime("10:00", "%H:%M").time(),
                    check_out=datetime.strptime("18:30", "%H:%M").time(),
                    status="Present"
                ))
            db.session.add_all(records)

    # Admin user
    if not Admin.query.first():
        admin = Admin(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)

    db.session.commit()


def create_tables():
    db.create_all()
    seed_demo_data()


def get_module_usage():
    """Return (rows, total_records) for module usage on dashboard & reports."""
    rows = []

    inv_count = InventoryItem.query.count()
    orders_count = Order.query.count()
    customers_count = Customer.query.count()
    employees_count = Employee.query.count()
    attendance_count = Attendance.query.count()

    rows.append({"name": "Inventory", "records": inv_count})
    rows.append({"name": "Orders", "records": orders_count})
    rows.append({"name": "Customers", "records": customers_count})
    rows.append({"name": "Employees", "records": employees_count})
    rows.append({"name": "Attendance Records", "records": attendance_count})

    total = sum(r["records"] for r in rows) or 1

    for r in rows:
        r["percentage"] = round((r["records"] / total) * 100, 1) if r["records"] else 0.0

    return rows, total


def parse_time_or_none(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


def compute_payroll_for_employee(emp, month, year):
    """Return a dict with salary breakdown for one employee for a given month/year."""
    base_salary = emp.salary or 0.0

    # Month range
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    # --- Annual leave logic ---
    # All LEAVE records in this year, ordered by date
    leaves_year = Attendance.query.filter(
        Attendance.employee_id == emp.id,
        Attendance.status == "Leave",
        Attendance.date >= date(year, 1, 1),
        Attendance.date <= date(year, 12, 31)
    ).order_by(Attendance.date.asc()).all()

    total_leaves_used = len(leaves_year)
    allowed_leaves = 25

    unpaid_leaves_in_month = 0
    # Leaves beyond 25 in the year are unpaid; count those that fall in this month
    for idx, rec in enumerate(leaves_year, start=1):
        if idx > allowed_leaves and rec.date.year == year and rec.date.month == month:
            unpaid_leaves_in_month += 1

    # Assume salary is for 30 days
    daily_rate = base_salary / 30.0 if base_salary else 0.0
    extra_leave_deduction = unpaid_leaves_in_month * daily_rate

    # --- Weekly 40 hours logic ---
    from collections import defaultdict
    week_hours = defaultdict(float)

    records_month = Attendance.query.filter(
        Attendance.employee_id == emp.id,
        Attendance.date >= month_start,
        Attendance.date <= month_end
    ).all()

    for rec in records_month:
        if rec.check_in and rec.check_out and rec.status == "Present":
            dt_in = datetime.combine(rec.date, rec.check_in)
            dt_out = datetime.combine(rec.date, rec.check_out)
            delta = dt_out - dt_in
            hours = max(0.0, delta.total_seconds() / 3600.0)
            iso_year, iso_week, _ = rec.date.isocalendar()
            key = (iso_year, iso_week)
            week_hours[key] += hours

    total_shortfall_hours = 0.0
    for _, hours in week_hours.items():
        if hours < 40:
            total_shortfall_hours += (40 - hours)

    # Assume monthly salary covers ~160 working hours (4 weeks * 40h)
    hourly_rate = base_salary / 160.0 if base_salary else 0.0
    hours_deduction = total_shortfall_hours * hourly_rate

    net_pay = max(0.0, base_salary - extra_leave_deduction - hours_deduction)

    remaining_leaves = max(0, allowed_leaves - total_leaves_used)

    return {
        "employee": emp,
        "base_salary": base_salary,
        "unpaid_leaves_in_month": unpaid_leaves_in_month,
        "extra_leave_deduction": extra_leave_deduction,
        "total_leaves_used": total_leaves_used,
        "remaining_leaves": remaining_leaves,
        "total_shortfall_hours": round(total_shortfall_hours, 2),
        "hours_deduction": hours_deduction,
        "net_pay": net_pay,
    }


# AUTH ROUTES
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ROUTES
@app.route("/")
@login_required
def dashboard():
    total_items = db.session.query(db.func.count(InventoryItem.id)).scalar() or 0
    low_stock = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level).count()
    total_customers = db.session.query(db.func.count(Customer.id)).scalar() or 0
    total_orders = db.session.query(db.func.count(Order.id)).scalar() or 0

    recent_orders = Order.query.order_by(Order.id.desc()).limit(6).all()

    module_usage, total_usage = get_module_usage()

    return render_template(
        "dashboard.html",
        page_title="Dashboard",
        total_items=total_items,
        low_stock=low_stock,
        total_customers=total_customers,
        total_orders=total_orders,
        orders=recent_orders,
        module_usage=module_usage,
        total_usage=total_usage,
    )


@app.route("/inventory", methods=["GET", "POST"])
@login_required
def inventory():
    if request.method == "POST":
        sku = (request.form.get("sku") or "").strip()
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        quantity = int(request.form.get("quantity") or 0)
        reorder_level = int(request.form.get("reorder_level") or 0)

        if not sku or not name or not category:
            flash("SKU, Name and Category are required.", "error")
        else:
            existing = InventoryItem.query.filter_by(sku=sku).first()
            if existing:
                flash("An item with this SKU already exists.", "error")
            else:
                item = InventoryItem(
                    sku=sku,
                    name=name,
                    category=category,
                    quantity=quantity,
                    reorder_level=reorder_level
                )
                db.session.add(item)
                db.session.commit()
                flash("Inventory item added.", "success")

        return redirect(url_for("inventory"))

    items = InventoryItem.query.order_by(InventoryItem.id.desc()).all()
    return render_template("inventory.html", page_title="Inventory", items=items)


@app.route("/inventory/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_inventory(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("inventory"))


@app.route("/orders", methods=["GET", "POST"])
@login_required
def orders_page():
    if request.method == "POST":
        order_number = (request.form.get("order_number") or "").strip()
        customer_name = (request.form.get("customer_name") or "").strip()
        amount = float(request.form.get("amount") or 0)
        status = request.form.get("status") or "Pending"

        if not order_number or not customer_name:
            flash("Order number and Customer name are required.", "error")
        else:
            existing = Order.query.filter_by(order_number=order_number).first()
            if existing:
                flash("Order with this number already exists.", "error")
            else:
                order = Order(
                    order_number=order_number,
                    customer_name=customer_name,
                    amount=amount,
                    status=status
                )
                db.session.add(order)
                db.session.commit()
                flash("Order created.", "success")

        return redirect(url_for("orders_page"))

    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template("orders.html", page_title="Orders", orders=orders)


@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers_page():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        company = (request.form.get("company") or "").strip()

        if not name:
            flash("Customer name is required.", "error")
        else:
            customer = Customer(name=name, email=email, phone=phone, company=company)
            db.session.add(customer)
            db.session.commit()
            flash("Customer added.", "success")

        return redirect(url_for("customers_page"))

    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template("customers.html", page_title="Customers", customers=customers)


@app.route("/finance")
@login_required
def finance_page():
    total_paid = db.session.query(db.func.sum(Order.amount)).filter(Order.status == "Paid").scalar() or 0
    total_overdue = db.session.query(db.func.sum(Order.amount)).filter(Order.status == "Overdue").scalar() or 0
    total_pending = db.session.query(db.func.sum(Order.amount)).filter(Order.status == "Pending").scalar() or 0

    return render_template(
        "finance.html",
        page_title="Finance",
        total_paid=total_paid,
        total_overdue=total_overdue,
        total_pending=total_pending
    )


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html", page_title="Settings")


@app.route("/employees", methods=["GET", "POST"])
@login_required
def employees_page():
    if request.method == "POST":
        emp_code = (request.form.get("emp_code") or "").strip()
        name = (request.form.get("name") or "").strip()
        department = (request.form.get("department") or "").strip()
        designation = (request.form.get("designation") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        date_of_joining = (request.form.get("date_of_joining") or "").strip()
        status = (request.form.get("status") or "Active").strip()
        salary_raw = request.form.get("salary") or "0"

        try:
            salary = float(salary_raw)
        except ValueError:
            salary = 0.0

        if not emp_code or not name:
            flash("Employee Code and Name are required.", "error")
        else:
            existing = Employee.query.filter_by(emp_code=emp_code).first()
            if existing:
                flash("An employee with this code already exists.", "error")
            else:
                employee = Employee(
                    emp_code=emp_code,
                    name=name,
                    department=department,
                    designation=designation,
                    email=email,
                    phone=phone,
                    date_of_joining=date_of_joining,
                    status=status,
                    salary=salary
                )
                db.session.add(employee)
                db.session.commit()
                flash("Employee added.", "success")

        return redirect(url_for("employees_page"))

    q = (request.args.get("q") or "").strip()

    if q:
        pattern = f"%{q}%"
        employees = Employee.query.filter(
            (Employee.name.ilike(pattern)) | (Employee.emp_code.ilike(pattern))
        ).order_by(Employee.id.desc()).all()
    else:
        employees = Employee.query.order_by(Employee.id.desc()).all()

    return render_template(
        "employees.html",
        page_title="Employees",
        employees=employees,
        search_query=q
    )


@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance_page():
    # Add new attendance (from New Entry modal)
    if request.method == "POST":
        employee_id_raw = request.form.get("employee_id") or ""
        date_str = (request.form.get("date") or "").strip()
        check_in_str = (request.form.get("check_in") or "").strip()
        check_out_str = (request.form.get("check_out") or "").strip()
        status = (request.form.get("status") or "Present").strip()
        remarks = (request.form.get("remarks") or "").strip()

        try:
            employee_id = int(employee_id_raw)
        except ValueError:
            employee_id = 0

        if not employee_id or not date_str:
            flash("Employee and Date are required.", "error")
        else:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                d = None

            if not d:
                flash("Invalid date.", "error")
            else:
                existing = Attendance.query.filter_by(employee_id=employee_id, date=d).first()
                if existing:
                    flash("Attendance for this employee and date already exists.", "error")
                else:
                    ci = parse_time_or_none(check_in_str)
                    co = parse_time_or_none(check_out_str)
                    rec = Attendance(
                        employee_id=employee_id,
                        date=d,
                        check_in=ci,
                        check_out=co,
                        status=status,
                        remarks=remarks
                    )
                    db.session.add(rec)
                    db.session.commit()
                    flash("Attendance record added.", "success")

        return redirect(url_for("attendance_page"))

    # ---------- GET: monthly overview + optional detail modal ----------
    today = date.today()
    month_raw = request.args.get("month")
    year_raw = request.args.get("year")
    employee_id_raw = request.args.get("employee_id")  # for detail modal

    try:
        month = int(month_raw) if month_raw else today.month
    except ValueError:
        month = today.month

    try:
        year = int(year_raw) if year_raw else today.year
    except ValueError:
        year = today.year

    # Month range
    start_date = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    end_date = next_month - timedelta(days=1)

    employees = Employee.query.order_by(Employee.name).all()

    # Monthly overview (days recorded per employee)
    overview = []
    for emp in employees:
        days_recorded = Attendance.query.filter(
            Attendance.employee_id == emp.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).count()
        overview.append({
            "employee": emp,
            "days_recorded": days_recorded
        })

    month_names = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    # ---- Detail modal data (1 year at a time) ----
    selected_employee = None
    record_rows = []
    available_years = []

    if employee_id_raw:
        try:
            employee_id = int(employee_id_raw)
        except ValueError:
            employee_id = 0

        if employee_id:
            selected_employee = Employee.query.get(employee_id)

            if selected_employee:
                # For detailed view we use the same `year` param (1 year at a time)
                year_start = date(year, 1, 1)
                year_end = date(year, 12, 31)

                records = Attendance.query.filter(
                    Attendance.employee_id == employee_id,
                    Attendance.date >= year_start,
                    Attendance.date <= year_end
                ).order_by(Attendance.date.asc()).all()

                for rec in records:
                    hours = None
                    if rec.check_in and rec.check_out:
                        dt_in = datetime.combine(rec.date, rec.check_in)
                        dt_out = datetime.combine(rec.date, rec.check_out)
                        delta = dt_out - dt_in
                        hours = round(delta.total_seconds() / 3600.0, 2)
                    record_rows.append({"rec": rec, "hours": hours})

                # Available years in which this employee has attendance
                year_rows = db.session.query(
                    db.func.strftime("%Y", Attendance.date)
                ).filter(
                    Attendance.employee_id == employee_id
                ).distinct().all()

                available_years = sorted({int(y[0]) for y in year_rows if y[0] is not None}) or [year]

    return render_template(
        "attendance.html",
        page_title="Attendance",
        overview=overview,
        employees=employees,   # needed for New Entry modal
        month=month,
        year=year,
        month_names=month_names,
        selected_employee=selected_employee,
        record_rows=record_rows,
        available_years=available_years
    )


@app.route("/attendance/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_attendance_record(record_id):
    record = Attendance.query.get(record_id)
    if not record:
        flash("Attendance record not found.", "error")
        return redirect(url_for("attendance_page"))

    employee_id = record.employee_id
    month = record.date.month
    year = record.date.year

    db.session.delete(record)
    db.session.commit()
    flash("Attendance entry deleted.", "success")

    return redirect(url_for("attendance_page",
                            month=month,
                            year=year,
                            employee_id=employee_id))


@app.route("/payroll")
@login_required
def payroll_page():
    today = date.today()
    month_raw = request.args.get("month")
    year_raw = request.args.get("year")
    employee_id_raw = request.args.get("employee_id")

    try:
        month = int(month_raw) if month_raw else today.month
    except ValueError:
        month = today.month

    try:
        year = int(year_raw) if year_raw else today.year
    except ValueError:
        year = today.year

    employees = Employee.query.order_by(Employee.name).all()

    rows = []
    for emp in employees:
        rows.append(compute_payroll_for_employee(emp, month, year))

    # Detail modal data (when clicking one employee)
    selected_row = None
    if employee_id_raw:
        try:
            eid = int(employee_id_raw)
        except ValueError:
            eid = 0
        if eid:
            emp = Employee.query.get(eid)
            if emp:
                selected_row = compute_payroll_for_employee(emp, month, year)

    month_names = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    return render_template(
        "payroll.html",
        page_title="Payroll",
        rows=rows,
        month=month,
        year=year,
        month_names=month_names,
        selected_row=selected_row
    )


@app.route("/usage-report")
@login_required
def usage_report():
    rows, total = get_module_usage()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Module", "Records", "Percentage of total", "Generated on"])
    today_str = date.today().strftime("%Y-%m-%d")

    for r in rows:
        writer.writerow([r["name"], r["records"], f'{r["percentage"]}%', today_str])

    csv_data = output.getvalue()
    filename = f"module_usage_{date.today().strftime('%Y%m%d')}.csv"

    resp = Response(csv_data, mimetype="text/csv")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


if __name__ == "__main__":
    with app.app_context():
        create_tables()
    app.run(debug=True)