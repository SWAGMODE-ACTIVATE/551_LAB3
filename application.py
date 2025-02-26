import os
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

# Get database URL from environment variable
DATABASE_URL = "postgresql://postgres:poop@localhost/bookdb"
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
print('flask is starting')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        search = request.form.get("query")
        search = f"%{search}%"
        result_exists = db.execute(text("SELECT * FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search OR CAST(year AS TEXT) LIKE :search"), {"search": search}).fetchall()
        if result_exists:
            return render_template("search.html", username=session["username"], results="results found", books=result_exists)
        else:
            return render_template("search.html", username=session["username"], results="no results found.")
    if request.method == "GET":
        return render_template("search.html", username=session["username"])

if __name__ == "__main__":
    app.run(debug=True)