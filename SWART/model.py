import requests
import json

def conn(query):

  response = requests.post(
      "~~~~~~~~~~~~~~~",
      data={"query": query})
  print(response.status_code)
  return json.loads(response.text)
