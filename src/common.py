import requests

BASE_URL = "https://kdtx-test.itheima.net"

class Api:

    def __init__(self, token=None, timeout=30):
        self.base_url = BASE_URL
        self.timeout = timeout
        self.session = requests.Session()

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0"
            ),
            "Content-Type": "application/json",
            "referer": "https://kdtx-test.itheima.net",
        }
        if token:
            self.set_token(token)

    def set_token(self, token):
        """设置 Authorization header"""
        auth_val = token if token.startswith("Bearer ") else f"Bearer {token}"
        self.headers["Authorization"] = auth_val
        self.session.headers["Authorization"] = auth_val

    def captcha(self):
        """获取验证码"""
        url = self.base_url + "/api/captchaImage"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            return response
        except requests.exceptions.RequestException as e:
            print(f"获取验证码请求失败: {e}")
            return None
        except ValueError as e:
            print(f"获取验证码返回数据失败: {e}")
            return None

    def login(self, username, password, code, uuid):
        """登录"""
        url = self.base_url + "/api/login"
        data = {
            "username": username,
            "password": password,
            "code": code,
            "uuid": uuid,
        }
        response = self.session.post(url, json=data, headers=self.headers)
        # 如果登录成功，自动保存 token
        try:
            body = response.json()
            token = body.get("token")
            if token:
                self.set_token(token)
        except Exception:
            pass
        return response

    def get(self, url, **kwargs):
        """通用 GET 方法"""
        full_url = self.base_url + url if not url.startswith("http") else url
        kwargs.setdefault("headers", self.headers)
        return self.session.get(full_url, **kwargs)

    def post(self, url, **kwargs):
        """通用 POST 方法"""
        full_url = self.base_url + url if not url.startswith("http") else url
        kwargs.setdefault("headers", self.headers)
        return self.session.post(full_url, **kwargs)

    def put(self, url, **kwargs):
        """通用 PUT 方法"""
        full_url = self.base_url + url if not url.startswith("http") else url
        kwargs.setdefault("headers", self.headers)
        return self.session.put(full_url, **kwargs)

    def delete(self, url, **kwargs):
        """通用 DELETE 方法"""
        full_url = self.base_url + url if not url.startswith("http") else url
        kwargs.setdefault("headers", self.headers)
        return self.session.delete(full_url, **kwargs)

    def close(self):
        self.session.close()