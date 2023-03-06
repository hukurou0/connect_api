from flask import current_app
from flask import request, redirect, url_for, jsonify
from sqlalchemy import exc, func
import re
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
#from flask_cors import CORS
from database_defined import app, db, get_key, increment_key
from database_defined import (User, Admin, User_login, OTP_table, Gakka, Subject, Taken, 
                               Task, Old_task, Task_regist, Task_regist_kind, Manage_primary_key)
from typing import Union
from pack_datetime_unixtime_serial import get_float_serial, get_int_serial, serial_to_str
from pack_decorater import  QueueOption, login_required, current_user_need_not_login, multiple_control, expel_frozen_account

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

# サインアップ機能(GET), ユーザー情報編集機能(GET) --Unit Tested 
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

# サインアップ機能(POST) --Unit Tested    
@app.route("/api/signup", methods=["POST"])
def signup():
    if request.method == "POST": 
        json_data = request.get_json()
        data = json_data["data"]
        username = data["username"]
        password = data["password"]
        department_id = data["department"]
        mail = data["mail"]
        try:
            id = get_key("user")
            user = User(id=id, username=username, password=generate_password_hash(password, method="sha256"), department_id = department_id, mail = mail)
            db.session.add(user)
            db.session.commit()
            increment_key("user")
            return make_response()
        except exc.IntegrityError:
            return make_response(201)

# 所属学科変更機能(POST) --Unit Tested
@app.route("/api/user/modifyDepartment", methods=["POST"])
@login_required
@expel_frozen_account
def modify_user():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        department_id = json_data["department"]
        try:
            user.department_id = department_id
            db.session.commit()
            return make_response()
        except exc.IntegrityError:
            return make_response(201)        

# 履修登録機能(GET) --Unit Tested
@app.route("/api/getSubjects", methods=["GET"])
@login_required
@expel_frozen_account
def getSubjet():
    user = current_user
    user = current_user_need_not_login()
    days = ['mon','tue','wed','thu','fri']
    periods = ['1','2','3','4','5']
    # when[i]に対する現履修中科目(taken_subject)の検索(in句)のために使用
    now_subject_ids=[t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
    if request.method == "GET": 
        # when[i]: 曜日時限, is_taken: when[i]に対して履修中の科目が存在するか否か
        # subject_ids[i]: [when[i]に対する現履修中科目id, ..., 〃] (taken_subject_ids[∃j]を優先), subject_names[i]: [when[i]に対する現履修中科目名, ..., 〃] (taken_subject_ids[∃j]に対応するものを優先)  
        when, is_taken, subject_ids, subject_names = [], [], [], []  # dataとしてクライアントに渡す要素
        for period in periods:
            for day in days:
                when.append(f'{day}{period}')
                taken_subject = Subject.query.filter(Subject.id.in_(now_subject_ids), Subject.department_id==user.department_id, Subject.day==day, Subject.period==period).one_or_none()
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
            "when": when,
            "id": subject_ids,
            "name": subject_names, 
            "is_taken": is_taken
        }
        return make_response(200,data)

# 履修登録機能(POST) --Unit Tested
@app.route("/api/taken", methods=["POST"])
@login_required
@expel_frozen_account
def taken():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        subject_ids = json_data["subject_id"]
        try:
            Taken.query.filter_by(user_id=user.id).delete() # レコードが存在しない場合は何も起こらない
            new_taken_all = []
            for subject_id in subject_ids:
                if(subject_id!=0):
                    new_taken = Taken(user_id=user.id, subject_id=subject_id)
                    new_taken_all.append(new_taken)
            db.session.add_all(new_taken_all)
            db.session.commit()
            return make_response()
        except exc.IntegrityError:
            return make_response(201)

# 課題登録機能_段階1(GET) --Unit Tested
@app.route("/api/task/regist/getSubjects", methods=["GET"])
@login_required
@expel_frozen_account
def taskRegistGetSubject():
    user = current_user
    user = current_user_need_not_login() 
    takens =  Taken.query.filter_by(user_id = user.id).all()
    taken_subject_ids, taken_subject_names = [], []
    for t in takens:
        taken_subject_ids += [t.subject_id]
        subject = Subject.query.filter_by(id=t.subject_id).one()    
        taken_subject_names += [subject.subject_name]
    if request.method == "GET":
        data = {
            "name" : taken_subject_names,
            "id" : taken_subject_ids
        }
        return make_response(200,data)

# 課題登録機能_段階1(POST) --Unit Tested
@app.route("/api/task/regist/check", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistCheck():
    if request.method == "POST": 
        #subject_id, deadline_year, deadline_month, deadline_day = 1, 2023, 4, 1
        json_data = json.loads(request.get_json())
        subject_id = json_data["subject_id"]
        deadline_year = json_data["deadline_year"]
        deadline_month = json_data["deadline_month"]
        deadline_day = json_data["deadline_day"]
        deadline_serial = get_int_serial(deadline_year, deadline_month, deadline_day)
        tasks = Task.query.filter_by(subject_id=subject_id, serial=deadline_serial).all()
        tasks_id = []
        tasks_packs = {}
        for t in tasks:
            s = Subject.query.filter_by(id = t.subject_id).one()
            tasks_id += [t.id]
            tasks_packs[t.id] = {
                "subject_name": s.subject_name,
                "summary": t.summary,
                "detail": t.detail,
                "deadline": f"{deadline_month}/{deadline_day}" 
            }
        data = {
            "tasks_id" : tasks_id,
            "tasks" : tasks_packs
        }
        return make_response(200, data)

# 課題登録機能_段階2(POST1) --Unit Tested
@app.route("/api/task/regist/duplication", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistDuplication():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST":
        json_data = json.loads(request.get_json())
        task_id = json_data["task_id"]
        task_regist = Task_regist(user_id=user.id, task_id=task_id, kind=1) 
        db.session.add(task_regist)
        db.session.commit()
        return make_response()

# 課題登録機能_段階2(POST2) --Unit Tested
@app.route("/api/task/regist/new", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistNew():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST":
        try:
            json_data = json.loads(request.get_json())
            subject_id = json_data["subject_id"]
            deadline_year = json_data["deadline_year"]
            deadline_month = json_data["deadline_month"]
            deadline_day = json_data["deadline_day"]           
            summary = json_data["summary"]
            detail = json_data["detail"]
            difficulty = json_data["difficulty"]
            serial = get_int_serial(deadline_year, deadline_month, deadline_day)
            task_data = [user.id, subject_id, detail, summary, serial, difficulty]
            task_regist_data = [user.id, 1]
            @multiple_control(QueueOption.singleQueue)  # 悲観ロック
            def add_Task_and_Task_regist(task_data_:list, task_regist_data_:list):
                t, r = task_data_, task_regist_data_
                task = Task(user_num=t[0], subject_id=t[1], detail=t[2], summary=t[3], serial=t[4], difficulty=t[5])
                db.session.add(task)
                db.session.commit()
                task_id = db.session.query(func.max(Task.id)).one()[0]  
                task_regist = Task_regist(user_id=r[0], task_id=task_id, kind=r[1])
                db.session.add(task_regist)
                db.session.commit()
            add_Task_and_Task_regist(task_data, task_regist_data)
            return make_response()
        except exc.DataError:  #データ長のはみ出し
            return make_response(3)

# 課題削除機能(GET)、課題表示機能(GET) --Unit Tested
@app.route("/api/task/getTasks", methods=["GET"])
@login_required
@expel_frozen_account
def taskGetTasks():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "GET":
        registerd_tasks = Task_regist.query.filter_by(user_id=user.id).all()
        tasks = []
        for r in registerd_tasks:
            task = Task.query.filter_by(id=r.task_id).one()
            subject = Subject.query.filter_by(id=task.subject_id).one()
            tasks += [
                {
                    "id": task.id,
                    "subject_name": subject.subject_name,
                    "summary": task.summary,
                    "detail": task.detail,
                    "deadline": serial_to_str(task.serial)
                }
            ]
        data = {
            "tasks" : tasks
        }
        return make_response(200, data)

# 課題削除機能(POST) --Unit Tested
@app.route("/api/task/delete", methods=["POST"])
@login_required
@expel_frozen_account
def taskDelete():
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        task_id = json_data["task_id"]
        task_regist = Task_regist.query.filter_by(task_id=task_id).one()
        if(task_regist.kind==1):
            Task.query.filter_by(id=task_id).delete()
        db.session.delete(task_regist)
        db.session.commit()     
        return make_response()
    
# 課題表示機能(GET)
@app.route("/api/task/getTasks", methods=["GET"])
@login_required
@expel_frozen_account
def taskGetTask():
    if request.method == "GET": 
        #subject_id, deadline_year, deadline_month, deadline_day = 1, 2023, 4, 1
        json_data = json.loads(request.get_json())
        subject_id = json_data["subject_id"]
        deadline_year = json_data["deadline_year"]
        deadline_month = json_data["deadline_month"]
        deadline_day = json_data["deadline_day"]
        deadline_serial = get_int_serial(deadline_year, deadline_month, deadline_day)
        tasks = Task.query.filter_by(subject_id=subject_id, serial=deadline_serial).all()
        tasks_id, hard_ids = [], []
        tasks_packs = {}
        for t in tasks:
            s = Subject.query.filter_by(id = t.subject_id).one()
            if(t.difficulty==5 or t.serial < get_int_serial() + 3):
                hard_ids += [t.id]
            tasks_id += [t.id]
            tasks_packs[t.id] = {
                "subject_name": s.subject_name,
                "summary": t.summary,
                "detail": t.detail,
                "deadline": f"{deadline_month}/{deadline_day}",
                "difficulty": t.difficulty
            }
        data = {
            "all_tasks_id": tasks_id,
            "hard_tasks_id": hard_ids,
            "tasks": tasks_packs
        }
        return make_response(200, data)

#! ログアウト機能(GET)
@app.route("/api/logout", methods=["GET"])
@login_required
@expel_frozen_account
def logout():
    if request.method == "GET":
        logout_user()  # セッション情報の削除  #? 変更となる可能性あり
        return make_response()
            
if __name__=='__main__':
    app.run(debug=True, threaded=True)
