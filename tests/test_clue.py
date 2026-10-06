import allure
import pytest
import random
from niweiming_kdtx.src.common_yaml import load_yaml

data = load_yaml("data/clue.yaml")
add_cases = data.get("add_cases", [])
list_cases = data.get("list_cases", [])
delete_normal = data.get("delete_cases", {}).get("normal", [])
delete_not_exist = data.get("delete_cases", {}).get("not_exist", [])
convert_cases = data.get("convert_cases", [])


def _find_clue_id(auth, phone):
    """根据手机号查询线索ID"""
    resp = auth.get("/api/clues/clue/list", params={"phone": phone})
    rows = resp.json().get("rows", [])
    return rows[-1]["id"] if rows else None


@pytest.fixture(scope="function")
def created_clue_id(auth):
    """创建一条正常线索，返回ID，测试结束后清理"""
    phone = f"{random.randint(17000000000, 18999999999)}"
    payload = {
        "activityId": "",
        "name": "临时线索",
        "phone": phone,
        "channel": "0",
        "sex": 0,
        "age": 20,
        "weixin": "wx111",
        "qq": ""
    }

    resp = auth.post("/api/clues/clue", json=payload)
    assert resp.json().get("code") == 200, "创建线索失败"
    clue_id = _find_clue_id(auth, phone)
    assert clue_id is not None, "无法获取新创建的线索ID"
    yield clue_id
    # 删除
    auth.put(f"/api/clues/clue/false/{clue_id}", json={"reason": "2", "remark": "清理"})

@pytest.mark.clue
class TestClueAdd:


    @allure.feature("线索管理")
    @allure.story("线索添加")
    @allure.title("线索添加用例")
    @pytest.mark.parametrize("case", add_cases, ids=lambda c: c["id"])
    def test_add(self, auth, case):
        req = case["request"]
        exp = case["expected"]
        if req.get("phone") == "__PHONE__":
            req["phone"] = str(random.randint(17000000000, 18999999999))

        print(f"\n=== 查询合同列表 ===")
        print(f"Request: {req}")
        resp = auth.post("/api/clues/clue", json=req)
        print(f"Response status: {resp.status_code}")
        print(f"Response body: {resp.text}")
        print("=== 结束 ===\n")

        assert resp.status_code == 200
        data = resp.json()

        print(f"ccc{data}")

        assert data.get("code") == exp["code"], f"业务码不符: {data}"
        if "msg" in exp:
            assert data.get("msg") == exp["msg"]

@pytest.mark.clue
class TestClueList:
    @allure.feature("线索管理")
    @allure.story("线索查询")
    @allure.title("线索查询用例")
    @pytest.mark.parametrize("case", list_cases, ids=lambda c: c["id"])
    def test_list(self, auth, case):
        # 如果是按ID查询
        if case.get("request_id") == "__DYNAMIC__":
            # 使用固定手机号
            phone = "18995235291"
            clue_id = _find_clue_id(auth, phone)
            if not clue_id:
                pytest.skip("未找到可用线索，跳过本用例")
            params = {"id": clue_id}
        else:
            params = case["request"]

        resp = auth.get("/api/clues/clue/list", params=params)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == case["expected"]["code"], f"业务码不符: {data}"
        assert data.get("msg") == case["expected"]["msg"]
        # rows 是否为空
        if "rows_not_empty" in case["expected"]:
            rows = data.get("rows", [])
            if case["expected"]["rows_not_empty"]:
                assert len(rows) > 0, "期望有数据但返回为空"
            else:
                assert len(rows) == 0, "期望无数据但返回了数据"

@pytest.mark.clue
class TestClueDelete:
    @allure.feature("线索管理")
    @allure.story("线索删除")
    @allure.title("线索删除用例")
    @pytest.mark.parametrize("case", delete_normal, ids=lambda c: c["id"])
    def test_delete_normal(self, auth, created_clue_id, case):

        clue_id = case.get("request_id",created_clue_id)
        req = case["request"]
        exp = case["expected"]
        resp = auth.put(f"/api/clues/clue/false/{clue_id}", json=req)

        assert resp.status_code == 200
        data = resp.json()

        assert data.get("code") == exp["code"], f"业务码不符: {data}"
        if "msg" in exp and exp["msg"] is not None:
            assert data.get("msg") == exp["msg"]

@pytest.mark.clue
class TestClueConvert:
    @allure.feature("线索管理")
    @allure.story("线索转商机")
    @allure.title("线索转商机用例")
    def test_convert(self, auth, created_clue_id):

        resp = auth.put(f"/api/clues/clue/changeBusiness/{created_clue_id}")
        assert resp.status_code == 200
        data = resp.json()
        print(f"响应: {data}")
        assert data.get("code") == 200, f"业务码不符: {data}"
        assert data.get("msg") == "操作成功"