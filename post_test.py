import requests
import json

# テスト方法: url, json_data を適した値にし、app.py を実行中に新たなターミナル (別のデスクトップを立ち上げても良い) で post_test.py を実行.
# requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0) の エラーは json 由来ではなく、app.py側のエラーも参照.
# => 全然見通しがつかない場合は、GETメソッドにするとエラー名が具体的になる可能性がある (但し、GETメソッドをPOSTメソッドに直すなどの後処理を忘れないように).


# POST先URL
url = "http://127.0.0.1:5000/api/signup"

#JSON形式のデータ(リクエスト用). 変数json_dataの格納値にドキュメントの {"data": data_value } (全て)をコピペする.
json_data = {
	"data": {
		"username": "khao",
		"password": "adaa",
		"department":1,
	}
}

#POST送信(Test)
response = requests.post(
    url,
    json = json_data    #dataを指定する
    )

res_data = response.json()
print(res_data)
