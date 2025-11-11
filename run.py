# [파일 이름: run.py]
# 프로젝트의 '유일한' 실행 파일입니다.

import sys
import os

# [중요] 'src' 폴더를 파이썬 경로에 추가합니다.
# (이래야 'import src.controller...'가 작동합니다)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    # '뇌' 임포트
    import src.controller.app_controller as controller
except ImportError as e:
    print(f"오류: 컨트롤러 임포트 실패. src 폴더 구조를 확인하세요. {e}")
    input("종료하려면 Enter를 누르세요...")
    sys.exit(1)


def main():
    # 1. '컨트롤러'에게 DB 초기화('setup')를 시킵니다.
    if not controller.setup_database():
        return # DB 초기화 실패 시 프로그램 종료

    # 2. '컨트롤러'에게 로그인 창을 띄우라고 '명령'합니다.
    auth_controller = controller.AuthController()
    auth_controller.start_login_window()


if __name__ == "__main__":
    main()