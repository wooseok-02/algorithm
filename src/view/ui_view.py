import tkinter as tk
from tkinter import messagebox
import os
import glob
from PIL import Image, ImageTk
import json
import hashlib
import re

# --- 상수 ---
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
    return ranking_win

def populate_ranking_data(ranking_win, rank_data):
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
        self.bet_entry = tk.Entry(frame, width=10)
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0,"100")

        self.charge_button = tk.Button(frame, text="돈 충전 (+100)", font=("Dotum",10))
        self.charge_button.pack(side="left", padx=5)
        self.start_game_button = tk.Button(self, text="게임 시작", font=("Dotum",14), width=20, height=2)
        self.start_game_button.pack(pady=10)
        self.ranking_button = tk.Button(self, text="랭킹 보기", font=("Dotum",14), width=20, height=2)
        self.ranking_button.pack(pady=10)
        self.logout_button = tk.Button(self, text="로그아웃", font=("Dotum", 14), width=20, height=2)
        self.logout_button.pack(pady=10)

        self.charge_button.config(command=self._charge_money)
        self.start_game_button.config(command=self._on_start_game)
        self.ranking_button.config(command=self._on_ranking)
        self.logout_button.config(command=self._on_logout)

    def update_chip_label(self, new_chips):
        self.chips = new_chips
        self.chip_label.config(text=f"보유 돈: ${self.chips}")

    def _charge_money(self):
        self.chips += 100
        self.user_data["bankroll"] = self.chips
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
        BlackjackGUI(self, self.user_data, bet, self.chips)

    def _on_ranking(self):
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
            win, _, _ = main_login_window()
            win.mainloop()

# =========================
# 블랙잭 GUI (View) - 플립 애니메이션 포함(데모 자동 실행)
# =========================
class BlackjackGUI:
    def __init__(self, main_menu_root, user_data: dict, bet_amount: int, current_bankroll: int):
        self.main_window = main_menu_root
        self.root = tk.Toplevel(main_menu_root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("900x600")
        self.root.configure(bg="green")

        self.card_images_pil = {}
        self.card_images_tk_cached = {}
        self.card_size = (100, 150)

        self.load_card_images()

        self.main_menu_button = tk.Button(self.root, text="메인 화면으로", width=11, height=2, font=("Arial",9,"bold"), command=self.root.destroy)
        self.main_menu_button.place(x=3, y=3)

        self.status_label = tk.Label(self.root, text=f"베팅: ${bet_amount} / 남은 돈: ${current_bankroll - bet_amount}", bg="green", fg="yellow", font=("Arial",14,"bold"))
        self.status_label.pack(pady=15)

        tk.Label(self.root, text="딜러", bg="green", fg="white", font=("Arial", 14, "bold")).pack(pady=(10,0))
        self.dealer_frame = tk.Frame(self.root, bg="green", height=160, width=800)
        self.dealer_frame.pack(pady=5)
        self.dealer_frame.pack_propagate(False)

        tk.Label(self.root, text=f"{user_data['username']}", bg="green", fg="white", font=("Arial", 14, "bold")).pack(pady=(10,0))
        self.player_frame = tk.Frame(self.root, bg="green", height=160, width=800)
        self.player_frame.pack(pady=5)
        self.player_frame.pack_propagate(False)

        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20, side="bottom")

        self.hit_button = tk.Button(self.button_frame, text="Hit", font=("Arial", 14), width=10)
        self.hit_button.pack(side="left", padx=5)
        self.stand_button = tk.Button(self.button_frame, text="Stand", font=("Arial", 14), width=10)
        self.stand_button.pack(side="left", padx=5)
        self.double_button = tk.Button(self.button_frame, text="Double", font=("Arial", 14), width=10)
        self.double_button.pack(side="left", padx=5)
        self.split_button = tk.Button(self.button_frame, text="Split", font=("Arial", 14), width=10)
        self.split_button.pack(side="left", padx=5)
        self.surrender_button = tk.Button(self.button_frame, text="Surrender", font=("Arial", 14), width=10)
        self.surrender_button.pack(side="left", padx=5)

        dummy_player_hand = ['C_2', 'C_3']
        dummy_dealer_hand = ['BACK', 'BACK']
        self.update_gui_cards(dummy_player_hand, dummy_dealer_hand)

        # ---- 필터링: 실제 카드 파일만 선택 (C_, D_, H_, S_ 로 시작하는 파일들)
        all_keys = list(self.card_images_pil.keys())
        card_pattern_keys = [k for k in all_keys if k.startswith(("C_", "D_", "H_", "S_")) and k != "BACK"]

        # 안전장치: 없으면 BACK 유지
        if len(card_pattern_keys) == 0:
            flip_targets = ["BACK", "BACK"]
        elif len(card_pattern_keys) == 1:
            flip_targets = [card_pattern_keys[0], card_pattern_keys[0]]
        else:
            flip_targets = [card_pattern_keys[0], card_pattern_keys[1]]

        # 데모: 1초 뒤 첫 카드 뒤집기, 0.6초 뒤 두번째 카드 뒤집기
        self.root.after(1000, lambda: self.flip_dealer_card(0, flip_targets[0]))
        self.root.after(1600, lambda: self.flip_dealer_card(1, flip_targets[1]))

    def load_card_images(self):
        card_size = self.card_size
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.[pP][nN][gG]"))
        if not image_paths:
            print(f"경고: '{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
            messagebox.showwarning("이미지 오류", f"'{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
            return

        for path in image_paths:
            filename = os.path.basename(path)
            card_name = filename.split('.')[0]
            try:
                img = Image.open(path).convert("RGBA")
                img_resized = img.resize(card_size, Image.LANCZOS)
                self.card_images_pil[card_name] = img_resized
            except Exception as e:
                print(f"이미지 로드 실패: {path} / {e}")

        if "BACK" not in self.card_images_pil:
            print(f"경고: '{IMAGE_DIR}/BACK.png' (뒷면) 이미지를 찾을 수 없습니다.")

    def _get_tk_image(self, card_name, width=None):
        if card_name not in self.card_images_pil:
            return None
        full_w, full_h = self.card_size
        target_w = width if width is not None else full_w
        target_h = full_h
        key = (card_name, target_w)
        if key in self.card_images_tk_cached:
            return self.card_images_tk_cached[key]
        if target_w <= 0:
            target_w = 1
        pil = self.card_images_pil[card_name].resize((int(target_w), int(target_h)), Image.LANCZOS)
        tkimg = ImageTk.PhotoImage(pil)
        self.card_images_tk_cached[key] = tkimg
        return tkimg

    def update_gui_cards(self, player_hand: list, dealer_hand: list):
        for widget in self.dealer_frame.winfo_children():
            widget.destroy()
        for widget in self.player_frame.winfo_children():
            widget.destroy()

        for card_name in dealer_hand:
            tkimg = self._get_tk_image(card_name)
            if tkimg:
                lbl = tk.Label(self.dealer_frame, image=tkimg, bg="green")
                lbl.image = tkimg
            else:
                lbl = tk.Label(self.dealer_frame, text=card_name, bg="white", fg="black", width=14, height=9, relief="sunken", font=("Arial", 10))
            lbl.pack(side="left", padx=5)

        for card_name in player_hand:
            tkimg = self._get_tk_image(card_name)
            if tkimg:
                lbl = tk.Label(self.player_frame, image=tkimg, bg="green")
                lbl.image = tkimg
            else:
                lbl = tk.Label(self.player_frame, text=card_name, bg="white", fg="black", width=14, height=9, relief="sunken", font=("Arial", 10))
            lbl.pack(side="left", padx=5)

    def flip_dealer_card(self, index, final_card_name):
        widgets = self.dealer_frame.winfo_children()
        if index < 0 or index >= len(widgets):
            return
        label = widgets[index]
        if not hasattr(label, "image"):
            tkimg = self._get_tk_image(final_card_name)
            if tkimg:
                label.config(image=tkimg, text="")
                label.image = tkimg
            return

        back_exists = "BACK" in self.card_images_pil
        front_exists = final_card_name in self.card_images_pil
        if not back_exists and not front_exists:
            return

        full_w, full_h = self.card_size
        steps = 12
        interval = 20

        widths_shrink = [int(full_w * (1 - i/steps)) for i in range(steps)]
        if widths_shrink[-1] <= 0:
            widths_shrink[-1] = 1
        widths_expand = [int(full_w * (i/steps)) for i in range(1, steps+1)]

        def do_shrink(i=0):
            if i >= len(widths_shrink):
                if front_exists:
                    tkimg = self._get_tk_image(final_card_name, width=1)
                    if tkimg:
                        label.config(image=tkimg)
                        label.image = tkimg
                do_expand(0)
                return
            w = widths_shrink[i]
            src = "BACK" if back_exists else final_card_name
            tkimg = self._get_tk_image(src, width=w)
            if tkimg:
                label.config(image=tkimg)
                label.image = tkimg
            self.root.after(interval, lambda: do_shrink(i+1))

        def do_expand(i=0):
            if i >= len(widths_expand):
                final_img = self._get_tk_image(final_card_name)
                if final_img:
                    label.config(image=final_img)
                    label.image = final_img
                return
            w = widths_expand[i]
            tkimg = self._get_tk_image(final_card_name, width=w)
            if tkimg:
                label.config(image=tkimg)
                label.image = tkimg
            self.root.after(interval, lambda: do_expand(i+1))

        do_shrink(0)

# =========================
# 로그인 창 (View)
# =========================
def main_login_window():
    global login_win, username_entry, password_entry
    users_store = load_users()
    login_win = tk.Tk()
    login_win.title("BLACK JACK 로그인")
    login_win.geometry("600x600")
    login_win.resizable(False, False)

    logo_path = os.path.join(IMAGE_DIR, "blackjack_logo.png")
    if not os.path.exists(logo_path):
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

    signup_btn = tk.Button(main_frame, text="회원가입", width=12, font=("Dotum",11,"bold"))
    signup_btn.grid(row=2, column=1, pady=20, padx=5, sticky="w")
    login_btn = tk.Button(main_frame, text="로그인", width=12, font=("Dotum",11,"bold"))
    login_btn.grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum",11,"bold"), command=login_win.destroy).grid(row=2, column=2, pady=20, padx=5, sticky="w")

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
        user_data = {"username": username, "bankroll": info.get("bankroll", 1000)}
        messagebox.showinfo("로그인 성공", f"{username} 님 환영합니다!")
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
