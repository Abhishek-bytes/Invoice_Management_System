import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///invoices.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    
    # Check if we need to migrate existing data
    try:
        # Try to query for the old column to see if migration is needed
        result = db.session.execute(db.text("PRAGMA table_info(company)"))
        columns = [row[1] for row in result.fetchall()]
        
        # If old columns exist, we need to migrate
        if 'zip_code' in columns and 'pin_code' not in columns:
            logging.info("Migrating database schema...")
            
            # Drop existing tables to recreate with new schema
            db.drop_all()
            db.create_all()
            logging.info("Database migration completed")
        else:
            db.create_all()
    except Exception as e:
        logging.error(f"Database migration error: {e}")
        # If there's an error, just recreate everything
        db.drop_all()
        db.create_all()

# Import routes
import routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
