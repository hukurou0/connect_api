from flask import current_app
from database_defined import app, db
from database_defined import (User, Admin, User_login, Login_limiter, OTP_table, Gakka, Subject, Taken, 
                               Task, Old_task, Task_regist, Task_regist_kind)
from datetime import datetime, date, timedelta
from pack_datetime_unixtime_serial import get_float_serial, get_int_serial, serial_to_str

ctx = app.app_context()
ctx.push()
app = current_app

#TaskレコードのリストからTaskEntityのリストを生成し返す関数
def create_task_entity(tasks:list):
    tasks_list = []
    for task in tasks:
        subject:Subject = Subject.query.filter_by(id=task.subject_id).one()
        tasks_list += [
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
    return tasks_list
                