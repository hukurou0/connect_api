from  datetime import datetime
from time import time
import uuid
from flask import current_app
from flask import request, redirect, url_for, jsonify
from sqlalchemy import exc, func
from werkzeug.security import generate_password_hash, check_password_hash
from database_defined import User_login
from pack_datetime_unixtime_serial import round_datetime_ut
#from flask_cors import CORS
from database_defined import app, db
from database_defined import (User, Login_limiter, Gakka, Subject, Taken, 
                               Task, Old_task, Task_regist)
from typing import Union
from pack_datetime_unixtime_serial import (get_int_serial, serial_to_iso, 
                                           trans_datetime_serial, trans_datetime_ut, 
                                           trans_ut_iso, ut_to_str, get_jst_datetime)
from pack_decorater import  QueueOption,  multiple_control, current_user_need_not_login
from pack_datetime_unixtime_serial import TimeBase
import traceback
from psycopg2 import errors as psycopg2_errors
from pack_func import create_task_entity,create_task_entity_in_apitaskgetTasks
import secret
from cryptography.fernet import Fernet

#必要な準備
ctx = app.app_context()
ctx.push()
app = current_app
#CORS(app)

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

def get_user(json_data):
    user_id:str = json_data["user_id"]
    if user_id == None:
        return None
    key = secret.SECRET_KEY.FERNET_KEY
    f = Fernet(key.encode('utf-8'))
    token = user_id.encode('utf-8')
    id = int(f.decrypt(token).decode('utf-8')) 
    user = User.query.filter_by(id = id).one_or_none()
    if user is not None: 
        if(user.login_possible==0):
            return None
    else:
        return None
    return user

# レスポンスの雛形
def make_response(status_code:int = 1, data:dict ={}):
    response_dic = {} 
    response_dic["status_code"] = status_code
    response_dic["data"] = data
    response = jsonify(response_dic)
    return response

# ログイン試行回数によるログイン制御
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
        return False, None
    login_limiter = Login_limiter.query.filter_by(user_id=user.id, is_stopped_access=True).all()
    # login_limmiter リストが空でないとき かつ ログイン制限時間中でないとき (短絡評価のため login_limiter リストは空でも良い)
    if(login_limiter and time() < login_limiter[-1].login_ut + TimeBase.stop_duration):
        if(is_update_restriction): 
            l = Login_limiter(user_id=user.id, is_stopped_access=True)
            db.session.add(l)
            db.session.commit()
        return False, None
    # ログイン未制限中 かつ ログイン成功時
    elif(check_password_hash(user.password, password)):
        user_login = User_login.query.filter_by(user_id=user.id, is_successful=1).one_or_none()
        if(user_login is None):
            user_login = User_login(user_id=user.id, is_successful=1)
            db.session.add(user_login)
            db.session.commit()
        else:
            user_login.login_ut = time()
            user_login.login_datetime=round_datetime_ut(get_jst_datetime())
            db.session.commit()
        return True, user
    else:
        add_user_login = lambda: [
            db.session.add(User_login(user_id=user.id, is_successful=0)),
            db.session.commit()
        ]
        add_user_login()
        login_fails_by_user = Login_limiter.query.filter(Login_limiter.user_id == user.id, \
                                                         TimeBase.focus_lower_limit_ut < Login_limiter.login_ut).all()
        # 罰点(ログイン失敗回数)が規定回数以上になった場合
        if(len(login_fails_by_user) - 1 > TimeBase.access_maximum_limit):
            l_l = Login_limiter(user_id=user.id, is_stopped_access=True)
        else: 
            l_l = Login_limiter(user_id=user.id) 
        db.session.add(l_l)
        db.session.commit()
        return False, None

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
                        department_id = department_id)
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
        
            

# 所属学科変更機能(post) --Unit Tested
@app.route("/api/user/modifyDepartment", methods=["POST"])
def modify_user():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
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

    return make_response()       

# 履修登録機能(get) --Unit Tested
@app.route("/api/taken/getSubjects", methods=["POST"])
def getSubjet():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    days = ['mon','tue','wed','thu','fri']
    periods = ['1','2','3','4','5']
    # taken_subject の id 検索のために定義. 履修科目IDを要素として持つ配列.
    now_taken_subject_ids = [t.subject_id for t in Taken.query.filter_by(user_id = user.id).all()]
    data = {}
    all_subjects = Subject.query.filter_by(department_id = user.department_id).all()#queryの回数を減らすためにfor文の外で一度だけ実行
    def subject_filter(all_subjects,period,day):#dayとperiodが一致するものをfilter
        subjects = []
        for subject in all_subjects:
            if subject.period == int(period):
                if subject.day == day:
                    subjects.append(subject)
        return subjects
    for period in periods:
        for day in days:
                # その曜日時限の科目一覧
            subjects = subject_filter(all_subjects,period,day)#データベースから取得したすべての科目からdayとperiodが一致するものを取得
            taken_id_set = {s.id for s in subjects} & set(now_taken_subject_ids)
            taken_id = 0 if(len(taken_id_set) == 0) else  taken_id_set.pop() # その曜日時限の履修科目ID
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
def taken():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
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

# 課題登録機能_段階1(post1) --Unit Tested
@app.route("/api/task/regist/getSubjects", methods=["POST"])
def taskRegistGetSubject():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    takens_ =  Taken.query.filter_by(user_id = user.id).all()
    takens = []
    for t in takens_:
        subject = Subject.query.filter_by(id=t.subject_id).one()    
        takens += [
            {"name": subject.subject_name, "subject_id": t.subject_id}
        ]
    data = takens
    return make_response(1,data)

# 課題登録機能_段階1(post2) --Unit Tested
@app.route("/api/task/regist/check", methods=["POST"])
def taskRegistCheck():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
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
    deadline_datetime = trans_datetime_serial(deadline_serial)
    deadline_ut = trans_datetime_ut(deadline_datetime)
    tasks = Task.query.filter_by(subject_id=subject_id, deadline_ut=deadline_ut).all()
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
def taskRegistDuplication():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    try:
        data = json_data["data"]
        task_id = data["task_id"]
    except:
        return make_response(2)
    
    task_regist = Task_regist(user_id=user.id, task_id=task_id, kind_id=1) 
    try:
        session = db.session
        session.add(task_regist)
        session.commit()
        return make_response() #make_response->finaly->returnの順に処理される
    except:
        session.rollback()
        return make_response(3) 
    
        
        

# 課題登録機能_段階2(post2) --Unit Tested
@app.route("/api/task/regist/new", methods=["POST"])
def taskRegistNew():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
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
    deadline_serial = get_int_serial(deadline_year, deadline_month, deadline_day)
    deadline_datetime = trans_datetime_serial(deadline_serial)
    deadline_ut = trans_datetime_ut(deadline_datetime)
    task_data = [user.id, subject_id, detail, summary, deadline_ut, difficulty]
    task_regist_data = [user.id, 1]
    @multiple_control(QueueOption.singleQueue)  # 悲観ロック
    def add_Task_and_Task_regist(task_data_:list, task_regist_data_:list):
        t, r = task_data_, task_regist_data_
        task = Task(user_id=t[0], subject_id=t[1], detail=t[2], summary=t[3], deadline_ut=t[4], difficulty=t[5])
        db.session.add(task)
        db.session.commit()
        task_id = db.session.query(func.max(Task.id)).one()[0]  
        task_regist = Task_regist(user_id=r[0], task_id=task_id, kind_id=r[1])
        db.session.add(task_regist)
        db.session.commit()
    add_Task_and_Task_regist(task_data, task_regist_data)
    return make_response()

# 課題削除機能(post1) --Unit Tested
@app.route("/api/user/getTasks", methods=["POST"])
def taskGetTasks():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    tasks:list = Task.query.filter_by(user_id=user.id).all()
    tasks_list = create_task_entity(tasks)
    data = {
        "tasks" : tasks_list
    }
    return make_response(1, data)

# 課題削除機能(post2) --Unit Tested
@app.route("/api/user/deleteTask", methods=["POST"])
def taskDelete():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    try:
        data = json_data["data"]
        task_id = data["task_id"]
    except:
        return make_response(2)
    task:Task = Task.query.filter_by(id=task_id).first()#TaskテーブルからOldTaskテーブルに移すことで削除とする。
    old_task = Old_task(task_id = task.id,user_id = task.user_id,subject_id = task.subject_id,detail = task.detail,summary = task.summary,deadline_ut = task.deadline_ut)
    task_regist = Task_regist(user_id=user.id, task_id=task_id, kind_id=5)#Task_registテーブルにログを残す。
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

             
    
# 課題表示機能(post) --Unit Tested
@app.route("/api/task/getTasks", methods=["POST"])
def taskGetTask():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
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
        regist_time.append(task_regist.regist_ut)
    if regist_time != []:
        recent_regist_ut: float = max(regist_time)
        #! 表示期限を示すシリアル値をiso8601に変換
        iso_visible_limit = trans_ut_iso(recent_regist_ut + TimeBase.access_maximum_limit,is_basic_format = False)
        now_ut = time()
        if now_ut >= recent_regist_ut + TimeBase.access_maximum_limit:
            __ = {"task_regist":False}
        else:
            __ = {"task_regist":True}
    else:
        iso_visible_limit = None
        __ = {"task_regist":False}   
           
    #課題表示出来るかの確認ー("display_ok"作成)ーーーーーーーーーーーーーーーー
    display_ok = {}
    display_ok.update(**_, **__)

    
    
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
    now_ut = time()
    for task in kadais:
        deadline_ut = task.deadline_ut
        if deadline_ut >= now_ut:
            subject:Subject = Subject.query.filter_by(id=task.subject_id).one()
            deadline_str = ut_to_str(task.deadline_ut)
            tasks += [
                {
                    "subject_id":subject.id,
                    "subject_name": subject.subject_name,
                    "task_id": task.id,
                    "deadline_year":deadline_str[0:4],
                    "deadline_month":deadline_str[5:7],
                    "deadline_day":deadline_str[8:10],
                    "summary": task.summary,
                    "detail": task.detail,
                    "difficulty":task.difficulty
                }
            ]  
        
    #all_tasks_idとhard_tasks_idの振り分け
    all_tasks_id, hard_tasks_id = [],[]
    now_ut = time()
    for kadai in kadais:
        deadline_ut = kadai.deadline_ut
        if deadline_ut >= now_ut:#期限が終わっていない
            if now_ut + TimeBase.access_maximum_limit >= deadline_ut:#期限が三日以内である
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

# ログインユーザの情報を返す(post)
@app.route("/api/user/getInfo", methods=["POST"])
def getinfo():
    json_data = request.get_json()
    user = get_user(json_data)
    if user is None: 
        return make_response(4)
    s:Gakka = Gakka.query.filter_by(id = user.department_id).one()
    task_regists = Task_regist.query.filter_by(user_id=user.id).all()
    regist_ut = []
    for task_regist in task_regists:
        regist_ut.append(task_regist.regist_ut)
    if regist_ut != []:
        recent_regist_ut: int = max(regist_ut)
        iso_visible_limit = trans_ut_iso(recent_regist_ut + TimeBase.access_maximum_limit,is_basic_format = False)
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

# ログイン機能(post)
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
            id = user.id
            key = secret.SECRET_KEY.FERNET_KEY
            f = Fernet(key.encode('utf-8'))
            token = f.encrypt(f"{id}".encode('utf-8'))
            data = {
                "user_id":token.decode('utf-8')
            }       
            return make_response(1,data)
        else:
            return make_response(101)

# ログイン排除(post)    
@app.route("/unlogin", methods=["GET"])
def unlogin():
    return make_response(4)

@app.route("/api/user/deleteuser", methods=["POST"])
def deleteUser():
    dummy = "$DUMMY"
    # uuid を取得
    namespace = uuid.NAMESPACE_URL
    name = 'https://www.examplejageiwiDFEIUF7932NFEIO8.com'  # テキトーな文字列
    uuid5 = uuid.uuid5(namespace, name)
    # dummy化関数
    DUMMYFUNC = lambda user: [
        setattr(user, "username", fr"{dummy}_USERNAME_{uuid5}"),
        setattr(user, "password", fr"{dummy}_PASSWORD_{uuid5}"),
        setattr(user, "mail", fr"{dummy}_MAIL_{uuid5}"),
        setattr(user, "login_possible", 0),
        db.session.commit()
    ]
    if request.method == "POST":
        json_data = request.get_json()
        try:
            user = get_user(json_data)
        except:
            return make_response(2)
        DUMMYFUNC(user)
        return make_response()

            
if __name__=='__main__':
    app.run(debug=True, threaded=True)
