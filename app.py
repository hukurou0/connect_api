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
from database_defined import app, db, get_key, increment_key
from database_defined import User, Admin, User_login, OTP_table, Task, Old_task, Gakka, Subject, Taken, Task_regist, Task_regist_kind, Manage_primary_key


#必要な準備
ctx = app.app_context()
ctx.push()
app = current_app

#ログイン機能に必要な準備
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')
 
def generate_star(difficulty):
    star = ""
    for _ in range(0,difficulty):
        star += "★"
    for _ in range(difficulty,5):
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
            user = User(id = id,username=username, password=generate_password_hash(password, method="sha256"), department_id = department_id,mail = "ss")
            db.session.add(user)
            db.session.commit()
            increment_key("user")
            return make_response()
        except exc.IntegrityError:
            return make_response(201)
        

#!---------------------------------shogo07xx-------------------------------------!#   
      
@app.route("/api/Subjects", methods=["GET"])
@login_required
def getSubjet():
    user = current_user
    days = ['mon','tue','wed','thu','fri']
    periods = ['1','2','3','4','5']
    if request.method == "GET": 
        # 現在履修中の科目idを配列に格納 (taken_now) #!この中から特定の曜日時限にマッチしたSubject_idを取り出す->これがtaken_now+
        taken_subject_ids=[t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
        # taken_now2 を除いた科目を配列に格納 (subject_for_exclude)
        exclude_subject_all=[]
        # 何曜日の何次元目か
        when = []
        for period in periods:
            for day in days:
                when.append(f'{day}{period}')
                taken_now = Subject.query.filter_by(id.in_(taken_subject_ids), department_id=user.department_id, day=day, period=period)


                taken_now = Subject.query.filter_by(id=taken.subject_id).one_or_none()
                subject_sorts3.append(
                    Subject.query.filter(
                        ~Subject.id.in_(subject_for_exclude),
                        Subject.department_id==user.department_id, Subject.day==f'{day}',Subject.period==period
                        ).all()
                    )        

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

"""
{
    "status_code":001
    "data" : {
        "when" : ["mon1", "tue1", ..., "fri5"]
        "name" : [ ["線形代数学Ⅰ", "微分積分学Ⅰ", ..., "線形代数学Ⅱ"], [...], ...,[...] ]
        "id" : [ ["3", "1", ..., "4"], [...], ..., [...] ]
    }
}
"""
@app.route("/taken", methods=['GET','POST'])  
def RisyukamokuTouroku(url): 
    if request.method=='GET':
        #現在履修中の科目を参照(:taken_now2)
        taken_now2=[]
        subject_for_exclude=[]
        for taken in Taken.query.filter_by(user_id=user.id):
            taken_now2.append(
                Subject.query.filter(Subject.id==taken.subject_id).one_or_none()
                )
            subject_for_exclude.append(taken.subject_id)
        #曜日時限でソート∧履修科目(subject_id:subject_for_exclude)を除いた科目一覧
        subject_sorts3=[]
        for period in periods:
            for day in days:
                subject_sorts3.append(
                    Subject.query.filter(
                        ~Subject.id.in_(subject_for_exclude),
                        Subject.department_id==user.department_id,Subject.day==f'{day}',Subject.period==period
                        ).all()
                    )

        return render_template("sample_taken.html",subject_sorts3=subject_sorts3,taken_now2=taken_now2,css=url.taken_css,icon=url.icon,header = url.header)
    else:                  
        #ユーザーの旧履修登録科目を削除              
        Taken.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        #ユーザーの新履修登録科目を登録
        taken_new=[]
        for period in periods:
            for day in days:
                subject_id = request.form.get("{}{}".format(day,period))
                #空きコマをデータテーブルに追加されないよう、弾く。#空きコマは5桁全て0の"文字列"。
                if subject_id!="00000":
                    taken_new.append(Taken(user_id=user.id,subject_id=subject_id,department_id=user.department_id))
        db.session.add_all(taken_new)
        db.session.commit()  
        flask.flash("履修科目登録が完了しました＼(^o^)／","success")  
        return redirect("/")

#!---------------------------------shogo07xx-------------------------------------!#        

            
if __name__=='__main__':
    app.run(debug=True)
