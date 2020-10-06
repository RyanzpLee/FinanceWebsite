import os
import re
from datetime import datetime
import sys
import sqlalchemy

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
# db = SQL("postgres://auufjngqybuokd:5d121905793f26e9ed88953b938ee03cba373b2f36aab9d0880099a10294d44c@ec2-52-31-94-195.eu-west-1.compute.amazonaws.com:5432/d349o1q6jjhetr")

# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    # Current user session id
    user = session.get("user_id")

    #  Select all shares for the user
    rows = db.execute(
        "SELECT symbol, name, shares FROM users_shares WHERE user_id = ?", (user))
    
    
    # Select the user's current cash
    funds = db.execute("SELECT cash FROM users WHERE id = ?", (user))
    price = {}
    total = {}
    grand_total = 0
    # For each share symbol, look up info, and calculate the price and total
    for row in rows:
        info = lookup(row["symbol"])
        price[row["symbol"]] = usd(info["price"])
        total[row["symbol"]] = usd(info["price"] * row["shares"])
        grand_total += info["price"] * row["shares"]

    grand_total  += float(funds[0]['cash']) 
    return render_template("index.html", rows=rows, price=price, funds=usd(funds[0]['cash']), total=total, grand_total=usd(grand_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        info = lookup(symbol)

        total = info["price"] * float(amount)
        user = session.get("user_id")

        if not symbol or not lookup(symbol):
            return apology("Stock symbol is empty or does not exist", 403)
        if not amount or int(amount) < 0:
            return apology("Must enter positive integer", 403)

        cash = db.execute("SELECT cash FROM users WHERE id = ?", user)

        if cash[0]["cash"] > total:
            # Store purchase history in purchases table
            db.execute(
                "INSERT INTO transactions (user_id, symbol, shares, share_price, value) VALUES (?,?,?,?,?)", (user, info["symbol"], amount, info["price"], total))

            # Update users_shares with new purchase
            if db.execute("SELECT * FROM users_shares WHERE user_id = ? and symbol = ?", (user, info["symbol"])):
                db.execute(
                    "UPDATE users_shares SET shares = shares + ? WHERE user_id = ? and symbol = ?", (amount, user, info["symbol"]))
            else:
                db.execute(
                    "INSERT INTO users_shares (user_id, symbol, name, shares) VALUES (?,?,?,?)", (user, info["symbol"], info["name"], amount))

            # Update user cash
            db.execute("UPDATE users SET cash = ? WHERE id = ?", (cash[0]["cash"] - total, user))

        elif not cash or cash[0]["cash"] < total:
            return apology("Sorry, you do not have enough money", 403)
        
        flash("You have successfully bought shares")
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user = session.get("user_id")
    
    rows = db.execute("SELECT symbol, date_purchased, shares, share_price, value FROM transactions WHERE user_id = ? ORDER BY date_purchased", (user))
    return render_template("history.html", rows=rows)

@app.route("/account")
@login_required
def account():
    
    return render_template("account.html")

@app.route("/change_pwd", methods=["GET", "POST"])
@login_required
def change_pwd():
    user = session.get("user_id")
    
    if request.method == "POST":
        old_pwd = request.form.get("old_pwd")
        new_pwd = request.form.get("new_pwd")
        confirmation = request.form.get("confirmation")
        pwd_hash = db.execute("SELECT hash FROM users WHERE id= ?", (user))
        
        if not password_requirements(new_pwd):
            return apology("New password does not meet requirements")

        
        if check_password_hash(pwd_hash[0]['hash'],old_pwd) and new_pwd == confirmation:
            new_pwd_hash = generate_password_hash(new_pwd)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", (new_pwd_hash, user))
            flash("Password Changed")
            return redirect("/")
        else:
            return apology("You have not entered the correct password")   
            
        
    


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", (username=request.form.get("username")))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        info = lookup(symbol)
        return render_template("quoted.html", info=info)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        password_hash = generate_password_hash(password)
        check = True

        if not username:
            check = False
            return apology("Username cannot be blank", 403)
        if validate(username):
            check = False
            return apology("Username already exists", 403)

        if not password:
            check = False
            return apology("You must enter a password", 403)

        if not confirmation or confirmation != password:
            check = False
            return apology("Retype your password correctly", 403)

        if not password_requirements(password):
            check = False
            return apology("Password must be 8 characters long and contain uppercase, and lower case, and a digit from 0-9 and a special character",403)

        if check:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :password_hash)", ("username": username, "password_hash": password_hash))
            db.commit()

    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user = session.get("user_id")
    
    if request.method == "GET":
        rows = db.execute("SELECT symbol FROM users_shares WHERE user_id = ?", (user))
        return render_template("sell.html", rows=rows)
    else:
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        
        rows = db.execute("SELECT symbol FROM users_shares WHERE user_id = ?", (user))
        stock = db.execute("SELECT shares FROM users_shares WHERE symbol = ?", (symbol))
        
        if not symbol:
            return apology("You did not pick a stock, or you do not own any shares", 403)
        
        if not amount or int(amount) < 0 or int(amount) > int(stock[0]['shares']):
            return apology("You do not own that many shares", 403)
        
        info = lookup(symbol)
        
        total = float(info["price"]) * float(amount)
        
        db.execute("UPDATE users_shares SET shares = shares - ? WHERE user_id = ? and symbol = ?", (amount, user, info["symbol"]))
        db.execute("UPDATE users SET cash = cash + ? WHERE id= ?", (total, user))
        
        db.execute("INSERT INTO transactions (user_id, symbol, shares, share_price, value) VALUES (?,?,?,?,?)", (user, info["symbol"], int(amount) * -1, info["price"], total))
        
        db.commit()
        flash("You have sold your shares")
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Checks if username exists in database
def validate(username):
    check = db.execute("SELECT * FROM users WHERE username = :username", ("username": username))

    return True if check else False


# Checks the password string for the requirements
def password_requirements(pwd):
    special = [
        "$",
        "@",
        "!",
        "?",
        '"',
        "'",
        "#",
        "%",
        "^",
        "&",
        "*",
        "(",
        ")",
        "_",
        "-",
        "=",
        "+",
        "{",
        "}",
        "[",
        "]",
        ";",
        ":",
        ",",
        ".",
        "?",
        "/",
    ]
    val = True
    if len(pwd) < 8:
        val = False
    if not any(char.isdigit() for char in pwd):
        val = False
    if not any(char.isupper() for char in pwd):
        val = False
    if not any(char.islower() for char in pwd):
        val = False
    if not any(char in special for char in pwd):
        val = False
    if val:
        return True


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run()