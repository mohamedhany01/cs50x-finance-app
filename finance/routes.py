import os

from finance import app

from flask import flash, redirect, render_template, request, session
from flask.helpers import url_for

from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

from finance.helpers import apology, formatted, login_required, lookup, enough_money, usd, campany_exist_in_db, record_history

from finance.forms import LoginForm, RegistrationForm, LoginForm, QuoteForm, BuyForm, SellForm

from finance.models import User, Purchase, database

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filters
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["formatted"] = formatted


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
    
# Index/Home Page Logic
@app.route("/")
@login_required
def index():
    
    # Get all info of the logged in user
    user = User.query.filter_by(id=session.get("USER_ID")).first()

    # Get all purchases info of the logged in user
    user_purchases = user.purchases

    # Get user cash
    available_cash = float(user.cash)

    total_cash = 0
    if user_purchases:
        for purchase in user_purchases:
            total_cash = float(total_cash + float(purchase.total)) 
        total_cash = float(total_cash + available_cash)
    else:
        total_cash = available_cash

    return render_template("index.html", available_cash=available_cash, total_cash=total_cash, user_purchases=user_purchases)

# Quote Page Logic
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    form = QuoteForm()

    if request.method == "POST":

        if form.validate_on_submit():

            query_value = request.form.get("quote").strip().lower()

            query_result = lookup(query_value)

            if query_result:
                return render_template("quote.html", form=form, query_result=query_result)
            else:
                flash(f"{query_value} doesn't exit", "danger")

                return render_template("quote.html", form=form)

    return render_template("quote.html", form=form)

# Logout Page Logic
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    
# Buy Page Logic
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    form = BuyForm()

    if request.method == "POST":

        if form.validate_on_submit():

            company = request.form.get("company").strip().lower()
            shares = int(request.form.get("shares"))

            query_result = lookup(company)

            if query_result:

                user = User.query.filter_by(id=session.get("USER_ID")).first()

                user_cash = float(user.cash)

                shares_total_price = shares * float(query_result["price"])

                if enough_money(user_amount=user_cash, shares_amount=shares_total_price):
                    
                    # If the campany already exist, update it
                    if campany_exist_in_db(user.id, company):
                        
                        existed_company =  None
                        
                        for com in user.purchases:
                            if com.symbol.lower() == company:
                                existed_company = com

                        print(existed_company)
                        existed_company.shares   = int(existed_company.shares) + shares
                        existed_company.price    =  query_result["price"]
                        existed_company.total    =  float(existed_company.total) + (query_result["price"] * shares)
                        database.session.commit()

                        # Add modifications to the history
                        data = {}
                        data["symbol"]  = query_result["symbol"]
                        data["price"]   = query_result["price"]
                        data["shares"]  = shares
                        data["user_id"] = user.id
                        record_history(data)
                    else:
                        # Add a new purchase to database 
                        new_purchase = Purchase(
                            name=query_result["name"], 
                            symbol=query_result["symbol"], 
                            price=query_result["price"], 
                            shares=shares,
                            total=shares_total_price,
                            user_id=user.id
                        )
                        database.session.add(new_purchase)
                        database.session.commit()

                        # Add to the history
                        data = {}
                        data["symbol"]  = query_result["symbol"]
                        data["price"]   = query_result["price"]
                        data["shares"]  = shares
                        data["user_id"] = user.id
                        record_history(data)

                    # Modify user cash balance
                    user.cash = float(user.cash - shares_total_price)
                    database.session.commit()

                    flash("A successful bought process", "success")

                    # Redirect to home page 
                    return redirect(url_for("index"))
                    
                else:

                    flash("Your cash isn't enough", "danger")

                    return render_template("buy.html", form=form)
            else:
                flash(f"{company} isn't exit", "danger")

                return render_template("buy.html", form=form)

    return render_template("buy.html", form=form)

# Sell Page Logic
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    form = SellForm()

    # Get all info of the logged in user
    user = User.query.filter_by(id=session.get("USER_ID")).first()

    # Get all purchases info of the logged in user
    user_purchases = user.purchases

    # Collect (id, symbol)pairs
    pairs = []
    for purchase in user_purchases:
        pairs.append((purchase.symbol.lower(), purchase.symbol))

    # Add pairs to the dropdown menu
    form.symbol.choices = pairs

    # POST Request
    if request.method == "POST":

        if form.validate_on_submit():

            form_stock_symbol = request.form.get("symbol").upper() # Must be upper to compare it with database matches
            form_shares = int(request.form.get("shares"))

            # Query about if the user has this stock "symbol" in his table or not
            """ SELECT purchase.symbol AS purchase_symbol FROM purchase WHERE purchase.symbol = ? AND purchase.user_id = ? """
            stock_query = database.session.query(Purchase.symbol).filter(
                Purchase.symbol == form_stock_symbol, 
                Purchase.user_id == session.get("USER_ID")
            )
            
            # Query about if the user has this count of shares in his table or not
            """ SELECT purchase.shares AS purchase_shares FROM purchase WHERE purchase.symbol = ? AND purchase.user_id = ? """
            shares_query = database.session.query(Purchase.shares).filter(
                Purchase.symbol == form_stock_symbol, 
                Purchase.user_id == session.get("USER_ID")
            )
            
            symbol_the_user_has         = str(stock_query.first()[0]).upper()
            shares_counts_the_user_has  = int(shares_query.first()[0])

            # If the user really has this stock name "symbol" in his table or not
            if  symbol_the_user_has == form_stock_symbol:

                # If the user really has enough shares to sell in his table or not
                if (shares_counts_the_user_has > 0 and form_shares > 0) and shares_counts_the_user_has >= form_shares:
                    
                    # Lookup for new api data
                    query_result = lookup(form_stock_symbol)

                    if query_result:
                        
                        user = database.session.query(User).filter(
                            User.id == int(session.get("USER_ID")), 
                        ).one()

                        new_stock_price         = float(query_result["price"])
                        new_user_total_price    = float(new_stock_price * form_shares)

                        # Query about current user's purchase with the symbol that was chosen by the user before
                        """
                            SELECT purchase.id AS purchase_id, purchase.name AS purchase_name, 
                            purchase.symbol AS purchase_symbol, purchase.price AS purchase_price, 
                            purchase.shares AS purchase_shares, purchase.total AS purchase_total, 
                            purchase.user_id AS purchase_user_id FROM purchase WHERE purchase.symbol = ? AND purchase.user_id = ?
                        """
                        new_user_purchase = database.session.query(Purchase).filter(
                            Purchase.symbol == form_stock_symbol, 
                            Purchase.user_id == session.get("USER_ID")
                        ).one()

                        new_user_purchase.price     =  new_stock_price
                        new_user_purchase.total     = float(abs(int(new_user_purchase.shares) - form_shares) * new_stock_price)
                        new_user_purchase.shares    = abs(int(new_user_purchase.shares) - form_shares)
                        user.cash                   = float(user.cash) + new_user_total_price
                        database.session.commit()

                        # Remove a purchase in case it's reached to "Zero" shares
                        if int(new_user_purchase.shares) <= 0:
                            print(new_user_purchase.symbol, " Removed < ZERO")
                            database.session.delete(new_user_purchase)
                            database.session.commit()
                            
                        # Populate user's history with new data
                        # Add modifications to the history
                        data = {}
                        data["symbol"]  = query_result["symbol"]
                        data["price"]   = query_result["price"]
                        data["shares"]  = -form_shares
                        data["user_id"] = user.id
                        record_history(data)
                        
                        flash("A successful selling process", "success")

                        # Redirect to home page 
                        return redirect(url_for("index"))
                    else:

                        flash("Error in retriveing data", "danger")

                        return render_template("sell.html", form=form, user_purchases=user_purchases)
                else:

                    flash("You don't have enough shares", "danger")

                    return render_template("sell.html", form=form, user_purchases=user_purchases)
            else:

                flash("You don't have this stock", "danger")

                return render_template("sell.html", form=form, user_purchases=user_purchases)

        else:
            return render_template("sell.html", form=form, user_purchases=user_purchases)

    # GET Request
    return render_template("sell.html", form=form, user_purchases=user_purchases)

# History Page Logic
@app.route("/history")
@login_required
def history():

    # Get all info of the logged in user
    user = User.query.filter_by(id=session.get("USER_ID")).first()

    # Get history info of the logged in user
    user_history = user.history

    return render_template("history.html", user_history=user_history)

# Login Page Logic
@app.route("/login", methods=["GET", "POST"])
def login():

    # Login form for the forms.py
    form = LoginForm()

    # In POST request, validate the form
    if request.method == "POST":

        # If all data are valid
        if form.validate_on_submit():

            # Get form username and check if is exist or not
            user_in_db = User.query.filter_by(username=request.form.get("username")).all()

            if user_in_db:

                if check_password_hash(user_in_db[0].hashed, request.form.get("password")):

                    session["USER_ID"] = user_in_db[0].id

                    flash(f"Welcome, {user_in_db[0].username}", category="success")

                    return redirect(url_for("index"))
                else:

                    flash("A Failure Login: Check your username/password", category="danger")

                    return render_template("login.html", form=form)

            else:

                flash("A Failure Login: This user doesn't exist", category="danger")

                return render_template("login.html", form=form)
        else:

            return render_template("login.html", form=form)

    return render_template("login.html", form=form)

# Register Page Logic
@app.route("/register", methods=["GET", "POST"])
def register():

    # Registration form for the forms.py
    form = RegistrationForm()

    # In POST request, validate the form
    if request.method == "POST":

        if form.validate_on_submit():

            # Add the user to the db
            new_valid_user = User(
                username=request.form.get("username").strip(), 
                email=request.form.get("email").strip(), 
                hashed=generate_password_hash(request.form.get("password"))
            )
            database.session.add(new_valid_user)
            database.session.commit()

            # Show data on the console
            print(new_valid_user)

            flash("A Successful Registration", category="success")

            return redirect(url_for("index"))
        else:
            flash("A Failure Registration", category="danger")

            return render_template("register.html", form=form)
    # In GET request
    return render_template("register.html", form=form)
    

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)