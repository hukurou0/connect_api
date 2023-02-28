import flask
from flask import current_app
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
from datetime import datetime, date, timedelta
import json
from typing import Union
from flask_cors import CORS
from database_defined import app, db, get_key, increment_key
from database_defined import User, Admin, User_login, OTP_table, Task, Old_task, Gakka, Subject, Taken, Task_regist, Task_regist_kind, Manage_primary_key


#! ログインせずにテストをしたい時のための関数。目的の関数の @login_required を 装飾付きコメントアウト「#!」をしてテストすること (∵検索のためのマーカー設置) 
#! 本番環境用に移行させたいときは必ず #!で検索をかけ @login_required のコメントアウトを解除すること。 
def current_user_not_login() -> Union[None, User]:
    #! return  #本番環境用   
    current_user_ = User.query.filter_by(id=1).one()
    return current_user_  #テスト環境用 

#必要な準備
ctx = app.app_context()
ctx.push()
app = current_app

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
            user = User(id=id, username=username, password=generate_password_hash(password, method="sha256"), department_id = department_id,mail = "ss")
            db.session.add(user)
            db.session.commit()
            increment_key("user")
            return make_response()
        except exc.IntegrityError:
            return make_response(201)
        
@app.route("/api/taken/getSubjects", methods=["GET"])
#!@login_required
def getSubjetsByTaken():
    user = current_user 
    user = current_user_not_login() #テスト環境用
    days = ['mon','tue','wed','thu','fri']
    periods = ['1','2','3','4','5']
    # 現ログインユーザーの when[i] に対する 履修中科目(taken_subject) の検索(in句) のために使用
    taken_now_subject_ids=[t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
    if request.method == "GET": 
        # when[i]: 曜日時限, is_taken: when[i]に対して履修中の科目が存在するか否か
        # subject_ids[i]: [when[i]に対する現履修中科目id, ..., 〃] (taken_subject_ids[∃j]を優先), subject_names[i]: [when[i]に対する現履修中科目名, ..., 〃] (taken_subject_ids[∃j]に対応するものを優先)  
        when, is_taken, subject_ids, subject_names = [], [], [], []  # dataとしてクライアントに渡す要素
        for period in periods:
            for day in days:
                when.append(f'{day}{period}')
                taken_subject = Subject.query.filter(Subject.id.in_(taken_now_subject_ids), Subject.day==day, Subject.period==period).one_or_none()
                when_i_subjects = Subject.query.filter_by(department_id=user.department_id, day=day, period=period).all()
                if(taken_subject is None):
                    is_taken.append("False")
                else:
                    is_taken.append("True")
                    # 既に履修登録していた課題が配列の添字最小となるように移動.
                    when_i_subjects.insert(0, taken_subject)
                    when_i_subjects = list(set(when_i_subjects))
                # subject_names: ["空きコマ", Union["履修中科目名", "other0"], other1, ..., otherN]
                subject_ids.append(['0'] + [f'{s.id}' for s in when_i_subjects])
                subject_names.append(["空きコマ"] + [s.subject_name for s in when_i_subjects])
        data = {
            "when" : when,
            "id" : subject_ids,
            "name" : subject_names, 
            "is_taken" : is_taken
        }
        return make_response(200,data)
      
@app.route("/api/taken", methods=["POST"])
@login_required
def taken():
    user = current_user
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        subject_ids = json_data["id"]
        try:
            Taken.query.filter_by(user_id=user.id).delete()
            new_taken_all = []
            for subject_id in subject_ids:
                if(subject_id!=0):
                    new_taken = Taken(user_id=user.id, subject_id=subject_id)
                    new_taken_all.append(new_taken)
            db.session.add_all(new_taken_all)
            db.commit()
            return make_response()
        except exc.IntegrityError:
            return make_response(201)   

            
if __name__=='__main__':
    app.run(debug=True)
