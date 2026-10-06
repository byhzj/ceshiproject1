import allure
import pytest
import time
import random
from src.common_yaml import load_yaml

# data = load_yaml("data/course.yaml")
# add_cases = data.get("add_cases", [])
# list_cases = data.get("list_cases", [])
# update_cases = data.get("update_cases", [])
# delete_normal = data.get("delete_cases", {}).get("normal", [])
# delete_not_exist = data.get("delete_cases", {}).get("not_exist", [])


@pytest.fixture(scope="function")
def created_course_id(auth):

    course_name = f"测试课程_{int(time.time())}"
    # 新增课程
    resp = auth.post("/api/clues/course", json={
        "name": course_name,
        "subject": "6",
        "price": 888,
        "applicablePerson": "2",
        "info": "创建测试课程"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == 200, f"创建课程失败: {body.get('msg')}"

    # 反查课程ID
    cid = body.get("id")
    if not cid:
        cid = _find_course_id(auth, course_name)
    assert cid, "无法获取创建课程ID"

    yield cid

    # 删除课程
    auth.delete(f"/api/clues/course/{cid}")

@pytest.mark.course
@allure.feature("课程管理")
@allure.story("新增课程")
@allure.title("新增课程用例")
@pytest.mark.parametrize("case", load_yaml("data/course.yaml")["add_cases"], ids=lambda x: x["id"])
def test_add_course(auth, case):
    req = case["request"]
    exp = case["expected"]
    resp = auth.post("/api/clues/course", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("code") == exp["code"], f"业务码不符: {data}"
    if "msg" in exp:
        assert data.get("msg") == exp["msg"], f"消息不符: {data.get('msg')}"


def _find_course_id(auth, name, subject=""):
    """通过名称和学科反查课程ID最后一条"""
    params = {"name": name}
    if subject:
        params["subject"] = subject
    r = auth.get("/api/clues/course/list", params=params)
    rows = r.json().get("rows", [])
    return rows[-1]["id"] if rows else None

@pytest.mark.course
@allure.feature("课程管理")
@allure.story("查询列表")
@allure.title("查询列表用例")
@pytest.mark.parametrize("case", load_yaml("data/course.yaml")["list_cases"], ids=lambda c: c["id"])
def test_list_course(auth, case):
    req = case["request"]
    exp = case["expected"]
    resp = auth.get("/api/clues/course/list", params=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("code") == exp["code"], f"业务码不符: {data}"
    if "msg" in exp:
        assert data.get("msg") == exp["msg"]
    rows = data.get("rows", [])
    if exp.get("rows_not_empty") is True:
        assert len(rows) > 0, "期望有数据但rows为空"
    elif exp.get("rows_not_empty") is False:
        assert len(rows) == 0, "期望无数据但rows不为空"

@pytest.mark.course
@allure.feature("课程管理")
@allure.story("修改课程")
@allure.title("修改课程用例")
def test_update_course(auth, created_course_id):
    course_id = created_course_id

    # 查询原始数据
    response = auth.get(f"/api/clues/course/{course_id}")
    assert response.status_code == 200
    original = response.json()
    original_data = original.get("data", {})
    print(f"原始课程数据：{original_data}")

    # 生成随机新数据
    new_name = f"{original_data.get('name', '课程')}_{int(time.time())}"
    new_subject = str(random.randint(0, 6))
    new_price = random.randint(1000, 10000)
    new_info = f"测试_{int(time.time())}_信息"

    # 执行修改
    update_resp = auth.put("/api/clues/course", json={
        "id": course_id,
        "name": new_name,
        "subject": new_subject,
        "price": new_price,
        "applicablePerson": "2",
        "info": new_info,
    })
    assert update_resp.status_code == 200
    update_body = update_resp.json()
    assert update_body.get("code") == 200, f"修改失败: {update_body.get('msg')}"
    assert update_body.get("msg") == "操作成功"

    # 重新查询，确认修改生效
    check_resp = auth.get(f"/api/clues/course/{course_id}")
    assert check_resp.status_code == 200
    check_data = check_resp.json().get("data", {})
    print(f"更新后课程数据：{check_data}")

    assert check_data.get("name") == new_name, f"名称未更新: {check_data.get('name')}"
    assert check_data.get("subject") == new_subject, f"学科未更新: {check_data.get('subject')}"
    assert check_data.get("price") == new_price, f"价格未更新: {check_data.get('price')}"
    assert check_data.get("info") == new_info, f"信息未更新: {check_data.get('info')}"

    print(f"课程 {course_id} 更新成功")


# 删除课程
@pytest.mark.course
@allure.feature("课程管理")
@allure.story("删除课程")
@allure.title("删除课程用例")
class TestDeleteCourse:

    @allure.title("删除存在的课程")
    def test_delete_normal(self, auth, created_course_id):
        course_id = created_course_id

        # 确认课程存在且未被删除
        before_resp = auth.get(f"/api/clues/course/{course_id}")
        assert before_resp.status_code == 200
        before_body = before_resp.json()
        assert before_body.get("code") == 200, "课程不存在，无法删除"
        before_data = before_body.get("data", {})
        assert before_data.get("isDelete") == 0, "课程已被删除"

        # 执行删除
        del_resp = auth.delete(f"/api/clues/course/{course_id}")
        assert del_resp.status_code == 200
        del_body = del_resp.json()
        assert del_body.get("code") == 200, f"删除失败: {del_body.get('msg')}"
        assert del_body.get("msg") == "操作成功"

        # 再次查询，确认课程已被删除
        after_resp = auth.get(f"/api/clues/course/{course_id}")
        assert after_resp.status_code == 200
        after_body = after_resp.json()
        assert after_body.get("code") == 200, f"查询异常: {after_body}"
        after_data = after_body.get("data", {})
        assert after_data.get("isDelete") == 1, f"课程未删除: isDelete={after_data.get('isDelete')}"

        print(f"课程 {course_id} 删除成功")

    @allure.title("删除不存在的课程")
    def test_delete_not_exist(self, auth):
        fake_id = 999999  # 确保不存在的 ID
        del_resp = auth.delete(f"/api/clues/course/{fake_id}")
        assert del_resp.status_code == 200
        body = del_resp.json()
        assert body.get("code") == 500, f"删除不存在课程应失败: {body}"
        assert body.get("msg") == "操作失败"

    @allure.title("根据名称批量删除课程")
    # @pytest.mark.skip(reason="批量删除风险较高，请手动确认后再取消跳过")
    def test_batch_delete_by_name(self, auth):

        name = ""  # 课程名称
        subject = 2  # 学科
        max_delete = 30  #None

        # 查询课程列表
        list_resp = auth.get("/api/clues/course/list", params={"name": name, "subject": subject})
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body.get("code") == 200, f"查询课程列表失败: {list_body}"

        # 直接取根对象的 rows
        all_courses = list_body.get("rows", [])
        if not all_courses:
            pytest.skip(f"未找到名称为 '{name}' 的课程，跳过批量删除")

        # 删除的课程列表
        if max_delete is not None and max_delete > 0:
            courses_to_delete = all_courses[:max_delete]
        else:
            courses_to_delete = all_courses

        if not courses_to_delete:
            pytest.skip("要删除的课程数量为0，跳过")

        # 逐个删除
        deleted_ids = []
        for course in courses_to_delete:
            course_id = course.get("id")
            del_resp = auth.delete(f"/api/clues/course/{course_id}")
            assert del_resp.status_code == 200
            del_body = del_resp.json()
            assert del_body.get("code") == 200, f"删除课程 {course_id} 失败: {del_body}"
            deleted_ids.append(course_id)

        # 验证所有已删除课程的状态
        for cid in deleted_ids:
            check_resp = auth.get(f"/api/clues/course/{cid}")
            assert check_resp.status_code == 200
            check_body = check_resp.json()
            check_data = check_body.get("data", {})
            assert check_data.get("isDelete") == 1, f"课程 {cid} 未被软删除"

        print(f"成功批量删除 {len(deleted_ids)} 个名称为 '{name}' 的课程: {deleted_ids}")