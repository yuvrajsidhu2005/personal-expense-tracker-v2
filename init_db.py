from app import app, db
from models import Category

def init_database():
    with app.app_context():
        db.drop_all()      # This will drop ALL tables
        db.engine.execute('DROP TABLE IF EXISTS "user" CASCADE;')
        db.create_all()    # This will re-create them based on your models!
        print("✅ Database tables re-created!")

        default_categories = [
            {"name": "Food", "color": "#FFB347", "icon": "🍔"},
            {"name": "Transport", "color": "#B0E0E6", "icon": "🚌"},
            {"name": "Entertainment", "color": "#FFD700", "icon": "🎮"},
            {"name": "Health", "color": "#98FB98", "icon": "💊"},
            {"name": "Utilities", "color": "#87CEEB", "icon": "💡"},
            {"name": "Shopping", "color": "#FF69B4", "icon": "🛒"},
            {"name": "Other", "color": "#CCCCCC", "icon": "🔖"},
        ]

        for cat_data in default_categories:
            if not Category.query.filter_by(name=cat_data["name"]).first():
                category = Category(**cat_data)
                db.session.add(category)

        db.session.commit()
        print("✅ Default categories created!")

if __name__ == "__main__":
    init_database()
