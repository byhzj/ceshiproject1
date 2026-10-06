import allure
import pytest
from src.common_yaml import load_yaml


@allure.feature("认证")
@allure.story("验证码")
@allure.title("验证码用例")
@pytest.mark.auth
@pytest.mark.smoke
def test_captcha(anon_api):
    """验证码接口获取 uuid 是否存在"""
    r = anon_api.captcha()
    assert r is not None, "请求失败"
    assert r.status_code == 200, f"状态码异常: {r.status_code}"
    body = r.json()
    assert body.get("code") == 200, f"业务码异常: {body}"
    assert body.get("uuid"), "未返回 uuid"


@allure.feature("认证")
@allure.story("登录")
@allure.title("登录用例")
@pytest.mark.auth
@pytest.mark.smoke
@pytest.mark.parametrize(
    "case",
    load_yaml("data/auth.yaml")["login_cases"],
    ids=lambda c: c["id"],
)
def test_login(anon_api, case):
    case_id = case["id"]
    desc = case["description"]
    req = case["request"]
    exp = case["expected"]

    print(f"\n执行用例：{case_id} - {desc}")

    # 处理 uuid
    if req.get("uuid_from") == "captcha":
        cap = anon_api.captcha()
        assert cap.status_code == 200
        uuid_val = cap.json().get("uuid", "")
    else:
        uuid_val = req.get("uuid_value", "")

    r = anon_api.login(
        username=req["username"],
        password=req["password"],
        code=req["code"],
        uuid=uuid_val,
    )
    # 断言状态码
    assert r is not None, f"请求失败：{case_id}"
    assert r.status_code == exp["status"], (
        f"HTTP状态码不符: {r.status_code}, body={r.text[:200]}"
    )
    data = r.json()
    print(f"响应数据：{data}")

    # 断言业务码
    assert data["code"] == exp["code"], (
        f"用例 {case_id} 失败：期望 code={exp["code"]}，实际 code={data['code']}"
    )
    # 断言消息
    if "msg" in exp:
        assert data.get("msg") == exp["msg"], (
            f"消息不符: {data.get('msg')} != {exp['msg']}"
        )