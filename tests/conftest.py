import pytest
from pathlib import Path
from src.common import Api
from src.common_yaml import load_yaml
import time
import functools

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# 遇到405和waf重试装饰器 ==========
def retry_on_405(max_retries=3, delay=2):
    """装饰器：对返回 405 的请求自动重试"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                response = func(*args, **kwargs)
                if response.status_code != 405:
                    return response
                print(f"[重试] 收到 405，第 {attempt+1} 次重试，等待 {delay}s")
                time.sleep(delay)
            return response  # 最后一次仍返回 405
        return wrapper
    return decorator

# 对 Api.captcha 方法应用重试
Api.captcha = retry_on_405()(Api.captcha)


@pytest.fixture(scope="function")
def anon_api():
    """未登录客户端，专门给验证码/登录用例用"""
    client = Api()
    yield client
    client.close()


@pytest.fixture(scope="function")
def captcha_client(anon_api):
    """获取验证码，返回 uuid"""
    response = anon_api.captcha()
    assert response is not None, "验证码请求失败"
    assert response.status_code == 200, f"验证码接口异常: {response.text}"
    data = response.json()
    uuid = data.get("uuid")
    assert uuid, "未获取到 uuid"
    return {"uuid": uuid}

@pytest.fixture(scope="function")
def token(anon_api, captcha_client):
    """登录并返回 token"""
    acc = load_yaml("data/auth.yaml")["account"]
    uuid = captcha_client["uuid"]
    response = anon_api.login(
        username=acc["username"],
        password=acc["password"],
        code=acc["code"],
        uuid=uuid,
    )
    assert response.status_code == 200, f"登录失败: {response.text}"
    body = response.json()
    assert body.get("code") == 200, f"登录业务失败: {body}"
    tk = body.get("token")
    assert tk, "未返回 token"
    return tk


@pytest.fixture(scope="function")
def auth(token):
    """带 token 的客户端"""
    client = Api(token=token)
    yield client
    client.close()

# 单个上传
@pytest.fixture(scope="function")
def upload_file(auth):
    """上传文件并返回 fileName"""
    file_path = PROJECT_ROOT / "sources" / "a.txt"

    # 确保文件非空
    if file_path.stat().st_size == 0:
        with open(str(file_path), "w") as f:
            f.write("test")

    url = auth.base_url.rstrip("/") + "/api/common/upload"

    # 保存原始 Content-Type，然后临时移除
    original_ct = auth.session.headers.pop("Content-Type", None)

    try:
        with open(str(file_path), "rb") as f:
            files = {"file": f}
            headers = dict(auth.headers)
            headers.pop("Content-Type", None)
            resp = auth.session.post(url, files=files, headers=headers)
    finally:
        # 恢复原始 Content-Type
        if original_ct:
            auth.session.headers["Content-Type"] = original_ct

    print(f"Upload response: {resp.status_code} {resp.text[:200]}...")
    assert resp.status_code == 200, f"HTTP请求失败: {resp.status_code} {resp.text}"
    data = resp.json()
    assert data.get("code") == 200, f"上传业务失败: {data}"
    fn = data.get("fileName", "")
    assert fn, "上传未返回 fileName"
    return fn

# 多个上传
@pytest.fixture(scope="function")
def upload_multi_files(auth):

    def multi_upload(count=2):
        # 准备多个文件
        file_paths = []
        for i in range(count):
            fp = PROJECT_ROOT / "sources" / f"a_{i}.txt"
            if not fp.exists() or fp.stat().st_size == 0:
                fp.write_text("test content")
            file_paths.append(fp)

        files = []
        for fp in file_paths:
            file_obj = open(fp, "rb")
            files.append(("file", (fp.name, file_obj, "text/plain")))

        url = auth.base_url.rstrip("/") + "/api/common/upload"
        original_ct = auth.session.headers.pop("Content-Type", None)
        try:
            headers = dict(auth.headers)
            headers.pop("Content-Type", None)
            resp = auth.session.post(url, files=files, headers=headers)
        finally:
            if original_ct:
                auth.session.headers["Content-Type"] = original_ct
            for _, ft in files:
                ft[1].close()

        assert resp.status_code == 200, f"HTTP请求失败: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("code") == 200, f"上传业务失败: {data}"
        raw = data.get("fileName", "")
        if isinstance(raw, list):
            return raw
        else:
            return [raw] if raw else []

    return multi_upload