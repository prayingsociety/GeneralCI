import http.client
import json


def get_response(api_key, model, content):
    conn = http.client.HTTPSConnection("")
    payload = json.dumps({
       "model": model,
       "messages": [
          {
             "role": "user",
             "content": content
          }
       ]
    })
    headers = {
       'Authorization': api_key,
       'User-Agent': '',
       'Content-Type': ''
    }
    conn.request("POST", "", payload, headers)
    res = conn.getresponse()
    res_dict = json.loads(res.read().decode('utf-8'))

    return res_dict
