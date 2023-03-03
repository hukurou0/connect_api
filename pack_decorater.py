from queue import Queue
from time import time
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user, logout_user
from flask import current_app
from database_defined import db, User, Admin
from pack_datetime_unixtime_serial import TimeBase


# 多重実行用のキュー
class QueueOption:
    singleQueue = Queue(maxsize=1)  # 最大同接数: 1

# 多重実行(排他)制御の関数デコレータ (悲観ロック)
def multiple_control(q: Queue):              # FIFO
    def _multiple_control(f):                # f は関数
        @wraps(f)
        def _wrapper(*args,**kwargs):
            q.put(time())                    # キューの中身を1つtime()で埋める
            result = f(*args,**kwargs)
            q.get()                          # キューを空(中身を削除)にする
            q.task_done()                    # タスク完了の通知
            return result
        return _wrapper                      
    return _multiple_control

# ユーザーIDが1のユーザーを返す (単体テスト用, ログイン不必要)
def current_user_need_not_login() -> None | User:
    # return  #!本番環境用   
    current_user_ = User.query.filter_by(id=1).one()
    return current_user_  

# 未ログイン者を弾く関数デコレータ. flask_login モジュールのものと全く同じ. 渡す値のみの記述ゆえここだけではcookieに関わらない.
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        return f(*args, **kwargs)  #! テスト環境用
        if current_app.login_manager._login_disabled:
            return f(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)
    return decorated_view
    
# 凍結アカウントを弾く関数デコレータ
def expel_frozen_account(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        return f(*args, **kwargs)  #! テスト環境用
        adminU = current_user
        if(adminU.login_possible==0):
            return redirect(url_for("freeze"))
        else:
            return f(*args, **kwargs)
    return _wrapper

# 管理者以外(arg=False)または管理者2(arg=True)以外を弾く関数デコレータ
def expel_not_admin(storng_restriction: bool = False):  # 引数は1つまで指定可能故、一つ下の階層の関数の引数を関数とする
    def _expel_not_admin(f):                            # 型ヒントのためのfunctionクラスは使用不可(Error). ここより下の関数階層構造は通常(関数引数)デコレータに準ず
        @wraps(f)                                       # テストを可能に
        def _wrapper(*args, **kwargs):                  # *args: 可変長タプル型引数, **kwargs: 可変長辞書型引数
            # return f(*args, **kwargs)  #! テスト環境用
            adminU = current_user
            adminA = Admin.query.filter_by(user_id=adminU.id).one_or_none()
            if(adminA is None):
                return redirect(url_for("signup"))
            elif(adminA.privilege==1 and not storng_restriction):
                f(*args, **kwargs)
                return redirect(url_for("admin_login1"))
            elif(adminA.privilege==2):
                return f(*args, **kwargs)
        return _wrapper                                 # 関数実行 g() を返すのではなく 関数ポインタ g を返す  
    return _expel_not_admin                             # 同上

# クリエイトモードでない場合
def expel_not_create_mode(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        admin2s = Admin.query.filter_by(privilege=2).all()
        is_opened = False
        for admin in admin2s:
            if(admin.create_mode==1):
                is_opened = True  
                break
        if(is_opened):
            return f(*args, **kwargs)
        else:
            return redirect(url_for("signup"))
    return _wrapper

# 時間ベースのログアウト
def logout_by_time_out(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        adminU = current_user
        adminA = Admin.query.filter_by(user_id=adminU.id).one_or_none()
        if(adminA.lastlogin_ut < TimeBase.now_minus_login_valid_ut):
            logout_user()
            if(adminA is None):
                return redirect(url_for("signup"))
            elif(adminA.privilege==1 or adminA.privilege==2):
                return redirect(url_for("admin_login1"))  
            else:
                return redirect(url_for("signup"))
        elif():
            adminA.lastlogin_ut = time()
            db.session.commit()
            return f(*args, **kwargs)
    return _wrapper



#*----------------------------------((解説))-------------------------------------------*#
# ((cf.)) **kwrags の本質(*argsの要素に辞書を格納する方法では補完できない理由)
# https://noauto-nolife.com/post/django-args-kwargs/#:~:text=%E7%B5%90%E8%AB%96%E3%81%8B%E3%82%89%E8%A8%80%E3%81%86%E3%81%A8%E3%80%81%20%2Aargs,%E3%81%AF%E3%82%AD%E3%83%BC%E3%83%AF%E3%83%BC%E3%83%89%E6%9C%AA%E6%8C%87%E5%AE%9A%E3%81%AE%E5%BC%95%E6%95%B0%E3%81%AE%E3%83%AA%E3%82%B9%E3%83%88%E3%80%81%20%2A%2Akwargs%20%E3%81%AF%E3%82%AD%E3%83%BC%E3%83%AF%E3%83%BC%E3%83%89%E3%81%8C%E6%8C%87%E5%AE%9A%E3%81%95%E3%82%8C%E3%81%9F%E5%BC%95%E6%95%B0%E3%81%AE%E8%BE%9E%E6%9B%B8%E3%82%92%E6%89%8B%E3%81%AB%E5%85%A5%E3%82%8C%E3%82%8B%E3%81%9F%E3%82%81%E3%81%AE%E3%82%82%E3%81%AE%E3%81%A7%E3%81%82%E3%82%8B%E3%80%82
# 関数デコレータは先に宣言したものから作用されていく (@f1; @f2; f(); ⇔ f1∘f2∘f();)
""" 
@app.route("/admin", methods=["GET", "POST"])   # ルーティング修飾
@login_required                                 # current_userを取得する((依存元@1: ログイン者のuser_id取得のため))
@logout_by_time_out                             # 時間経過状況によりログアウト((依存先@1))((依存元@2))
@login_required                                 # ログアウトしているならば制限する((依存先@2))
@expel_not_admin()                              # 管理者を弾く関数修飾((依存先@1)). 引数が関数でないため "()" をつける. 
def admin_top():                                # 装飾先関数
    processing                                  # 処理内容
"""