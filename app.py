from flask import current_app
from flask import request,redirect,url_for,jsonify
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
from pack_decorater import  QueueOption, login_required, current_user_need_not_login, multiple_control, expel_freeze_account

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

@app.route("/api/getSubjects", methods=["GET"])
@login_required
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
    user = current_user_need_not_login()
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        subject_ids = json_data["id"]
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

#課題登録機能_段階1(GET)
@app.route("/api/task/regist/getSubjects", methods=["GET"])
@login_required
def taskRegistGetSubject():
    user = current_user
    user = current_user_need_not_login() 
    taken_subject_ids=[t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
    taken_subject_names=[t.subject_name for t in Taken.query.filter_by(user_id = user.id).all()]
    if request.method == "GET":
        data = {
            "name" : taken_subject_names,
            "id" : taken_subject_ids
        }
        return make_response(200,data)

#課題登録機能_段階1(POST)
@app.route("/api/task/regist/check", methods=["POST"])
@login_required
def taskRegistCheck():
    user = current_user
    user = current_user_need_not_login() 
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        subject_id = json_data["subject_id"]
        deadline_month = json_data["deadline_month"]
        deadline_day = json_data["deadline_day"]
        # deadline_day = json_data["deadline_day"]
        # 現在の月より締切の月の方が過去に存在するとき、1年繰り上げる
        today_year = date.today().year() if(deadline_month < date.today().month) else date.today().year+1
        serial = get_int_serial(today_year=today_year, deadline_month=deadline_month, deadline_day=deadline_day)
        tasks = Task.query.filter_by(subject_id=subject_id, serial=serial).all()
        tasks_id = []
        tasks_packs = {}
        for t in tasks:
            tasks_id = tasks_id + [t.id]
            tasks_packs[t.id] = {
                "subject_name" : t.subject_name,
                "summary" : t.summary,
                "detail" : t.detail,
                "deadline" : f"{deadline_month}/{deadline_day}" 
            }
        data = {
            "tasks_id" : tasks_id,
            "tasks" : tasks_packs
        }
        return make_response(200, data)

#課題登録機能_段階2(POST1)
@app.route("/api/task/regist/duplication", methods=["POST"])
@login_required
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

#課題登録機能_段階2(POST2)
@app.route("/api/task/regist/new", methods=["POST"])
@login_required
def taskRegistNew():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST":
        try:
            json_data = json.loads(request.get_json())
            subject_id = json_data["subject_id"]
            deadline_month = json_data["deadline_month"]
            #!today_year = json_data["deadline_year"]
            today_year = date.today().year() if(deadline_month < date.today().month) else date.today().year + 1  #!unused予定
            summary = json_data["summary"]
            deadline_day = json_data["deadline_day"]
            detail = json_data["detail"]
            difficulty = json_data["difficulty"]
            serial = get_int_serial(today_year, today_year=today_year, deadline_month=deadline_month, deadline_day=deadline_day)
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

#課題削除機能(GET)
@app.route("/api/task/getTasks", methods=["GET"])
@login_required
def taskGetTasks():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "GET":
        registerd_tasks = Task.query.filter_by(user_id=user.id).all()
        task_packs = []
        for t in registerd_tasks:
            subject = Subject.query.filer_by(id=t.subject_id).one()
            str_datetime = serial_to_str(t.serial)
            task_packs += [
                {
                    "id" : t.id,
                    "subject_name" : subject.subject_name,
                    "detail" : t.detail,
                    "deadline" : str_datetime
                }
            ]
        data = {
            "tasks" : task_packs
        }
        return make_response(200, data)

#課題削除機能(POST)
@app.route("/api/task/delete", methods=["POST"])
@login_required
def taskDelete():
    if request.method == "POST": 
        json_data = json.loads(request.get_json())
        task_id = json_data["task_id"]
        Task.query.filter_by(id=task_id).delete()
        db.session.commit
        return make_response()

            
if __name__=='__main__':
    app.run(debug=True, threaded=True)
