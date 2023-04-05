from flask import current_app
from database_defined import app, db
from database_defined import (User, Admin, User_login, Login_limiter, Gakka, Subject, Taken, 
                               Task, Old_task, Task_regist, Task_regist_kind)
from datetime import datetime, date, timedelta
from pack_datetime_unixtime_serial import get_int_serial, serial_to_str, ut_to_str

ctx = app.app_context()
ctx.push()
app = current_app

#TaskレコードのリストからTaskEntityのリストを生成し返す関数
def create_task_entity(tasks:list):
    tasks_list = []
    for task in tasks:
        subject:Subject = Subject.query.filter_by(id=task.subject_id).one()
        deadline_str = ut_to_str(task.deadline_ut)
        tasks_list += [
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
    return tasks_list
                