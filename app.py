from time import time
from flask import current_app
from flask import request, redirect, url_for, jsonify
from sqlalchemy import exc, func
import re
from flask_login import LoginManager, login_user, logout_user, current_user,login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import json
#from flask_cors import CORS
from database_defined import app, db
from database_defined import (User, Admin, User_login, Login_limiter, OTP_table, Gakka, Subject, Taken, 
                               Task, Old_task, Task_regist, Task_regist_kind)
from typing import Union
from pack_datetime_unixtime_serial import get_float_serial, get_int_serial, serial_to_str, serial_to_iso
from pack_decorater import  QueueOption,  multiple_control, expel_frozen_account, current_user_need_not_login
from pack_datetime_unixtime_serial import TimeBase
import traceback
from psycopg2 import errors as psycopg2_errors
from pack_func import create_task_entity,create_task_entity_in_apitaskgetTasks

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
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/unlogin')

def generate_star(difficulty: int) -> str:
    star = ""
    for _ in range(0,difficulty):
        star += "★"
    for _ in range(difficulty,5):
        star += "☆" 
    return star    
  
def make_response(status_code:int = 1, data:dict ={}):
    response_dic = {} 
    response_dic["status_code"] = status_code
    response_dic["data"] = data
    response = jsonify(response_dic)
    return response

def is_strict_login_possible(username: str, password: str, is_update_restriction: bool = False) -> bool:
    """
    ログイン機能にアクセス制限を課す関数. 
    ログイン制限はログイン試行時にログイン試行回数が一定回数以上になった場合に発動.
    TimeBaseクラスで許容アクセス回数(/秒)とログイン制限の時間幅を指定する.

    Parameters
    ----------
    is_update_ristriction: bool, default False
        third_arg = True の場合、ログイン制限時のログイン試行に対して、
        制限時間を更新する (実質ログイン可能までの時間が増加する) .
    
    Returns
    ----------
    ログイン条件(制限時間中でなく入力内容が正しい)を満たす時: True
    """
    user = User.query.filter_by(username=username).one_or_none()
    if(user is None): 
        return False,None
    login_limiter = Login_limiter.query.filter_by(user_id=user.id, is_stopped_access=True).all()
    # login_limmiter リストが空でないとき かつ ログイン制限時間中でないとき (短絡評価のため login_limiter リストは空でも良い)
    if(login_limiter and time() < login_limiter[-1].login_ut + TimeBase.stop_duration):
        if(is_update_restriction): 
            l = Login_limiter(user_id=user.id, is_stopped_access=True)
            db.session.add(l)
            db.session.commit()
        return False,None
    # ログイン未制限中 かつ ログイン成功時
    elif(check_password_hash(user.password, password)):
        return True,user
    else:
        login_fails_by_user = Login_limiter.query.filter(Login_limiter.user_id == user.id, \
                                                         TimeBase.focus_lower_limit_ut < Login_limiter.login_ut).all()
        # 罰点(ログイン失敗回数)が規定回数以上になった場合
        if(len(login_fails_by_user) - 1 > TimeBase.access_maximum_limit):
            l_l = Login_limiter(user_id=user.id, is_stopped_access=True)
        else: 
            l_l = Login_limiter(user_id=user.id) 
        db.session.add(l_l)
        db.session.commit()
        return False,None

# サインアップ機能(get), ユーザー情報編集機能(get) --Unit Tested 
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
        return make_response(1,data)

# サインアップ機能(post) --Unit Tested    
@app.route("/api/signup", methods=["POST"])
def signup():
    if request.method == "POST": 
        json_data = request.get_json()
        try:
            data = json_data["data"]
            username = data["username"]
            password = data["password"]
            department_id = data["department_id"]
        except:
            return make_response(2)
        
        def create_user():
            try:
                user = User( username=username, password=generate_password_hash(password, method="sha256"), \
                        department_id = department_id,mail="abbb")
                session.add(user)
                session.commit()

            except exc.IntegrityError as sqlalchemy_error: #IntegrityErrorは一意制約だけでなくnull違反など包括的なエラー
                raise sqlalchemy_error.orig # DatabaseごとのAPIのエラーをraiseする
            
        try:
            session = db.session
        except:
            return make_response(3)    
            
        try:
            create_user()
            return make_response()
        except psycopg2_errors.UniqueViolation:# 一意制約違反のエラー　ここではusername重複
            #traceback.print_exc()
            session.rollback()
            return make_response(201)
        finally:
            session.close()
            

# 所属学科変更機能(post) --Unit Tested
@app.route("/api/user/modifyDepartment", methods=["POST"])
@login_required
@expel_frozen_account
def modify_user():
    user = current_user
    if request.method == "POST": 
        json_data = request.get_json()
        try:
            data = json_data["data"]
            department_id = data["department_id"]
        except:
            return make_response(2)
        
        try:
            session = db.session
            user.department_id = department_id
            session.commit()
        except:
            session.rollback()
            return make_response(3) 
        finally:
            session.close()
        
        return make_response()       

# 履修登録機能(get) --Unit Tested
@app.route("/api/taken/getSubjects", methods=["GET"])
@login_required
@expel_frozen_account
def getSubjet():
    user = current_user
    days = ['mon','tue','wed','thu','fri']
    periods = ['1','2','3','4','5']
    # taken_subject の id 検索のために定義. 履修科目IDを要素として持つ配列.
    now_taken_subject_ids = [t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
    if request.method == "GET": 
        data, taken_id = {}, []
        for period in periods:
            for day in days:
                subjects = Subject.query.filter_by(period = period, day = day)  # その曜日時限の科目一覧
                taken_subject = [s for s in subjects if s.id in now_taken_subject_ids]  # その曜日時限の履修科目オブジェクト
                taken_id = 0 if(taken_subject == []) else taken_subject[0].id  # その曜日時限の履修科目ID
                classes = [{
                    "id": 0,
                    "name": "空きコマ"
                }]
                classes += [
                    {
                        "id": s.id,
                        "name": s.subject_name
                    }
                for s in subjects] 
                data[f"{day}{period}"] = {
                    "classes": classes,
                    "taken_id": taken_id
                }
        return make_response(1, data)

# 履修登録機能(post) --Unit Tested
@app.route("/api/taken", methods=["POST"])
@login_required
@expel_frozen_account
def taken():
    user = current_user
    if request.method == "POST": 
        json_data = request.get_json()
        try:
            data = json_data["data"]
            subject_ids = data["subject_id"]
        except:
            return make_response(2)
        
        Taken.query.filter_by(user_id=user.id).delete() # レコードが存在しない場合は何も起こらない
        new_taken_all = []
        for subject_id in subject_ids:
            if(subject_id!=0):
                new_taken = Taken(user_id=user.id, subject_id=subject_id)
                new_taken_all.append(new_taken)
        try:
            session = db.session
            session.add_all(new_taken_all)
            session.commit()
            return make_response()
        except:
            session.rollback()
            return make_response(3) 
        finally:
            session.close()
        
        

# 課題登録機能_段階1(get) --Unit Tested
@app.route("/api/task/regist/getSubjects", methods=["GET"])
@login_required
@expel_frozen_account
def taskRegistGetSubject():
    user = current_user
    takens_ =  Taken.query.filter_by(user_id = user.id).all()
    takens = []
    for t in takens_:
        subject = Subject.query.filter_by(id=t.subject_id).one()    
        takens += [
            {"name": subject.subject_name, "subject_id": t.subject_id}
        ]
    if request.method == "GET":
        data = takens
        return make_response(1,data)

# 課題登録機能_段階1(post) --Unit Tested
@app.route("/api/task/regist/check", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistCheck():
    if request.method == "POST": 
        #subject_id, deadline_year, deadline_month, deadline_day = 1, 2023, 4, 1
        json_data = request.get_json()
        try:
            data = json_data["data"]
            subject_id = data["subject_id"]
            deadline_year = data["deadline_year"]
            deadline_month = data["deadline_month"]
            deadline_day = data["deadline_day"]
        except:
            return make_response(2)
        
        deadline_serial = get_int_serial(deadline_year, deadline_month, deadline_day)
        tasks = Task.query.filter_by(subject_id=subject_id, serial=deadline_serial).all()
        tasks_packs = []
        for t in tasks:
            s = Subject.query.filter_by(id = t.subject_id).one()
            tasks_packs += [
                {
                "task_id": t.id,
                "subject_name": s.subject_name,
                "summary": t.summary,
                "detail": t.detail,
                "deadline": f"{deadline_month}/{deadline_day}" 
                }
            ]
        data = {
            "tasks" : tasks_packs
        }
        return make_response(1, data)

# 課題登録機能_段階2(post1) --Unit Tested
@app.route("/api/task/regist/duplication", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistDuplication():
    user = current_user
    if request.method == "POST":
        json_data = request.get_json()
        try:
            data = json_data["data"]
            task_id = data["task_id"]
        except:
            return make_response(2)
        
        task_regist = Task_regist(user_id=user.id, task_id=task_id, kind=1) 
        try:
            session = db.session
            session.add(task_regist)
            session.commit()
            return make_response() #make_response->finaly->returnの順に処理される
        except:
            session.rollback()
            return make_response(3) 
        finally:
            session.close()
        
        

# 課題登録機能_段階2(post2) --Unit Tested
@app.route("/api/task/regist/new", methods=["POST"])
@login_required
@expel_frozen_account
def taskRegistNew():
    user = current_user
    if request.method == "POST":
        try:
            json_data = request.get_json()
            try:
                data = json_data["data"]
                subject_id = data["subject_id"]
                deadline_year = data["deadline_year"]
                deadline_month = data["deadline_month"]
                deadline_day = data["deadline_day"]           
                summary = data["summary"]
                detail = data["detail"]
                difficulty = data["difficulty"]
            except:
                return make_response(2)
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

# 課題削除機能(get) --Unit Tested
@app.route("/api/user/getTasks", methods=["GET"])
@login_required
@expel_frozen_account
def taskGetTasks():
    user = current_user
    if request.method == "GET":
        tasks:list = Task.query.filter_by(user_num=user.id).all()
        tasks_list = create_task_entity(tasks)
        data = {
            "tasks" : tasks_list
        }
        return make_response(1, data)

# 課題削除機能(post) --Unit Tested
@app.route("/api/user/deleteTask", methods=["POST"])
@login_required
@expel_frozen_account
def taskDelete():
    user = current_user
    user = current_user_need_not_login()
    if request.method == "POST": 
        json_data = request.get_json()
        try:
            data = json_data["data"]
            task_id = data["task_id"]
        except:
            return make_response(2)
        task = Task.query.filter_by(id=task_id).first()#TaskテーブルからOldTaskテーブルに移すことで削除とする。
        old_task = Old_task(task_id = task.id,user_num = task.user_num,subject_id = task.subject_id,detail = task.detail,summary = task.summary,serial = task.serial)
        task_regist = Task_regist(user_id=user.id, task_id=task_id, kind=5)#Task_registテーブルにログを残す。
        try:
            session = db.session
            session.delete(task)
            session.add(old_task)
            session.add(task_regist)
            session.commit()
            return make_response()
        except:
            session.rollback()
            return make_response(3) 
        finally:
            session.close()
             
    
# 課題表示機能(get) --Unit Tested
@app.route("/api/task/getTasks", methods=["GET"])
@login_required
@expel_frozen_account
def taskGetTask():
    user = current_user
    if request.method == "GET": 
        #課題表示出来るかの確認ー(履修登録)ーーーーーーーーーーーーーーーー
        taken = Taken.query.filter_by(user_id=user.id).all()
        if taken == []:
            _ = {"subject_taken":False}
        else:
            _ = {"subject_taken":True}
            
        #課題表示出来るかの確認ー(課題登録)ーーーーーーーーーーーーーーーー
        task_regists = Task_regist.query.filter_by(user_id=user.id).all()
        regist_time = []
        for task_regist in task_regists:
            regist_time.append(task_regist.regist_time)
        if regist_time != []:
            recent_regist_time: float = max(regist_time)
            now_serial = get_float_serial()
            if now_serial >= recent_regist_time + 3:
                __ = {"task_regist":False}
            else:
                __ = {"task_regist":True}
        else:
            __ = {"task_regist":False}
            
        #課題表示出来るかの確認ー("display_ok"作成)ーーーーーーーーーーーーーーーー
        display_ok = {}
        display_ok.update(**_, **__)
        
        #残りの課題表示出来る時間
        #hour = int((recent_regist_time + 3 - now_serial)/0.04166667) 

        #! 表示期限を示すシリアル値をiso8601に変換
        iso_visible_limit = serial_to_iso(recent_regist_time + 3,is_basic_format = False)
        
        #課題情報を作成ーーーーーーーーーーーーーーーーーーーーーーーーー
        taken_subject_ids = []
        append = taken_subject_ids.append
        for i in taken:
            taken_subject_id = i.subject_id
            append(taken_subject_id)
        
        kadais = []
        extend = kadais.extend
        for i in taken_subject_ids:
            kadai = Task.query.filter_by(subject_id = i).all()  
            extend(kadai)
        tasks = []
        today_serial = get_int_serial()
        for task in kadais:
            serial = task.serial
            if serial >= today_serial:
                subject:Subject = Subject.query.filter_by(id=task.subject_id).one()
                tasks += [
                    {
                        "subject_id":subject.id,
                        "subject_name": subject.subject_name,
                        "task_id": task.id,
                        "deadline_year":(datetime(1899,12,30) + timedelta(task.serial)).strftime('%Y'),
                        "deadline_month":(datetime(1899,12,30) + timedelta(task.serial)).strftime('%m'),
                        "deadline_day":(datetime(1899,12,30) + timedelta(task.serial)).strftime('%d'),
                        "summary": task.summary,
                        "detail": task.detail,
                        "difficulty":task.difficulty
                    }
                ]  
         
        #all_tasks_idとhard_tasks_idの振り分け
        all_tasks_id, hard_tasks_id = [],[]
        today_serial = get_int_serial()
        for kadai in kadais:
            serial = kadai.serial
            if serial >= today_serial:#期限が終わっていない
                if today_serial+3 >= serial:#期限が三日以内である
                    all_tasks_id.append(kadai.id)
                    hard_tasks_id.append(kadai.id)
                else:#期限が三日以内でない
                    all_tasks_id.append(kadai.id)
                    if kadai.difficulty == 5:#期限は三日以内でないが大変さが5である
                        hard_tasks_id.append(kadai.id)
                        
        data = {
            "display_ok":display_ok,
            "visible_limit":iso_visible_limit,
            "all_tasks_id": all_tasks_id,
            "hard_tasks_id": hard_tasks_id,
            "tasks": tasks
        } 
        return make_response(1,data)

@app.route("/api/user/getInfo", methods=["GET"])
@login_required
@expel_frozen_account
def getinfo():
    user = current_user
    s:Gakka = Gakka.query.filter_by(id = user.department_id).one()
    task_regists = Task_regist.query.filter_by(user_id=user.id).all()
    regist_time = []
    for task_regist in task_regists:
        regist_time.append(task_regist.regist_time)
    if regist_time != []:
        recent_regist_time: float = max(regist_time)
        iso_visible_limit = serial_to_iso(recent_regist_time + 3,is_basic_format = False)
    else:
        iso_visible_limit = None
    data = {
        "username":user.username,
        "department":s.gakka,
        "department_id":user.department_id,
        "mail":user.mail,
        "iso_visible_limit":iso_visible_limit
    }
    return make_response(1,data)

#! ログアウト機能(get)
@app.route("/api/logout", methods=["GET"])
@login_required
@expel_frozen_account
def logout():
    if request.method == "GET":
        logout_user()  # セッション情報の削除  #? 変更となる可能性あり
        return make_response()
    
@app.route("/api/login", methods=["POST"])
def login():
    if request.method == "POST":
        json_data = request.get_json()
        try:
            data = json_data["data"]
            username = data["username"]
            password = data["password"]
        except:
            return make_response(2)
        can_login,user = is_strict_login_possible(username,password)
        if can_login:
            login_user(user,remember=True) 
            return make_response()
        else:
            return make_response(101)
        
@app.route("/unlogin", methods=["GET"])
def unlogin():
    return make_response(4)
            
if __name__=='__main__':
    app.run(debug=True, threaded=True)
