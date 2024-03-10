import requests

GRANT_TYPE = "~~~~~~~~~~~"
CLIENT_ID = "~~~~~~~~~~~~"
REDIRECT_URL = "https://swart.run.goorm.site/login"

ACCESS_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
USER_INFOMATION_URL = "https://kapi.kakao.com/v2/user/me"


def cert(code):
  DATA1 = {
      "grant_type": GRANT_TYPE,
      "client_id": CLIENT_ID,
      "redirect_uri": REDIRECT_URL,
      "code": code
  }
  raw_token = requests.post(ACCESS_TOKEN_URL, data=DATA1)

  access_token = raw_token.json()['access_token']
  DATA2 = {"Authorization": "Bearer " + access_token}
  return requests.get(USER_INFOMATION_URL,
                      headers=DATA2).json()['kakao_account']
