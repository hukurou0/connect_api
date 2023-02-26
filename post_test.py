import requests
import json

#POST先URL
url = "http://127.0.0.1:5000/api/signup"

#JSON形式のデータ
json_data = {
            "username":"aa",
            "password":"aa",
            "department":"1",
        }    

#POST送信(Test)
response = requests.post(
    url,
    json = json.dumps(json_data)    #dataを指定する
    )

res_data = response.json()
print(res_data)