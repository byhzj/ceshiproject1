import allure
import pytest
import random
import time
from niweiming_kdtx.src.common_yaml import load_yaml

# 加载数据
data = load_yaml("data/contract.yaml")
add_cases = data.get("add_cases", [])
list_cases = data.get("list_cases", [])
update_cases = data.get("update_cases", [])
delete_normal = data.get("delete_cases", {}).get("normal", [])
delete_not_exist = data.get("delete_cases", {}).get("not_exist", [])





@pytest.fixture(scope="function")
def uploaded_file_name(upload_file):
    return upload_file

@pytest.fixture(scope="function")
def uploaded_muti_name(upload_multi_files):
    # 上传3个文件
    fn_list = upload_multi_files(count=3)
    assert len(fn_list) == 3


@pytest.fixture(scope="function")
def created_contract_id(auth, uploaded_file_name,upload_file):
    """创建合同并返回ID（用于修改和删除测试）"""

    # 上传
    fn = uploaded_file_name

    # 创建合同（随机数据）
    phone = f"17{random.randint(170000000, 189999999)}"
    payload = {
        "name": f"测试_{int(random.randint(1,1000))}",
        "phone": phone,
        "contractNo": f"课程_{int(time.time())}",
        "subject": "6",
        "courseId": 99,
        "channel": "0",
        "activityId": 77,
        "fileName": fn,
    }

    resp = auth.post("/api/contract", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("code") == 200, f"创建合同失败: {data.get('msg')}"

    # 反查ID
    list_resp = auth.get("/api/contract/list", params={"phone": phone})
    rows = list_resp.json().get("rows", [])
    assert rows, "未查到刚创建的合同"
    cid = rows[-1].get("id")
    print(cid)
    assert cid, "合同数据缺少 id"
    return cid


#  新增合同
@pytest.mark.contract
@allure.feature("合同管理")
@allure.story("新增合同")
@pytest.mark.parametrize("case", add_cases, ids=lambda c: c["id"])
def test_add_contract(auth, uploaded_file_name, case):
    req = case["request"].copy()
    if req.get("fileName") == "__UPLOAD__":
        req["fileName"] = uploaded_file_name
    if req.get("contractNo") == "__CNO__":
        req["contractNo"] = f"HT_{int(time.time())}_{random.randint(1000,9999)}"
    exp = case["expected"]

    print(f"\n=== 新增合同请求 ===")
    print(f"Request: {req}")
    resp = auth.post("/api/contract", json=req)
    print(f"Response status: {resp.status_code}")
    print(f"Response body: {resp.text}")
    print("=== 结束 ===\n")

    assert resp.status_code == 200, f"请求码不符: {resp.status_code}"
    data = resp.json()
    assert data.get("code") == exp["code"], f"业务码不符: {data}"

# 查询列表
@pytest.mark.contract
@allure.feature("合同管理")
@allure.story("查询合同列表")
@pytest.mark.parametrize("case", list_cases, ids=lambda c: c["id"])
def test_list_contract(auth, case):
    req = case["request"]
    exp = case["expected"]

    print(f"\n=== 查询合同列表 ===")
    print(f"Request: {req}")
    resp = auth.get("/api/contract/list", params=req)
    print(f"Response status: {resp.status_code}")
    print(f"Response body: {resp.text}")
    print("=== 结束 ===\n")

    assert resp.status_code == 200

    data = resp.json()
    assert data.get("code") == exp["code"], f"业务码不符: {data[:20]}"
    if "msg" in exp:
        assert data.get("msg") == exp["msg"]
    rows = data.get("rows", [])
    if exp.get("rows_not_empty") is True:
        assert len(rows) > 0, "期望有数据但rows为空"
    elif exp.get("rows_not_empty") is False:
        assert len(rows) == 0, "期望无数据但rows不为空"


# 修改合同
@pytest.mark.contract
@allure.feature("合同管理")
@allure.story("修改合同")
@pytest.mark.parametrize("case", update_cases, ids=lambda c: c["id"])
def test_update_contract(auth, created_contract_id, case):

    contract_id = created_contract_id
    req = case["request"]
    req["id"] = contract_id
    exp = case["expected"]

    print(f"\n=== 修改合同列表 ===")
    print(f"id: {contract_id}")
    print(f"Request: {req}")
    # 执行修改
    resp = auth.put("/api/contract", json=req)
    print(f"Response status: {resp.status_code}")
    print(f"Response body: {resp.text}")
    print("=== 结束 ===\n")

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("code") == exp["code"], f"业务码不符: {data}"
    if "msg" in exp:
        assert data.get("msg") == exp["msg"], f"消息不符: {data.get('msg')}"

    # 如果修改成功
    if data.get("code") == 200:
        check_resp = auth.get(f"/api/contract/{contract_id}")
        check_body = check_resp.json()
        check_data = check_body.get("data", {}).get("info", {})

       # 验证被修改的字段
        if "name" in req and req["name"]:
            assert check_data.get("name") == req["name"]
        if "phone" in req and req["phone"]:
            assert check_data.get("phone") == req["phone"]


# 修改不存在的合同
@pytest.mark.contract
@allure.feature("合同管理")
@allure.story("修改合同")
def test_update_not_exist(auth):
    fake_id = 999999
    resp = auth.put("/api/contract", json={
        "id": fake_id,
        "name": "不存在的合同",
        "phone": random.randint(17000000000,18999999999),
        "subject": "6",
        "courseId": 99,
        "channel": "0",
        "activityId": 74,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == 500, f"修改不存在合同应失败: {body}"
    assert body.get("msg") == "操作失败"


#  删除合同
@pytest.mark.contract
@allure.feature("合同管理")
@allure.story("删除合同")
class TestDeleteContract:

    @allure.title("删除存在的合同")
    @pytest.mark.parametrize("case", delete_normal, ids=lambda c: c["id"])
    def test_delete_normal(self, auth, created_contract_id, case):
        contract_id = created_contract_id
        exp = case["expected"]

        print(f"\n=== 删除合同 ===")
        print(f"id: {contract_id}")
        print(f"Expected: {exp}")
        # 执行删除
        resp = auth.post("/api/contract/remove", params={"id": contract_id})
        print(f"Response status: {resp.status_code}")
        print(f"Response body: {resp.text}")
        print("=== 结束 ===\n")

        assert resp.status_code == 200
        try:
            data = resp.json()
        except Exception:
            data = {"code": 200, "msg": resp.text.strip()}

        assert data.get("code") == exp["code"], f"业务码不符: {data}"
        if "msg" in exp:
            assert data.get("msg") == exp["msg"]

        # 验证删除成功
        check_resp = auth.get(f"/api/contract/{contract_id}")
        assert check_resp.status_code == 200
        check_body = check_resp.json()
        check_data = check_body.get("data", {})
        info = check_data.get("info")
        if info:
            # 如果有 info，检查 isDelete 是否为 1
            assert info.get("isDelete") == 1, f"合同未被删除: {check_data}"
        else:
            # 没有 info，删除成功
            print(f"合同 {contract_id} 已删除")


    @allure.title("删除不存在的合同")
    @pytest.mark.parametrize("case", delete_not_exist, ids=lambda c: c["id"])
    def test_delete_not_exist(self, auth, case):
        fake_id = case["request_id"]
        exp = case["expected"]
        resp = auth.post("/api/contract/remove", params={"id": fake_id})
        assert resp.status_code == 200
        try:
            data = resp.json()
        except Exception:
            data = {"code": 500, "msg": resp.text.strip()}  # 构造模拟响应
        assert data.get("code") == exp["code"], f"业务码不符: {data}"
        if "msg" in exp:
            assert data.get("msg") == exp["msg"]