import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image, ImageTk # Pillow 라이브러리에서 필요한 부분 가져오기

# ----------------------------------------------------------------------
# --- 3. 게임 화면 관련 함수 ---
# (이전과 동일)
# ----------------------------------------------------------------------
def player_hit(result_var, hit_btn, stand_btn):
    if random.random() < 0.3:
        result_var.set("BUST")
        result_var.get_label().config(fg="orange")
        hit_btn.config(state="abled")
        stand_btn.config(state="abled")

def player_stand(result_var, hit_btn, stand_btn):
    if random.random() < 0.5:
        result_var.set("WIN")
        result_var.get_label().config(fg="green")
    else:
        result_var.set("LOSE")
        result_var.get_label().config(fg="red")
    hit_btn.config(state="abled")
    stand_btn.config(state="abled")

def open_game_window():
    game_win = tk.Tk()
    game_win.title("BLACK JACK Game")
    game_win.geometry("700x500")
    game_win.configure(bg="#016D29")

    class ResultVar(tk.StringVar):
        def set_label(self, label):
            self._label = label
        def get_label(self):
            return self._label

    game_result_var = ResultVar(value="")
    result_label = tk.Label(game_win, textvariable=game_result_var, font=("Arial", 60, "bold"), bg="#016D29", fg="white")
    result_label.place(relx=0.5, rely=0.5, anchor="center")
    game_result_var.set_label(result_label)

    dealer_frame = tk.Frame(game_win, pady=10, bg="#016D29")
    dealer_frame.pack()
    player_frame = tk.Frame(game_win, pady=10, bg="#016D29")
    player_frame.pack()
    control_frame = tk.Frame(game_win, pady=20, bg="#016D29")
    control_frame.pack(side="bottom")

    dealer_label = tk.Label(dealer_frame, text="딜러의 카드", font=("Arial", 12), fg="white", bg="#016D29")
    dealer_label.pack()
    dealer_cards_label = tk.Label(dealer_frame, text="[카드 1] [?]", font=("Arial", 16, "bold"), pady=10, fg="white", bg="#016D29")
    dealer_cards_label.pack()
    
    player_label = tk.Label(player_frame, text="플레이어의 카드", font=("Arial", 12), fg="white", bg="#016D29")
    player_label.pack()
    player_cards_label = tk.Label(player_frame, text="[카드 1] [카드 2]", font=("Arial", 16, "bold"), pady=10, fg="white", bg="#016D29")
    player_cards_label.pack()

    chip_label = tk.Label(control_frame, text="남은 칩: $1000", font=("Arial", 12), fg="white", bg="#016D29")
    chip_label.pack(pady=10)

    hit_button = tk.Button(control_frame, text="힛 (Hit)", font=("Arial", 14), width=10)
    hit_button.pack(side="left", padx=10)
    stand_button = tk.Button(control_frame, text="스탠드 (Stand)", font=("Arial", 14), width=10)
    stand_button.pack(side="left", padx=10)
    
    hit_button.config(command=lambda: player_hit(game_result_var, hit_button, stand_button))
    stand_button.config(command=lambda: player_stand(game_result_var, hit_button, stand_button))
    game_win.mainloop()

# ----------------------------------------------------------------------
# --- 2. 메인 메뉴 화면 관련 함수 ---
# (이전과 동일)
# ----------------------------------------------------------------------
def start_game(main_window):
    main_window.destroy()
    open_game_window()

def show_ranking():
    messagebox.showinfo("랭킹", "랭킹 정보를 불러옵니다.")

def open_main_window():
    main_win = tk.Tk()
    main_win.title("BLACK JACK 메인 화면")
    main_win.geometry("1000x600")
    
    betting_amount = tk.StringVar(value="베팅 금액: $1000") 
    betting_label = tk.Label(main_win, textvariable=betting_amount, font=("Arial", 14, "bold"), pady=20)
    betting_label.pack(pady=10)
    start_button = tk.Button(main_win, text="게임 시작", font=("Arial", 12), width=20, height=2, command=lambda: start_game(main_win))
    start_button.pack(pady=10)
    
    ranking_button = tk.Button(main_win, text="랭킹 보기", font=("Arial", 12), width=20, height=2, command=show_ranking)
    ranking_button.pack(pady=10)
    main_win.mainloop()

# ----------------------------------------------------------------------
# --- 1. 로그인 화면 관련 함수 및 실행 코드 (✨ 이 부분이 수정됨) ---
# ----------------------------------------------------------------------
def attempt_login(event=None):
    username = username_entry.get()
    password = password_entry.get()
    if username == "" and password == "":
        messagebox.showinfo("로그인 성공", f"{username}님, 환영합니다!")
        login_win.destroy()
        open_main_window()
    else:
        messagebox.showerror("로그인 실패", "사용자 이름 또는 비밀번호가 잘못되었습니다.")

if __name__ == "__main__":
    login_win = tk.Tk()
    login_win.title("BLACK JACK 로그인")
    login_win.geometry("350x300") # 창 크기를 조금 키움
    login_win.resizable(False, False)

    main_frame = tk.Frame(login_win, padx=20, pady=20)
    main_frame.pack(expand=True)


    # 사용자 이름 입력란 (row 번호가 1로 밀림)
    username_label = tk.Label(main_frame, text="사용자 이름:")
    username_label.grid(row=1, column=0, sticky="w", pady=5)
    username_entry = tk.Entry(main_frame)
    username_entry.grid(row=1, column=1, padx=5)

    # 비밀번호 입력란 (row 번호가 2로 밀림)
    password_label = tk.Label(main_frame, text="비밀번호:")
    password_label.grid(row=2, column=0, sticky="w", pady=5)
    password_entry = tk.Entry(main_frame, show="*")
    password_entry.grid(row=2, column=1, padx=5)

    # 버튼 (row 번호가 3으로 밀림)
    login_button = tk.Button(main_frame, text="로그인", width=10, command=attempt_login)
    login_button.grid(row=3, column=0, pady=15, sticky="e")
    close_button = tk.Button(main_frame, text="닫기", width=10, command=login_win.destroy)
    close_button.grid(row=3, column=1, pady=15, padx=5, sticky="w")

    login_win.bind('<Return>', attempt_login)
    login_win.mainloop()
