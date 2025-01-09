from flask import render_template, session, redirect, url_for, abort,jsonify,json
from database.mongodb import Mongodb
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId

# Inicializar conexión a MongoDB
db = Mongodb().db()

def begin(request):
    return render_template("views/index.html")

