import sys
import os

# [중요] 'src' 폴더를 파이썬 경로에 추가합니다.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    # '뇌' 임포트
    # 🌟 수정 1: 경로를 'src.controll' (l 하나)로 수정합니다.
    import src.controller.new_controller as controller 
except ImportError as e:
    print(f"오류: 컨트롤러 임포트 실패. src 폴더 구조를 확인하세요. {e}")
    input("종료하려면 Enter를 누르세요...")
    sys.exit(1)


def main():
    # 1. '컨트롤러'에게 DB 초기화('setup')를 시킵니다.
    # setup_database는 모듈(controller) 내부에 정의된 일반 함수이므로 이 호출은 유지합니다.
    if not controller.setup_database():
        return # DB 초기화 실패 시 프로그램 종료

    # 2. '컨트롤러'에게 로그인 창을 띄우라고 '명령'합니다.
    # 🌟 수정 2: new_controller 모듈 안의 'AuthController' 클래스를 호출해야 합니다.
    auth_controller = controller.AuthController() 
    auth_controller.start_login_window()


if __name__ == "__main__":
    main()