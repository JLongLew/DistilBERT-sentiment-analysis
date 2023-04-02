from flask import *
import pyrebase
import firebase_admin
from firebase_admin import credentials, storage, firestore
from google.cloud import storage as sto 

UPLOAD_FOLDER = 'website/static/images/'

app = Flask(__name__)
app.secret_key = 'secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Firebase config
config = {
    "apiKey": "AIzaSyCH-oeHe3XD9tYnY8ukCWEXJgWhux_5cH4",
    "authDomain": "sentimentanalyais-4721b.firebaseapp.com",
    "projectId": "sentimentanalyais-4721b",
    "storageBucket": "sentimentanalyais-4721b.appspot.com",
    "messagingSenderId": "906296566901",
    "appId": "1:906296566901:web:9400fdfd405c45c58f843c",
    "measurementId": "G-048H4L8JD4",
    "databaseURL": ""
}

# Init Firebase REST API
firebase = pyrebase.initialize_app(config)
# Auth Instance
auth = firebase.auth()

# Connect Firebase service account
cred = credentials.Certificate("./serviceAccountKey.json")
# Init Firebase admin
firebase_admin.initialize_app(cred, {
    'storageBucket': 'sentimentanalyais-4721b.appspot.com'})
# Firestore database instance
db = firestore.client()
# Firebase storage instance
bucket = storage.bucket()
storage_client = sto.Client.from_service_account_json("./serviceAccountKey.json")

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

# Method Not Allowed Error 
@app.errorhandler(405)
def page_not_found(e):
	return render_template("405.html"), 405
    
# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500

from website.business import routes
from website.customer import routes
from website.product import routes