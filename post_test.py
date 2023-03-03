import requests
import json

# テスト方法:
# url, json_data を適した値にする。
# app.py を実行中に (別のデスクトップで post_test.py を vscord から開いて立ち上げた) 新たなターミナルで post_test.py を実行
# requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0) の エラーは大抵記述した処理部分がおかしい
# => 全然見通しがつかない場合は、GETメソッドにするとエラー名が具体的に(json由来のものでなく)なるので、オススメ
# 但し、GETメソッドをPOSTメソッドに直したりの後処理を忘れないように
# get_int_serial(..., today_month, ...), Task.user_num.

#POST先URL
url = "http://127.0.0.1:5000/api/task/delete"

#JSON形式のデータ(リクエスト用)
json_data = {
        "task_id":2
        }    

#POST送信(Test)
response = requests.post(
    url,
    json = json.dumps(json_data)    #dataを指定する
    )

res_data = response.json()
print(res_data)
