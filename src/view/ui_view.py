import tkinter as tk
from tkinter import messagebox
import os
import glob
from PIL import Image, ImageTk
import json
import hashlib

# --- 상수 ---
# ui_view.py 파일 기준으로 img 폴더 경로 생성 (안전한 절대 경로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "img")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

# ----------------------
# 간단한 사용자 저장소 (파일 기반)
# ----------------------
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def load_users():
    try:
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("사용자 파일 로드 실패:", e)
        return {}

def save_users(users: dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("사용자 파일 저장 실패:", e)

# =========================
# 랭킹창 (View)
# =========================
def open_ranking_window():
    ranking_win = tk.Toplevel()
    ranking_win.title("🏆 게임 랭킹")
    ranking_win.geometry("300x400")
    ranking_win.resizable(False, False)
    tk.Label(ranking_win, text="랭킹 순위", font=("Dotum",16,"bold"), pady=15).pack()
    
    tk.Button(ranking_win, text="닫기", command=ranking_win.destroy).pack(pady=15)
    return ranking_win # 컨트롤러가 접근할 수 있도록 윈도우 객체 반환

def populate_ranking_data(ranking_win, rank_data):
    """ [View] 컨트롤러가 준 데이터로 랭킹창 채우기 """
    if not rank_data:
        tk.Label(ranking_win, text="아직 랭킹이 없습니다.", font=("Dotum",12)).pack(pady=5)
        return

    for rank, (name, score) in enumerate(rank_data, 1):
        medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"{rank}."
        text = f"{medal} {name}: ${score}"
        tk.Label(ranking_win, text=text, font=("Dotum",12), anchor="w").pack(fill="x", pady=2, padx=20)

# =========================
# 메인 메뉴 (View)
# =========================
class MainMenu(tk.Tk):
    """ '순수' 메인 메뉴 UI (껍데기) """
    def __init__(self, user_data: dict, users_store: dict):
        super().__init__()
        self.title("BLACK JACK 메인 화면")
        self.geometry("800x500")
        self.resizable(False, False)
        
        self.user_data = user_data
        self.users_store = users_store

        self.chips = user_data["bankroll"] 

        tk.Label(self, text=f"🎲 {user_data['username']}님, 환영합니다!", font=("Dotum",18,"bold"), pady=20).pack()
        self.chip_label = tk.Label(self, text=f"보유 돈: ${self.chips}", font=("Dotum",14,"bold"))
        self.chip_label.pack(pady=5)

        frame = tk.Frame(self)
        frame.pack(pady=5)

        tk.Label(frame, text="베팅 금액:").pack(side="left")
        self.bet_entry = tk.Entry(frame, width=10) # Controller가 이 위젯에 접근
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0,"100") 

        # 버튼들 (이벤트는 아래에서 연결)
        self.charge_button = tk.Button(frame, text="돈 충전 (+100)", font=("Dotum",10))
        self.charge_button.pack(side="left", padx=5)

        self.start_game_button = tk.Button(self, text="게임 시작", font=("Dotum",14), width=20, height=2)
        self.start_game_button.pack(pady=10)
        
        self.ranking_button = tk.Button(self, text="랭킹 보기", font=("Dotum",14), width=20, height=2)
        self.ranking_button.pack(pady=10) 
        
        self.logout_button = tk.Button(self, text="로그아웃", font=("Dotum", 14), width=20, height=2)
        self.logout_button.pack(pady=10)

        # 이벤트 연결 (여기서는 UI 내부에서 직접 처리)
        self.charge_button.config(command=self._charge_money)
        self.start_game_button.config(command=self._on_start_game)
        self.ranking_button.config(command=self._on_ranking)
        self.logout_button.config(command=self._on_logout)

    def update_chip_label(self, new_chips):
        """ [View] 컨트롤러의 요청을 받아 칩 라벨 업데이트 """
        self.chips = new_chips
        self.chip_label.config(text=f"보유 돈: ${self.chips}")

    # ----- 버튼 이벤트 구현 (간단 구현) -----
    def _charge_money(self):
        self.chips += 100
        self.user_data["bankroll"] = self.chips
        # 저장
        self.users_store[self.user_data["username"]]["bankroll"] = self.chips
        save_users(self.users_store)
        self.update_chip_label(self.chips)
        messagebox.showinfo("충전 완료", "보유금액이 $100 충전되었습니다.")

    def _on_start_game(self):
        try:
            bet = int(self.bet_entry.get())
            if bet <= 0:
                raise ValueError()
        except Exception:
            messagebox.showerror("베팅 오류", "올바른 베팅 금액을 입력하세요.")
            return
        if bet > self.chips:
            messagebox.showerror("베팅 오류", "보유 금액보다 많은 금액을 베팅할 수 없습니다.")
            return

        # 간단히 게임 화면 열기
        BlackjackGUI(self, self.user_data, bet, self.chips)

    def _on_ranking(self):
        # 예시: 로컬 유저 데이터로 간단 랭킹 생성 (bankroll 내림차순)
        rank_list = sorted(
            [(u, data.get("bankroll", 0)) for u, data in self.users_store.items()],
            key=lambda x: x[1], reverse=True
        )
        w = open_ranking_window()
        populate_ranking_data(w, rank_list)

    def _on_logout(self):
        username = self.user_data["username"]
        if messagebox.askyesno("로그아웃", "정말 로그아웃 하시겠습니까?"):
            self.destroy()
            # 로그인 창 다시 띄우기 (단독 실행용 편의)
            win, _, _ = main_login_window()
            win.mainloop()

# =========================
# 블랙잭 GUI (View)
# =========================
class BlackjackGUI:
    """ '순수' 블랙잭 게임 UI (껍데기) """
    def __init__(self, main_menu_root, user_data: dict, bet_amount: int, current_bankroll: int):
        
        self.main_window = main_menu_root
        self.root = tk.Toplevel(main_menu_root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("900x600")
        self.root.configure(bg="green")
        
        self.card_images = self.load_card_images()
        self.current_dealer_hand_hidden = [] 

        self.main_menu_button = tk.Button(self.root, text="메인 화면으로", width=11, height=2, font=("Arial",9,"bold"), command=self.root.destroy)
        self.main_menu_button.place(x=3, y=3)

        self.status_label = tk.Label(self.root, text=f"베팅: ${bet_amount} / 남은 돈: ${current_bankroll - bet_amount}", bg="green", fg="yellow", font=("Arial",14,"bold"))
        self.status_label.pack(pady=15)

        # 단순 설명용 라벨
        tk.Label(self.root, text="(게임 로직은 구현되어 있지 않습니다 — UI 데모)", bg="green", fg="white").pack(pady=10)
        tk.Button(self.root, text="게임 종료(창 닫기)", command=self.root.destroy).pack(pady=10)

    def load_card_images(self):
        """ [View] 카드 이미지 로드 (이건 View의 책임) """
        images = {}
        card_size = (100, 150) 
        
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
        
        if not image_paths:
            print(f"경고: '{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다. (예: S_A.png)")
            # 경고는 띄우되 실행은 계속
            # messagebox.showwarning("이미지 오류", f"'{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
            return {}
            
        for path in image_paths:
            filename = os.path.basename(path)
            card_name = filename.split('.')[0]
            try:
                img = Image.open(path).resize(card_size)
                images[card_name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"이미지 로드 실패: {path} / {e}")
        
        if "BACK" not in images:
            print(f"경고: '{IMAGE_DIR}/BACK.png' (뒷면) 이미지를 찾을 수 없습니다.")
            
        return images

    def update_gui_cards(self, player_hand, dealer_hand):
        """ [View] 컨트롤러의 요청을 받아 카드 그리기 """
        # (딜러 패 저장 로직은 Controller로 이동)
        self.current_dealer_hand_hidden = dealer_hand # (히트 시 필요하므로 저장)

# =========================
# 로그인 창 (View)
# =========================
def main_login_window():
    """ 로그인 UI 생성 """
    global login_win, username_entry, password_entry # (Controller에서 접근해야 하므로 global 유지)

    users_store = load_users()

    login_win = tk.Tk()
    login_win.title("BLACK JACK 로그인")
    login_win.geometry("600x600")
    login_win.resizable(False, False)

    # ----------------------------------------------------
    # 로그인 이미지 로드 (함수 내부에 있어야 함)
    logo_path = os.path.join(IMAGE_DIR, "blackjack_logo.png")  # 실제 파일명에 맞게 수정하세요

    if not os.path.exists(logo_path):
        # messagebox.showwarning("이미지 오류", f"로그인 로고 이미지 '{logo_path}'를 찾을 수 없습니다.")
        logo_label = tk.Label(login_win, text="BLACKJACK", font=("Dotum", 30, "bold"), fg="gold", bg="darkblue", width=25, height=4)
    else:
        try:
            original_image = Image.open(logo_path)
            resized_image = original_image.resize((400, 200), Image.LANCZOS)
            logo_image = ImageTk.PhotoImage(resized_image)

            logo_label = tk.Label(login_win, image=logo_image)
            logo_label.image = logo_image
        except Exception as e:
            messagebox.showerror("이미지 로드 실패", f"로그인 로고 이미지 로드 중 오류 발생: {e}")
            logo_label = tk.Label(login_win, text="BLACKJACK", font=("Dotum", 30, "bold"), fg="gold", bg="darkblue")

    logo_label.pack(pady=20)

    main_frame = tk.Frame(login_win, padx=30, pady=30)
    main_frame.pack(expand=True)

    tk.Label(main_frame, text="사용자 이름:", font=("Dotum",12,"bold")).grid(row=0,column=0,sticky="w", pady=10)
    username_entry = tk.Entry(main_frame, font=("Dotum",12))
    username_entry.grid(row=0,column=1, padx=5, pady=10)

    tk.Label(main_frame, text="비밀번호:", font=("Dotum",12,"bold")).grid(row=1,column=0,sticky="w", pady=10)
    password_entry = tk.Entry(main_frame, font=("Dotum",12), show="*")
    password_entry.grid(row=1,column=1, padx=5, pady=10)

    # 버튼을 객체로 생성해서 반환(다른 모듈에서 접근 가능)
    signup_btn = tk.Button(main_frame, text="회원가입", width=12, font=("Dotum",11,"bold"))
    signup_btn.grid(row=2, column=1, pady=20, padx=5, sticky="w")
    login_btn = tk.Button(main_frame, text="로그인", width=12, font=("Dotum",11,"bold"))
    login_btn.grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum",11,"bold"), command=login_win.destroy).grid(row=2, column=2, pady=20, padx=5, sticky="w") 

    # ---------------------------
    # 버튼 동작 정의
    # ---------------------------
    def _do_signup():
        username = username_entry.get().strip()
        pwd = password_entry.get().strip()
        if not username or not pwd:
            messagebox.showerror("회원가입 오류", "사용자 이름과 비밀번호를 입력하세요.")
            return
        if username in users_store:
            messagebox.showerror("회원가입 오류", "이미 존재하는 사용자 이름입니다.")
            return
        users_store[username] = {
            "password": _hash_password(pwd),
            "bankroll": 1000
        }
        save_users(users_store)
        messagebox.showinfo("회원가입 완료", f"{username} 님의 계정이 생성되었습니다. 기본 금액 $1000 지급.")
        # 자동 로그인 유도(선택) — 입력란 클리어
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

    def _do_login():
        username = username_entry.get().strip()
        pwd = password_entry.get().strip()
        if not username or not pwd:
            messagebox.showerror("로그인 오류", "사용자 이름과 비밀번호를 입력하세요.")
            return
        info = users_store.get(username)
        if not info or info.get("password") != _hash_password(pwd):
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 올바르지 않습니다.")
            return

        # 로그인 성공 — 메인 창으로 이동
        user_data = {"username": username, "bankroll": info.get("bankroll", 1000)}
        messagebox.showinfo("로그인 성공", f"{username} 님 환영합니다!")
        # 닫고 메인 열기
        login_win.destroy()
        main_win = MainMenu(user_data, users_store)
        main_win.mainloop()

    signup_btn.config(command=_do_signup)
    login_btn.config(command=_do_login)

    return login_win, username_entry, password_entry

# ----- 단독 실행 편의 -----
if __name__ == "__main__":
    win, _, _ = main_login_window()
    win.mainloop()
