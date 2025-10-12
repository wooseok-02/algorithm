import tkinter as tk
from tkinter import messagebox
import random
from PIL import Image, ImageTk # Pillow 라이브러리에서 필요한 부분 가져오기

# ----------------------------------------------------------------------
# --- 4. 랭킹 창 관련 함수 (새로 추가) ---
# ----------------------------------------------------------------------
def open_ranking_window():
    """랭킹 정보를 보여주는 새 창을 생성하는 함수"""
    # Toplevel은 메인 창 위에 띄우는 보조 창을 만들 때 사용합니다.
    ranking_win = tk.Toplevel()
    ranking_win.title("🏆 게임 랭킹")
    ranking_win.geometry("300x400")
    ranking_win.resizable(False, False)

    # 창 제목 라벨
    title_label = tk.Label(ranking_win, text="랭킹 순위", font=("Dotum", 16, "bold"), pady=15)
    title_label.pack()

    # 랭킹 정보를 담을 프레임
    ranking_frame = tk.Frame(ranking_win)
    ranking_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # --- 예시 랭킹 데이터 ---
    rankings = {
        "1. Player1": "$ 9,500",
        "2. Dealer": "$ 8,100",
        "3. AcePlayer": "$ 7,650",
        "4. Lucky7": "$ 6,200",
        "5. CardMaster": "$ 5,150",
    }

    # 랭킹 데이터를 화면에 표시
    for rank, (name, score) in enumerate(rankings.items(), 1):
        # 1, 2, 3위는 메달 아이콘 추가
        medal = ""
        if rank == 1: medal = "🥇"
        elif rank == 2: medal = "🥈"
        elif rank == 3: medal = "🥉"
        
        rank_text = f"{medal} {name}: {score}"
        rank_label = tk.Label(ranking_frame, text=rank_text, font=("Dotum", 12,), anchor="w")
        rank_label.pack(fill="x", pady=2) # anchor='w'는 텍스트를 왼쪽으로 정렬

    # 닫기 버튼
    close_button = tk.Button(ranking_win, text="닫기", font=("Dotum", 10), command=ranking_win.destroy)
    close_button.pack(pady=15)

# ----------------------------------------------------------------------
# --- 3. 게임 화면 관련 함수 ---
# (이전과 동일)
# ----------------------------------------------------------------------

def reset_game_state(result_var, player_cards_var, dealer_cards_var, hit_btn, stand_btn):
    """게임 상태를 초기화하는 함수 (버튼 활성화, 텍스트 초기화 등)"""
    # 1. 승/패/버스트 결과 텍스트를 지웁니다.
    result_var.set("")
    
    # 2. 플레이어와 딜러의 카드를 초기 상태로 되돌립니다.
    player_cards_var.set("[카드 1] [카드 2]")
    dealer_cards_var.set("[카드 1] [?]")
    
    # 3. 비활성화되었던 '힛', '스탠드' 버튼을 다시 활성화합니다.
    hit_btn.config(state="normal")
    stand_btn.config(state="normal")

def player_hit(result_var, hit_btn, stand_btn):
    if random.random() < 0.3:
        result_var.set("BUST")
        result_var.get_label().config(fg="orange")
        hit_btn.config(state="disabled")
        stand_btn.config(state="disabled")

def player_stand(result_var, hit_btn, stand_btn):
    if random.random() < 0.5:
        result_var.set("WIN")
        result_var.get_label().config(fg="green")
    else:
        result_var.set("LOSE")
        result_var.get_label().config(fg="red")
    hit_btn.config(state="disabled")
    stand_btn.config(state="disabled")

def open_game_window():
    game_win = tk.Tk()
    game_win.title("♠️ Blackjack Game")
    game_win.geometry("700x500")
    game_win.configure(bg="#016D29")

    class ResultVar(tk.StringVar):
        def set_label(self, label):
            self._label = label
        def get_label(self):
            return self._label

    # --- 실시간 변경을 위한 변수(StringVar)들 생성 ---
    game_result_var = ResultVar(value="")
    # ✨ 1. 카드 표시를 위한 StringVar 생성
    player_cards_var = tk.StringVar(value="[카드 1] [카드 2]")
    dealer_cards_var = tk.StringVar(value="[카드 1] [?]")
    
    # --- 위젯 배치 ---
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
    # ✨ 2. 딜러 카드 라벨에 text 대신 textvariable 연결
    dealer_cards_label = tk.Label(dealer_frame, textvariable=dealer_cards_var, font=("Arial", 16, "bold"), pady=10, fg="white", bg="#016D29")
    dealer_cards_label.pack()
    
    player_label = tk.Label(player_frame, text="플레이어의 카드", font=("Arial", 12), fg="white", bg="#016D29")
    player_label.pack()
    # ✨ 2. 플레이어 카드 라벨에 text 대신 textvariable 연결
    player_cards_label = tk.Label(player_frame, textvariable=player_cards_var, font=("Arial", 16, "bold"), pady=10, fg="white", bg="#016D29")
    player_cards_label.pack()

    chip_label = tk.Label(control_frame, text="남은 칩: $1000", font=("Arial", 12), fg="white", bg="#016D29")
    chip_label.pack(pady=10)

    hit_button = tk.Button(control_frame, text="힛 (Hit)", font=("Arial", 14), width=10)
    hit_button.pack(side="left", padx=10)
    stand_button = tk.Button(control_frame, text="스탠드 (Stand)", font=("Arial", 14), width=10)
    stand_button.pack(side="left", padx=10)
    restart_button = tk.Button(control_frame, text="Restart", font=("Arial", 14), width=10)
    restart_button.pack(side="left", padx=10)
    
    # --- 버튼 기능 연결 ---
    hit_button.config(command=lambda: player_hit(game_result_var, hit_button, stand_button))
    stand_button.config(command=lambda: player_stand(game_result_var, hit_button, stand_button))
    # ✨ 3. Restart 버튼의 command를 새 함수와 모든 필요 인자들로 연결
    restart_button.config(command=lambda: reset_game_state(game_result_var, player_cards_var, dealer_cards_var, hit_button, stand_button))

    game_win.mainloop()

# ----------------------------------------------------------------------
# --- 2. 메인 메뉴 화면 관련 함수 ---
# (이전과 동일)
# ----------------------------------------------------------------------
def start_game(main_window):
    main_window.destroy()
    open_game_window()

def show_ranking():
    """'랭킹 보기' 버튼을 누르면 팝업 대신 새 랭킹 창을 연다."""
    open_ranking_window()

def open_main_window():
    main_win = tk.Tk()
    main_win.title("BLACK JACK 메인 화면")
    main_win.geometry("1000x600")
    
    betting_amount = tk.StringVar(value="베팅 금액: $1000") 
    betting_label = tk.Label(main_win, textvariable=betting_amount, font=("Dotum", 14, "bold"), pady=20)
    betting_label.pack(pady=10)
    start_button = tk.Button(main_win, text="게임 시작", font=("Dotum", 12), width=20, height=2, command=lambda: start_game(main_win))
    start_button.pack(pady=10)

    ranking_button = tk.Button(main_win, text="랭킹 보기", font=("Dotum", 12), width=20, height=2, command=show_ranking)
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

