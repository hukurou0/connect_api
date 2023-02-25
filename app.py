import flask
from flask import Flask,session
from flask import render_template,request,redirect,url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import re
from flask_login import UserMixin,LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secret
import os
from time import time
from datetime import datetime, date,timedelta
import json
#from flask_cors import CORS

#必要な準備
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = secret.LocalDatabase.uri
app.config['SECRET_KEY'] = secret.SECRET_KEY.SECRET_KEY
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')

#データベース定義
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,unique=True)
    password = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, nullable=False) 
    mail = db.Column(db.String(80), nullable=False,unique=True) 
    signup_datetime = db.Column(db.DateTime, nullable=False, default=datetime.today()) #! add: signup日時
    login_possible = db.Column(db.Integer, nullable=False, default=1) #! add: 1=ログイン可能, 0=ログイン不可能(凍結) 
    privilege = db.Column(db.Integer, nullable=False, default=0) #! add: 0<強力な権限, 2=adminデータに干渉可能(for hukusuke)

class User_login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  
    login_ut = db.Column(db.Integer, nullable=False, default=time()) #ログイン(orしようとした(ユーザー名のみ一致))時のユニックスタイム
    login_datetime = db.Column(db.DateTime, nullable=False, default=datetime.today()) #同上(文字列型時間)
    is_successful = db.Column(db.Integer, nullable=False) #1:True, 0:False

class OTP_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(80), nullable=False) 
    otp = db.Column(db.Integer, nullable=False)
    issuance_ut = db.Column(db.Integer, nullable=False)
    
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_num = db.Column(db.Integer)
    subject_id = db.Column(db.Integer, nullable=False)
    detail = db.Column(db.String(80), nullable=False)
    summary = db.Column(db.String(80), nullable=False)
    serial = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    
class Old_task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer)
    user_num = db.Column(db.Integer)
    subject_id = db.Column(db.Integer, nullable=False)
    detail = db.Column(db.String(80), nullable=False)
    summary = db.Column(db.String(80), nullable=False)
    serial = db.Column(db.Integer, nullable=False)
    next_task_id = db.Column(db.Integer)
    
class Gakka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gakka = db.Column(db.String(80), nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    department_id = db.Column(db.Integer, nullable=False) 
    subject_name = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(50), nullable=False)
    day = db.Column(db.String(50), nullable=False) 
    period = db.Column(db.Integer)
    
class Taken(db.Model): 
    id = db.Column(db.Integer, primary_key=True)  
    user_id = db.Column(db.Integer, nullable=False) 
    subject_id = db.Column(db.Integer, nullable=False) 
    department_id = db.Column(db.Integer, nullable=False)

#kindについて  
class Task_regist(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, nullable=False) 
    task_id = db.Column(db.Integer, nullable=False)
    regist_time = db.Column(db.Integer)
    kind = db.Column(db.Integer)
         
class Task_regist_kind(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    kind = db.Column(db.String(50), nullable=False)  
    
class Manage_primary_key(db.Model):
    table = db.Column(db.String, primary_key=True) 
    next_primary_key = db.Column(db.Integer, nullable=False)     
    
def get_key(table):
    primary_key = Manage_primary_key.query.filter_by(table = table).first()  
    id = primary_key.next_primary_key
    return id

def increment_key(table):
    primary_key = Manage_primary_key.query.filter_by(table = table).first()  
    id = primary_key.next_primary_key
    next_id = id + 1  
    primary_key.next_primary_key = next_id
    db.session.commit()
 
def generate_star(difficulty):
    star = ""
    for i in range(0,difficulty):
        star += "★"
    for i in range(difficulty,5):
        star += "☆" 
    return star    
  
def make_response(status_code=200,data={}):
    response_dic = {} 
    response_dic["status_code"] = status_code
    response_dic["data"] = data
    response = jsonify(response_dic)
    return response
  
@app.route("/api/getDepartment", methods=["GET"])
def getDepartment():
    if request.method == "GET": 
        gakkas = Gakka.query.filter_by().all()
        name = []
        id = []
        for gakka in gakkas:
            name.append(gakka.gakka)
            id.append(gakka.id)
        data = {
            "name":name,
            "id":id
        }
        return make_response(200,data)
    
@app.route("/api/signup", methods=["POST"])
def signup():
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        username = json_data["username"]
        password = json_data["password"]
        department_id = json_data["department"]
        try:
            id = get_key("user")
            user = User(id = id,username=username, password=generate_password_hash(password, method="sha256"),department_id = department_id,mail = "ss")
            db.session.add(user)
            db.session.commit()
            increment_key("user")
            return make_response()
        except exc.IntegrityError:
            return make_response(201)
    
##################################################################################################   
            
if __name__=='__main__':
    app.run(debug=True)
