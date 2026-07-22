# ============================================================
# models.py
# Defines the database tables as Python classes (ORM models).
# Each class = one table. Each attribute = one column.
# SQLAlchemy translates these into SQL CREATE TABLE statements.
# ============================================================

from database import db
from datetime import datetime


class Account(db.Model):
    """Represents the `accounts` table. Stores consumer and merchant accounts."""

    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    # type is either "consumer" or "merchant"
    type = db.Column(db.String(20), nullable=False)
    # Decimal(15,2) stores money precisely (avoids floating point errors)
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)

    def masked_account_number(self):
        """Returns account number with all but last 4 digits masked. e.g. ••••7890"""
        return "••••" + self.account_number[-4:]

    def __repr__(self):
        return f"<Account {self.name}>"


class Transaction(db.Model):
    """Represents the `transactions` table. Records every completed payment."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    # order_id comes from the Ecommerce application
    order_id = db.Column(db.String(50), nullable=False)
    # Account numbers (not IDs) so the record is human-readable
    from_account = db.Column(db.String(20), nullable=False)
    to_account = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    reference_number = db.Column(db.String(20), unique=True, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.reference_number}>"
