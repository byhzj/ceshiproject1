import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
# 项目根目录
BASE_DIR = SCRIPT_DIR.parent
RESULTS = SCRIPT_DIR  / "reports" / "allure-results"
REPORT_DIR = SCRIPT_DIR  / "reports" / "allure-report"
ALLURE_PATH = r"D:\python\allure\allure-2.46.1\bin\allure.bat"


def generate_report(pytest_args=None):
    print("执行测试...")
    cmd = [
        sys.executable, "-m", "pytest",
        str(SCRIPT_DIR / "tests"),
        f"--rootdir={SCRIPT_DIR}",
        f"--alluredir={RESULTS}",
        "--clean-alluredir",
        "-vs"
    ]
    if pytest_args:
        cmd.extend(pytest_args)

    result = subprocess.run(cmd, cwd=BASE_DIR, shell=True)
    if result.returncode != 0:
        print(f"测试退出码 {result.returncode}，仍继续生成报告。")

    print("生成报告到指定文件夹...")
    subprocess.run(
        [ALLURE_PATH, "generate", str(RESULTS), "-o", str(REPORT_DIR), "--clean"],
        cwd=BASE_DIR,
        shell=True
    )
    print(f"报告已生成至: {REPORT_DIR}")

#     print("打开服务器，正在打开报告...")
#     subprocess.run(
#         [ALLURE_PATH, "open", str(REPORT_DIR)],
#         cwd=BASE_DIR,
#         shell=True
#     )


# def open_report():
#     """仅打开已生成的 Allure 报告"""
#     if not REPORT_DIR.exists() or not (REPORT_DIR / "index.html").exists():
#         print(f"错误：报告目录 {REPORT_DIR} 不存在或不完整，请先生成报告。")
#         sys.exit(1)
#     print("启动 Allure 报告服务器...")
#     subprocess.run(
#         [ALLURE_PATH, "open", str(REPORT_DIR)],
#         cwd=BASE_DIR,
#         shell=True
#     )


def main():
    if len(sys.argv) < 2:
        print("用法: python run_test.py [generate|open] [pytest选项(smoke)]")
        print("  generate  : 执行测试并生成/打开报告")
        print("  open      : 打开已生成的报告")
        sys.exit(1)

    mode = sys.argv[1].lower()
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if mode == "generate":
        # 传入额外的 pytest 参数
        generate_report(extra_args)
    elif mode == "open":
        if extra_args:
            print("警告：open 模式不支持额外参数，已忽略")
        open_report()
    else:
        print(f"错误: 未知模式 '{mode}'，请输入 generate 或 open")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
生成报告
python niweiming_kdtx/run_test.py generate

生成冒烟用例报告
python niweiming_kdtx/run_test.py generate -m smoke

打开已有报告
python niweiming_kdtx/run_test.py open



"""
