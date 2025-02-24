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


"""
turns out this is ORM so not using it.
class Book(db.Model):
    __tablename__="books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer, nullable = False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review = db.Column(db.String, nullable=False)

"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods =["POST"])
def login():
    username = request.form.get("usernamel")
    password = request.form.get("passwordl")
    existing_user = db.execute(text("SELECT * FROM users WHERE username = :username AND password = :password"), {"username": username, "password": password}).fetchone()
    if existing_user:
        session["username"] = username
        return render_template("search.html", username=session["username"])
    else:
        return render_template("index.html", message="username or password is incorrect.")
    
@app.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("usernamer")
    password = request.form.get("passwordr")
    existing_user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
    if existing_user:
        return render_template("index.html", message="username already exists.")
    else:
        db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), {"username": username, "password": password})
        db.commit()
        return render_template("index.html", message="account created, you can log in now.")

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

@app.route("/book/<int:book_id>", methods=["POST","GET"])
def bookpage(book_id):
    #Get GEMINI google api key from enviornment varibales
    gemini_key = os.environ["GEMINI_KEY"]

    #initialize book and get google api reviews
    book = db.execute(text("SELECT * FROM books WHERE id = :id"), {"id":book_id}).fetchone()
    isbn = book.isbn
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
    json = (res.json())
    #check if theres any ratings
    try:
        number_ratings = json["items"][0]["volumeInfo"]["ratingsCount"]
        average_rating = json["items"][0]["volumeInfo"]["averageRating"]
    except (KeyError, IndexError):
        number_ratings = "no ratings found on google books api."
        average_rating = "no ratings found on google books api."    

    try:
        bookapidesc = json["items"][0]["volumeInfo"]["description"]
    except (KeyError, IndexError):
        bookapidesc = "no description found on google books api."
 
    #gemini api fetch, the rawdata is pasted from lab page
    rawdata = {
        "contents": [{
            "parts": [
                {
                    "text": f"Summarize this text using less than 50 words: {bookapidesc}"
                }
            ]
        }]
    }
    gemini_res = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent", params={"key":gemini_key}, headers={"Content-Type":"application/json"}, json=rawdata)
    gemini_json = (gemini_res.json())
    gemini_json = gemini_json["candidates"][0]["content"]["parts"][0]["text"]
    
    if request.method == "GET":
        reviews = db.execute(text("SELECT * FROM reviews WHERE book_id = :id"), {"id":book_id}).fetchall()
        return render_template("bookpage.html", book=book, username=session["username"], reviews=reviews, average_rating=average_rating, number_ratings=number_ratings, gemini_json=gemini_json)
    if request.method == "POST":
        review = request.form.get("review")
        ratingnum = request.form.get("ratingnum")
        username = session["username"]
        
        #test if review by this user already exists, mostly same as testing for usernames when regitsering
        existing_review= db.execute(text("SELECT * FROM reviews WHERE book_id =:book_id AND username = :username"), {"book_id":book_id, "username":username}).fetchone()
        if existing_review:
            message = "you may only create one review per book on your account."
        else:
            db.execute(text("INSERT INTO reviews (book_id, username, review, rating) VALUES (:book_id, :username, :review, :rating)"), {"book_id":book_id, "username":username, "review":review, "rating":ratingnum})
            db.commit()
            message = "review added."

        reviews = db.execute(text("SELECT * FROM reviews WHERE book_id = :id"), {"id":book_id}).fetchall()
        return render_template("bookpage.html", book=book, username=session["username"], reviews=reviews, message=message, average_rating=average_rating, number_ratings=number_ratings, gemini_json=gemini_json)

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    #initialize book and get google api reviews
    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn":isbn}).fetchone()

    if book:
        #Get GEMINI google api key from enviornment varibales
        gemini_key = os.environ["GEMINI_KEY"]

        #rest of info needs google api
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
        json = (res.json())
        #check if theres any ratings
        try:
            number_ratings = json["items"][0]["volumeInfo"]["ratingsCount"]
            average_rating = json["items"][0]["volumeInfo"]["averageRating"]
        except (KeyError, IndexError):
            number_ratings = "Null"
            average_rating = "Null"   
        try:
            bookapidesc = json["items"][0]["volumeInfo"]["description"]
        except (KeyError, IndexError):
            bookapidesc = "Null"
        try:
            pubdate = json["items"][0]["volumeInfo"]["publishedDate"]
        except (KeyError, IndexError):
            pubdate = "Null"
        #getting the isbns
        isbn_10 = "Null"
        isbn_13 = "Null"
        for identifier in json["items"][0]["volumeInfo"]["industryIdentifiers"]:
            if identifier["type"] == "ISBN_10":
                isbn_10 = identifier["identifier"]
            if identifier["type"] == "ISBN_13":
                isbn_13 = identifier["identifier"]
        #this way they will be null if the loop doesnt find them
        
        #gemini api fetch, the rawdata is pasted from lab page
        rawdata = {
            "contents": [{
                "parts": [
                    {
                        "text": f"Summarize this text using less than 50 words: {bookapidesc}"
                    }
                ]
            }]
        }
        gemini_res = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent", params={"key":gemini_key}, headers={"Content-Type":"application/json"}, json=rawdata)
        gemini_json = (gemini_res.json())
        gemini_desc = gemini_json["candidates"][0]["content"]["parts"][0]["text"]

        #make the dictionary and return it
        bookdict = {
            "title":book.title,
            "author":book.author,
            "publishedDate":pubdate,
            "ISBN_10":isbn_10,
            "ISBN_13":isbn_13,
            "reviewCount":number_ratings,
            "averageRating":average_rating,
            "description":bookapidesc,
            "summarizedDescription":gemini_desc
        }
        return bookdict

    else:
        error404 = {"code":404}
        return error404


if __name__ == "__main__":
    app.run(debug=True)