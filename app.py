from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from models import db, User, Category, Expense, Income
from config import Config
import csv
from io import StringIO

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def setup_default_categories():
    default = [
        {"name": "Food", "color": "#FFB347", "icon": "🍔"},
        {"name": "Transport", "color": "#B0E0E6", "icon": "🚌"},
        {"name": "Entertainment", "color": "#FFD700", "icon": "🎮"},
        {"name": "Health", "color": "#98FB98", "icon": "💊"},
        {"name": "Utilities", "color": "#87CEEB", "icon": "💡"},
        {"name": "Shopping", "color": "#FF69B4", "icon": "🛒"},
        {"name": "Other", "color": "#CCCCCC", "icon": "🔖"},
    ]
    if Category.query.count() == 0:
        for cat in default:
            category = Category(name=cat["name"], color=cat["color"], icon=cat["icon"])
            db.session.add(category)
        db.session.commit()

with app.app_context():
    setup_default_categories()

def get_expenses_q():
    if current_user.is_authenticated:
        return Expense.query.filter_by(user_id=current_user.id)
    else:
        eids = session.get("guest_expense_ids") or []
        return Expense.query.filter(Expense.id.in_(eids)) if eids else Expense.query.filter_by(id=None)

def get_incomes_q():
    if current_user.is_authenticated:
        return Income.query.filter_by(user_id=current_user.id)
    else:
        iids = session.get("guest_income_ids") or []
        return Income.query.filter(Income.id.in_(iids)) if iids else Income.query.filter_by(id=None)

@app.route("/", methods=["GET"])
def index():
    categories = Category.query.all()
    q_exp = get_expenses_q()
    q_inc = get_incomes_q()
    expenses = q_exp.order_by(Expense.date.desc()).limit(10).all()
    incomes = q_inc.order_by(Income.date.desc()).limit(10).all()
    today = date.today()
    start_month = today.replace(day=1)
    start_week = today - timedelta(days=today.weekday())
    total_exp_month = sum(e.amount for e in q_exp.filter(Expense.date >= start_month).all())
    total_inc_month = sum(i.amount for i in q_inc.filter(Income.date >= start_month).all())
    total_today = sum(e.amount for e in q_exp.filter(Expense.date == today).all())
    total_week = sum(e.amount for e in q_exp.filter(Expense.date >= start_week).all())
    user_budget = current_user.monthly_budget if current_user.is_authenticated else 0
    cat_totals = {cat.name: sum(e.amount for e in q_exp.filter_by(category_id=cat.id).all()) for cat in categories}
    max_cat_name = max(cat_totals, key=lambda k: cat_totals[k]) if cat_totals else ""
    max_cat_amt = cat_totals.get(max_cat_name, 0)
    stats = {
        "today": total_today,
        "week": total_week,
        "month": total_exp_month,
        "income": total_inc_month,
        "budget": user_budget,
        "max_cat_name": max_cat_name,
        "max_cat_amt": max_cat_amt
    }
    alert_budget = user_budget > 0 and total_exp_month >= 0.9 * user_budget
    trend_labels, trend_data = [], []
    for d in range(0, 30):
        day = start_month + timedelta(days=d)
        if day > today: break
        amt = sum(e.amount for e in q_exp.filter(Expense.date == day).all())
        trend_labels.append(day.strftime('%Y-%m-%d'))
        trend_data.append(amt)

    # Prepare category data for charts
    category_chart_data = []
    for cat in categories:
        total = sum(e.amount for e in q_exp.filter(Expense.category_id==cat.id).all())
        if total > 0:
            category_chart_data.append({'name': cat.name, 'icon': cat.icon, 'color': cat.color, 'total': float(total)})
    theme = current_user.theme if current_user.is_authenticated else "default"
    show_onboarding = not current_user.is_authenticated and not session.get("onboarded")
    session["onboarded"] = True
    return render_template("index.html",
        categories=categories,
        category_chart_data=category_chart_data,
        expenses=expenses,
        incomes=incomes,
        total_month=total_exp_month,
        cat_totals=cat_totals or {},
        stats=stats,
        trend_labels=trend_labels or [],
        trend_data=trend_data or [],
        theme=theme,
        alert_budget=alert_budget,
        show_onboarding=show_onboarding
    )

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    categories = Category.query.all()
    if request.method == "POST":
        amount = float(request.form["amount"])
        description = request.form["description"]
        category_id = int(request.form["category"])
        date_str = request.form["date"]
        expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        tags = request.form.get("tags", "")
        currency = request.form.get("currency", "INR")
        expense = Expense(amount=amount, description=description, category_id=category_id,
                          date=expense_date, tags=tags, currency=currency)
        if current_user.is_authenticated:
            expense.user_id = current_user.id
            db.session.add(expense)
            db.session.commit()
        else:
            db.session.add(expense)
            db.session.commit()
            eids = session.get("guest_expense_ids", [])
            eids.append(expense.id)
            session["guest_expense_ids"] = eids
        flash("Expense added successfully!", "success")
        return redirect(url_for("index"))
    return render_template("add_expense.html", categories=categories, now=datetime.now)

# ... Part 2 will start from here ...
@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    categories = Category.query.all()
    expense = Expense.query.get_or_404(expense_id)
    allow_edit = (current_user.is_authenticated and expense.user_id == current_user.id) or (
        not current_user.is_authenticated and expense.id in (session.get("guest_expense_ids") or []))
    if not allow_edit:
        flash("Unauthorized", "danger")
        return redirect(url_for("expenses"))
    if request.method == "POST":
        expense.amount = float(request.form["amount"])
        expense.description = request.form["description"]
        expense.category_id = int(request.form["category"])
        date_str = request.form["date"]
        expense.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        expense.tags = request.form.get("tags", "")
        expense.currency = request.form.get("currency", "INR")
        db.session.commit()
        flash("Expense updated!", "success")
        return redirect(url_for("expenses"))
    return render_template("edit_expense.html", categories=categories, expense=expense)

@app.route("/expenses")
def expenses():
    categories = Category.query.all()
    q = get_expenses_q()
    expenses = q.order_by(Expense.date.desc()).all()
    return render_template("expenses.html", expenses=expenses, categories=categories)

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    allow_delete = (current_user.is_authenticated and expense.user_id == current_user.id) or (
        not current_user.is_authenticated and expense.id in (session.get("guest_expense_ids") or []))
    if not allow_delete:
        flash("Unauthorized", "danger")
        return redirect(url_for("expenses"))
    db.session.delete(expense)
    db.session.commit()
    if not current_user.is_authenticated:
        eids = session.get("guest_expense_ids", [])
        eids = [eid for eid in eids if eid != expense.id]
        session["guest_expense_ids"] = eids
    flash("Expense deleted!", "info")
    return redirect(url_for("expenses"))

@app.route("/search", methods=["GET"])
def search():
    category_id = request.args.get("category")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = get_expenses_q()
    if category_id:
        q = q.filter_by(category_id=category_id)
    if date_from:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        q = q.filter(Expense.date >= dt_from)
    if date_to:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        q = q.filter(Expense.date <= dt_to)
    results = q.order_by(Expense.date.desc()).all()
    categories = Category.query.all()
    return render_template("expenses.html", expenses=results, categories=categories)

@app.route("/suggest_descriptions")
def suggest_descriptions():
    q = request.args.get('q', '')
    suggestions = []
    base_q = get_expenses_q()
    if q:
        results = base_q.filter(Expense.description.ilike(f"%{q}%")).distinct(Expense.description).limit(5).all()
        suggestions = list({e.description for e in results if e.description.lower().startswith(q.lower())})
    return jsonify(suggestions)

@app.route("/export_expenses")
def export_expenses():
    category_id = request.args.get("category")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = get_expenses_q()
    if category_id:
        q = q.filter_by(category_id=category_id)
    if date_from:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        q = q.filter(Expense.date >= dt_from)
    if date_to:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        q = q.filter(Expense.date <= dt_to)
    expenses = q.order_by(Expense.date.desc()).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Category", "Description", "Amount", "Tags", "Currency"])
    categories_dict = {cat.id: cat for cat in Category.query.all()}
    for e in expenses:
        cat = categories_dict.get(e.category_id)
        writer.writerow([
            e.date.strftime('%Y-%m-%d'),
            cat.name if cat else "",
            e.description,
            e.amount,
            e.tags,
            e.currency
        ])
    output = si.getvalue()
    response = Response(output, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    return response

@app.route("/print_report")
def print_report():
    category_id = request.args.get("category")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    q = get_expenses_q()
    if category_id:
        q = q.filter_by(category_id=category_id)
    if date_from:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        q = q.filter(Expense.date >= dt_from)
    if date_to:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        q = q.filter(Expense.date <= dt_to)
    expenses = q.order_by(Expense.date.asc()).all()
    categories = Category.query.all()
    total = sum(e.amount for e in expenses)
    now = datetime.now
    return render_template("print_report.html", expenses=expenses, categories=categories, total=total, now=now)

@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        name = request.form["name"]
        color = request.form["color"]
        icon = request.form["icon"]
        budget = float(request.form.get("budget", 0))
        if name and color and icon:
            cat = Category(name=name, color=color, icon=icon, budget=budget)
            db.session.add(cat)
            db.session.commit()
            flash("Category added!", "success")
            return redirect(url_for("expenses"))
        flash("All fields required.", "danger")
    return render_template("add_category.html")

# --- INCOME CRUD, safe int input ---
@app.route("/add_income", methods=["GET", "POST"])
def add_income():
    categories = Category.query.all()
    if request.method == "POST":
        amount = float(request.form["amount"])
        source = request.form["source"]
        cat_val = request.form.get("category", "")
        category_id = int(cat_val) if cat_val.isdigit() else None
        date_str = request.form["date"]
        income_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        recurring = bool(request.form.get("recurring", False))
        interval = request.form.get("interval", "monthly")
        currency = request.form.get("currency", "INR")
        tags = request.form.get("tags", "")
        income = Income(amount=amount, source=source, date=income_date,
                        recurring=recurring, interval=interval, category_id=category_id,
                        currency=currency, tags=tags)
        if current_user.is_authenticated:
            income.user_id = current_user.id
            db.session.add(income)
            db.session.commit()
        else:
            db.session.add(income)
            db.session.commit()
            iids = session.get("guest_income_ids", [])
            iids.append(income.id)
            session["guest_income_ids"] = iids
        flash("Income added successfully!", "success")
        return redirect(url_for("index"))
    return render_template("add_income.html", categories=categories, now=datetime.now)

# --- More routes: profile, help, accessibility, 404, authentication as before.
# ... (keep your previous code for profile, help, accessibility, signup, login, logout) ...
# --- User profile, theme, accessibility, help, error pages ---
@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        budget = float(request.form.get("monthly_budget", 0))
        current_user.monthly_budget = budget
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html")

@app.route("/set_theme")
@login_required
def set_theme():
    theme = request.args.get("theme", "default")
    current_user.theme = theme
    db.session.commit()
    return ("",204)

@app.route("/accessibility")
def accessibility():
    return render_template("accessibility.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --- Authentication (signup, login, logout) ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username & Password required.", "danger")
            return render_template("signup.html")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template("signup.html")
        u = User(username=username, password=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash("Account created and signed in!", "success")
        return redirect(url_for("index"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            guest_ids = session.get("guest_expense_ids", [])
            for eid in guest_ids:
                exp = Expense.query.get(eid)
                if exp and not exp.user_id:
                    exp.user_id = user.id
            guest_iids = session.get("guest_income_ids", [])
            for iid in guest_iids:
                inc = Income.query.get(iid)
                if inc and not inc.user_id:
                    inc.user_id = user.id
            db.session.commit()
            session.pop("guest_expense_ids", None)
            session.pop("guest_income_ids", None)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)