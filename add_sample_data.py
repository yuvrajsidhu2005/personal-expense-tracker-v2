from app import app, db
from models import Expense, Income, Category, User
from datetime import date


def add_sample_data():
    with app.app_context():
        # Get the first user (or modify to get by ID)
        user = User.query.first()  # Gets the first user
        # OR if you know your user ID, use: user = User.query.get(1)
        
        if not user:
            print("❌ No user found! Please create an account first.")
            return
        
        print(f"📝 Adding data for user: {user.username} (ID: {user.id})")
        
        # Get categories
        food = Category.query.filter_by(name="Food").first()
        transport = Category.query.filter_by(name="Transport").first()
        entertainment = Category.query.filter_by(name="Entertainment").first()
        health = Category.query.filter_by(name="Health").first()
        utilities = Category.query.filter_by(name="Utilities").first()
        shopping = Category.query.filter_by(name="Shopping").first()
        
        # Sample expenses for November 1-5, 2025
        sample_expenses = [
            # November 1st
            Expense(amount=120, description="Breakfast at cafe", category_id=food.id, date=date(2025, 11, 1), tags="breakfast, cafe", user_id=user.id),
            Expense(amount=85, description="Uber to college", category_id=transport.id, date=date(2025, 11, 1), tags="transport, uber", user_id=user.id),
            Expense(amount=180, description="Lunch with friends", category_id=food.id, date=date(2025, 11, 1), tags="lunch, friends", user_id=user.id),
            Expense(amount=250, description="Movie ticket - latest release", category_id=entertainment.id, date=date(2025, 11, 1), tags="movie, entertainment", user_id=user.id),
            
            # November 2nd  
            Expense(amount=650, description="Weekly groceries", category_id=shopping.id, date=date(2025, 11, 2), tags="groceries, shopping", user_id=user.id),
            Expense(amount=320, description="Medical checkup", category_id=health.id, date=date(2025, 11, 2), tags="health, doctor", user_id=user.id),
            Expense(amount=480, description="Dinner at restaurant", category_id=food.id, date=date(2025, 11, 2), tags="dinner, restaurant", user_id=user.id),
            Expense(amount=150, description="Snacks and coffee", category_id=food.id, date=date(2025, 11, 2), tags="snacks, coffee", user_id=user.id),
            
            # November 3rd
            Expense(amount=199, description="Mobile recharge", category_id=utilities.id, date=date(2025, 11, 3), tags="mobile, recharge", user_id=user.id),
            Expense(amount=150, description="Coffee with friends", category_id=food.id, date=date(2025, 11, 3), tags="coffee, friends", user_id=user.id),
            Expense(amount=499, description="Gaming subscription", category_id=entertainment.id, date=date(2025, 11, 3), tags="gaming, subscription", user_id=user.id),
            Expense(amount=220, description="Brunch at cafe", category_id=food.id, date=date(2025, 11, 3), tags="brunch, cafe", user_id=user.id),
            
            # November 4th
            Expense(amount=100, description="Breakfast - dosa and chai", category_id=food.id, date=date(2025, 11, 4), tags="breakfast", user_id=user.id),
            Expense(amount=60, description="Auto rickshaw fare", category_id=transport.id, date=date(2025, 11, 4), tags="transport, auto", user_id=user.id),
            Expense(amount=280, description="Stationery and books", category_id=shopping.id, date=date(2025, 11, 4), tags="stationery, books", user_id=user.id),
            Expense(amount=140, description="Lunch - thali", category_id=food.id, date=date(2025, 11, 4), tags="lunch, thali", user_id=user.id),
            Expense(amount=95, description="Evening snacks", category_id=food.id, date=date(2025, 11, 4), tags="snacks", user_id=user.id),
            
            # November 5th (Today)
            Expense(amount=110, description="Breakfast - sandwich", category_id=food.id, date=date(2025, 11, 5), tags="breakfast", user_id=user.id),
            Expense(amount=75, description="Bus pass weekly", category_id=transport.id, date=date(2025, 11, 5), tags="transport, bus", user_id=user.id),
            Expense(amount=90, description="Afternoon snacks", category_id=food.id, date=date(2025, 11, 5), tags="snacks", user_id=user.id),
            Expense(amount=350, description="Online course subscription", category_id=entertainment.id, date=date(2025, 11, 5), tags="education, online", user_id=user.id),
        ]
        
        # Sample incomes
        sample_incomes = [
            Income(amount=5000, source="Freelance Project Payment", date=date(2025, 11, 1), tags="freelance, work", user_id=user.id),
            Income(amount=2000, source="Part-time job salary", date=date(2025, 11, 3), tags="salary, part-time", user_id=user.id),
        ]
        
        # Add all expenses and incomes
        for expense in sample_expenses:
            db.session.add(expense)
        
        for income in sample_incomes:
            db.session.add(income)
        
        db.session.commit()
        print("✅ Sample data added successfully!")
        print(f"Added {len(sample_expenses)} expenses and {len(sample_incomes)} incomes")
        
        # Print summary
        total_expenses = sum(e.amount for e in sample_expenses)
        total_income = sum(i.amount for i in sample_incomes)
        print(f"\n📊 Summary:")
        print(f"Total Expenses: ₹{total_expenses}")
        print(f"Total Income: ₹{total_income}")
        print(f"Balance: ₹{total_income - total_expenses}")


if __name__ == "__main__":
    add_sample_data()
