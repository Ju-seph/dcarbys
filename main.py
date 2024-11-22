from flask import Flask, request ,render_template
import os

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.getenv("KEY")