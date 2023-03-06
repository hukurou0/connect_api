from flask import current_app
from flask import request,redirect,url_for,jsonify
from sqlalchemy import exc
import re
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
#from flask_cors import CORS
from database_defined import app, db, get_key, increment_key
from database_defined import User, Admin, User_login, OTP_table, Task, Old_task, Gakka, Subject, Taken, Task_regist, Task_regist_kind, Manage_primary_key


#必要な準備
ctx = app.app_context()
ctx.push()
app = current_app
#CORS(app)

#ログイン機能に必要な準備
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
 
def generate_star(difficulty: int) -> str:
    star = ""
    for _ in range(0,difficulty):
        star += "★"
    for _ in range(difficulty,5):
        star += "☆" 
    return star    
  
def make_response(status_code:int =200, data:dict ={}):
    response_dic = {} 
    response_dic["status_code"] = status_code
    response_dic["data"] = data
    response = jsonify(response_dic)
    return response
  
@app.route("/api/getDepartment", methods=["GET"])
def getDepartment():
    if request.method == "GET": 
        gakkas = Gakka.query.filter_by().all()
        data = []
        for gakka in gakkas:
            dic = {}
            dic["id"] = gakka.id
            dic["name"] = gakka.gakka
            data.append(dic)
        print(data)
        return make_response(200,data)
    
@app.route("/api/signup", methods=["POST"])
def signup():
    if request.method == "POST": 
        json_data = request.get_json()
        data = json_data["data"]
        username = data["username"]
        password = data["password"]
        department_id = data["department"]
        try:
            id = get_key("user")
            user = User(id=id, username=username, password=generate_password_hash(password, method="sha256"), department_id = department_id,mail = "ss")
            db.session.add(user)
            db.session.commit()
            increment_key("user")
            return make_response()
        except exc.IntegrityError:
            return make_response(201)
        
    


            
if __name__=='__main__':
    app.run(debug=True)
