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

@app.route("/", methods=["POST","GET"])
def index():
    if request.method=="GET":
        return render_template("index.html")
    if request.method=="POST":
        startdate = request.form.get("from_date")
        enddate = request.form.get("till_date")

        try:
            yearf, monthf, dayf = map(int, startdate.split("-"))
            yeart, montht, dayt = map(int, enddate.split("-"))
        except (ValueError, AttributeError):
            return render_template("index.html", message="invalid date(s) entered.")
        
        datef = (yearf*360)+(monthf*30)+(dayf)
        datet = (yeart*360)+(montht*30)+(dayt)

        if datef < datet:
            res = requests.get(f"https://data.calgary.ca/resource/c2es-76ed.geojson?$where=issueddate > '{startdate}' and issueddate < '{enddate}'&$select=issueddate,workclassgroup,contractorname,communityname,originaladdress,locationsgeojson")
            result = res.json()
            return result
        else:
            return render_template("index.html", message="invalid date(s) entered.")

if __name__ == "__main__":
    app.run(debug=True)