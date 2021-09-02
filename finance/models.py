from finance import database
from datetime import datetime

# Database classes
class User(database.Model):
    id          = database.Column(database.Integer, primary_key=True)
    username    = database.Column(database.String(30), unique=True, nullable=False)
    email       = database.Column(database.String(50), unique=True, nullable=False)
    hashed      = database.Column(database.String(100), nullable=False)
    cash        = database.Column(database.Float, nullable=False, default=10000.0) # Each user satart with fixed amount of cash
    
    # One-to-Many relationship with the History, Purchase tables
    history     = database.relationship('History', backref='user', lazy=True)
    purchases   = database.relationship('Purchase', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.cash}')"

class Purchase(database.Model):
    id          = database.Column(database.Integer, primary_key=True)
    name        = database.Column(database.String(50), nullable=False)
    symbol      = database.Column(database.String(6), nullable=False)
    price       = database.Column(database.Float, nullable=False)
    shares      = database.Column(database.Integer, nullable=False)
    total       = database.Column(database.Float, nullable=False)

    # A User's table reference
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Purchase('{self.name}', '{self.symbol}', '{self.price}', '{self.shares}', '{self.total}')"

class History(database.Model):
    id              = database.Column(database.Integer, primary_key=True)
    symbol          = database.Column(database.String(6), nullable=False)
    price           = database.Column(database.Float, nullable=False)
    shares          = database.Column(database.Integer, nullable=False)
    transacted      = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)

    # A User's table reference
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"History('{self.symbol}', '{self.price}', '{self.shares}', '{self.transacted}')"