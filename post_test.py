import requests
import json

# テスト方法:
# url, json_data を適した値にする。
# app.py を実行中に (別のデスクトップで post_test.py を vscord から開いて立ち上げた) 新たなターミナルで post_test.py を実行

#POST先URL
url = "http://127.0.0.1:5000/api/taken"

#JSON形式のデータ(リクエスト用)
json_data = {
            "id":[]
        }    

#POST送信(Test)
response = requests.post(
    url,
    json = json.dumps(json_data)    #dataを指定する
    )

res_data = response.json()
print(res_data)
