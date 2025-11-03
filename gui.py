import tkinter as tk
from tkinter import messagebox
import ctypes

import hashlib
import os
import sqlite3
import database as db

# =========================
# 고해상도 DPI 지원 (Windows 전용)
# =========================
# ctypes.windll.shcore.SetProcessDpiAwareness(1)

# =========================
# 블랙잭 GUI (빈 틀만)
# =========================

DB_NAME = db.DB_FILE


class BlackjackGUI:
    def __init__(self, root, user_data : dict):
        self.root = tk.Toplevel(root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("1286x886")
        self.root.configure(bg="green")

        self.user_id = user_data["id"]
        self.username = user_data["username"]
        self.bankroll = user_data["bankroll"]

        # 메인 화면 버튼
        self.main_menu_button = tk.Button(self.root, text="로그아웃", width=11, height=2, font=("Arial",7,"bold"), command=self.logout)
        self.main_menu_button.place(x=3, y=3)

        # 딜러 카드 프레임
        self.dealer_frame = tk.LabelFrame(self.root, text="딜러", font=("Arial",16,"bold"), fg="white", bg="green", labelanchor="n")
        self.dealer_frame.pack(fill="x", padx=20, pady=(50,10))
        self.dealer_inner_frame = tk.Frame(self.dealer_frame, bg="green")
        self.dealer_inner_frame.pack(pady=10)

        # 상태 표시
        self.status_label = tk.Label(self.root, text="게임 준비 완료!", bg="green", fg="yellow", font=("Arial",20,"bold"))
        self.status_label.pack(pady=15)

        # 플레이어 카드 프레임
        self.player_frame = tk.LabelFrame(self.root, text="플레이어", font=("Arial",16,"bold"), fg="white", bg="green", labelanchor="n")
        self.player_frame.pack(fill="x", padx=20, pady=(10,0))
        self.player_inner_frame = tk.Frame(self.player_frame, bg="green")
        self.player_inner_frame.pack(pady=10)

        # 남은 돈 표시
        self.chip_label = tk.Label(self.root, text=f"남은 돈: {self.bankroll}", bg="green", fg="white", font=("Arial",16,"bold"))
        self.chip_label.pack(pady=10)

        # 버튼 프레임
        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20)

        btn_width = 15
        btn_height = 2
        btn_font = ("Arial", 10, "bold")

        # 더블다운
        tk.Button(self.button_frame, text="더블다운", width=btn_width, height=btn_height, font=btn_font).grid(row=0, column=0, padx=30)
        # 스플릿
        tk.Button(self.button_frame, text="스플릿", width=btn_width, height=btn_height, font=btn_font).grid(row=0, column=1, padx=30)
        # 스탠드
        tk.Button(self.button_frame, text="스탠드", width=btn_width, height=btn_height, font=btn_font).grid(row=0, column=2, padx=30)
        # 히트
        tk.Button(self.button_frame, text="히트", width=btn_width, height=btn_height, font=btn_font).grid(row=0, column=3, padx=30)
        # 다시하기
        tk.Button(self.button_frame, text="다시하기", width=btn_width, height=btn_height, font=btn_font).grid(row=0, column=4, padx=30)

    def logout(self):
        """로그아웃 시 로그인창으로 복귀"""
        self.root.destroy()
        main_login_window()

# =========================
# 로그인 창
# =========================

def main_login_window():
    global login_win, username_entry, password_entry

    login_win = tk.Tk()
    login_win.title("BLACK JACK 로그인")
    login_win.geometry("600x300")
    login_win.resizable(False, False)

    main_frame = tk.Frame(login_win, padx=30, pady=30)
    main_frame.pack(expand=True)

    tk.Label(main_frame, text="사용자 이름:", font=("Dotum",12,"bold")).grid(row=0,column=0,sticky="w", pady=10)
    username_entry = tk.Entry(main_frame, font=("Dotum",12))
    username_entry.grid(row=0,column=1, padx=5, pady=10)

    tk.Label(main_frame, text="비밀번호:", font=("Dotum",12,"bold")).grid(row=1,column=0,sticky="w", pady=10)
    password_entry = tk.Entry(main_frame, font=("Dotum",12), show="*")
    password_entry.grid(row=1,column=1, padx=5, pady=10)

    tk.Button(main_frame, text="회원가입", width=12, font=("Dotum",11,"bold"), command=handle_signup_click).grid(row=2, column=1, pady=20, padx=5, sticky="w")
    tk.Button(main_frame, text="로그인", width=12, font=("Dotum",11,"bold"), command=handle_login_click).grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum",11,"bold"), command=login_win.destroy).grid(row=2, column=2, pady=20, padx=5, sticky="w")

    login_win.bind('<Return>', handle_login_click)
    login_win.mainloop()

#회원가입
def handle_signup_click():
    """ [연결 지점 1: 회원가입] GUI -> DB """
    username = username_entry.get()
    password = password_entry.get()
    if not username or not password:
        messagebox.showerror("오류", "ID와 비밀번호를 모두 입력하세요.")
        return

    # 1. 비밀번호 해싱 (로직)
    salt = os.urandom(16) # 16바이트의 랜덤 '솔트' 생성
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000
    )

    # 2. DB 연결 및 호출
    try:
        conn = sqlite3.connect(DB_NAME)
        # 'database.py'의 create_user 함수 호출!
        success = db.create_user(conn, username, hashed_password, salt)
        conn.close()

        if success:
            messagebox.showinfo("성공", "회원가입 성공! 이제 로그인하세요.")
        else:
            messagebox.showerror("오류", "이미 존재하는 ID입니다.")
    except Exception as e:
        messagebox.showerror("DB 오류", f"오류 발생: {e}")
#로그인
def handle_login_click(event=None):
    """ [연결 지점 2: 로그인] GUI -> DB -> GUI """
    username = username_entry.get()
    password = password_entry.get()
    if not username or not password:
        messagebox.showerror("오류", "ID와 비밀번호를 모두 입력하시오.")
        return

    # 1. DB 연결 및 사용자 조회
    try:
        conn = sqlite3.connect(DB_NAME)
        # 'database.py'의 get_user_by_username 함수 호출!
        user_record = db.get_user_by_username(conn, username)
        conn.close()

        if user_record is None:
            messagebox.showerror("실패", "존재하지 않는 ID입니다.")
            return

        # 2. 비밀번호 검증 (로직)
        user_id, stored_hash, salt, bankroll = user_record

        # 사용자가 입력한 비번을 DB의 '솔트'로 다시 해싱
        provided_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, 100000
        )

        if provided_hash == stored_hash:
            # 3. [핵심] 로그인 성공!
            messagebox.showinfo("로그인 성공", f"{username}님, 환영합니다!")
            login_win.withdraw() # 로그인창 숨기기

            # 'user_data' 딕셔너리로 묶어서 게임 창에 전달
            user_data = {
                "id": user_id,
                "username": username,
                "bankroll": bankroll
            }
            # BlackjackGUI 클래스에 user_data를 넘겨줌!
            BlackjackGUI(login_win, user_data) 
        else:
            messagebox.showerror("실패", "비밀번호가 틀렸습니다.")

    except Exception as e:
        messagebox.showerror("DB 오류", f"오류 발생: {e}")
# =========================
# 프로그램 실행
# =========================

# 1. DB를 맨 처음 세팅하는 함수를 하나 만듭니다.
def setup_database():
    """ 프로그램 시작 시 DB와 테이블을 초기화합니다. """
    conn = sqlite3.connect(db.DB_FILE) # database.py의 DB_FILE 이름을 사용
    
    # ⬇️  ★★★ 바로 여기! ★★★
    # database.py에 정의된 테이블 생성 함수를 '호출'합니다.
    db.initialize_db(conn) 
    
    conn.close()
    print("데이터베이스 초기화 완료. (테이블 생성됨)")

# =========================
# 프로그램 실행
# =========================
if __name__ == "__main__":
    setup_database()    
    main_login_window()   

