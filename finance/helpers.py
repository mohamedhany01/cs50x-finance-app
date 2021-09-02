import os

import requests
import urllib.parse

from flask import redirect, render_template, session
from functools import wraps
from finance.models import User, History, database

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("USER_ID") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

# A utilities functions
def formatted(unformatted_date):
    """Format utc date"""
    return unformatted_date.strftime("%Y-%m-%d %H:%M:%S")


def enough_money(user_amount, shares_amount):

    if user_amount < shares_amount:
        return False
        
    return True

"""Moving it to helpers.py will cause a circular import problem"""
def campany_exist_in_db(user_id, co):

    companies = User.query.get(user_id).purchases
    
    for i in range(len(companies)):
        if co == companies[i].symbol.lower():
            return True

    return False

"""Moving it to helpers.py will cause a circular import problem"""
def record_history(data_to_recorded):

    new_history = History(
        symbol=data_to_recorded["symbol"], 
	    price=data_to_recorded["price"], 
	    shares=data_to_recorded["shares"], 
	    user_id=data_to_recorded["user_id"], 
    )
    database.session.add(new_history)
    database.session.commit()