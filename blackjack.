import tkinter as tk
from tkinter import messagebox
import ctypes

# =========================
# 고해상도 DPI 지원
# =========================
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# =========================
# 블랙잭 GUI (UI만, 게임 로직 제거)
# =========================
class BlackjackGUI:
    def __init__(self, root, main_window, bet_amount):
        self.main_window = main_window

        self.root = tk.Toplevel(root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("1286x886")
        self.root.configure(bg="green")

        # 메인 화면 버튼
        self.main_menu_button = tk.Button(self.root, text="메인 화면으로", width=11, height=2,
                                          font=("Arial",7,"bold"), command=self.back_to_main)
        self.main_menu_button.place(x=3, y=3)

        # 딜러 카드 프레임
        self.dealer_frame = tk.LabelFrame(self.root, text="딜러", font=("Arial",16,"bold"),
                                          fg="white", bg="green", labelanchor="n")
        self.dealer_frame.pack(fill="x", padx=20, pady=(50,10))
        self.dealer_inner_frame = tk.Frame(self.dealer_frame, bg="green")
        self.dealer_inner_frame.pack(pady=10)

        # 상태 표시
        self.status_label = tk.Label(self.root, text="게임 화면입니다.", bg="green", fg="yellow",
                                     font=("Arial",20,"bold"))
        self.status_label.pack(pady=15)

        # 플레이어 카드 프레임
        self.player_frame = tk.LabelFrame(self.root, text="플레이어", font=("Arial",16,"bold"),
                                          fg="white", bg="green", labelanchor="n")
        self.player_frame.pack(fill="x", padx=20, pady=(10,0))
        self.player_inner_frame = tk.Frame(self.player_frame, bg="green")
        self.player_inner_frame.pack(pady=10)

        # 버튼 프레임 (더미 버튼)
        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20)

        btn_names = ["더블다운", "스플릿", "스탠드", "히트", "다시하기"]
        for i, name in enumerate(btn_names):
            btn = tk.Button(self.button_frame, text=name, width=15, height=2, font=("Arial",10,"bold"),
                            command=lambda n=name: messagebox.showinfo("버튼 클릭", f"{n} 버튼 클릭됨 (기능 없음)"))
            btn.grid(row=0, column=i, padx=15)

    def back_to_main(self):
        self.root.destroy()
        self.main_window.deiconify()

# =========================
# 랭킹창
# =========================
def open_ranking_window():
    ranking_win = tk.Toplevel()
    ranking_win.title("🏆 게임 랭킹")
    ranking_win.geometry("300x400")
    ranking_win.resizable(False, False)
    tk.Label(ranking_win, text="랭킹 순위", font=("Dotum",16,"bold"), pady=15).pack()
    rankings = {
        "1. Player1":"$9,500",
        "2. Dealer":"$8,100",
        "3. AcePlayer":"$7,650",
        "4. Lucky7":"$6,200",
        "5. CardMaster":"$5,150"
    }
    for rank, (name, score) in enumerate(rankings.items(),1):
        medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else ""
        text = f"{medal} {name}: {score}"
        tk.Label(ranking_win, text=text, font=("Dotum",12), anchor="w").pack(fill="x", pady=2)
    tk.Button(ranking_win, text="닫기", command=ranking_win.destroy).pack(pady=15)

# =========================
# 메인 메뉴
# =========================
class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BLACK JACK 메인 화면")
        self.geometry("800x500")
        self.chips = 5000

        tk.Label(self, text="🎲 블랙잭에 오신 걸 환영합니다!", font=("Dotum",18,"bold"), pady=20).pack()
        self.chip_label = tk.Label(self, text=f"보유 돈: ${self.chips}", font=("Dotum",14,"bold"))
        self.chip_label.pack(pady=5)

        frame = tk.Frame(self)
        frame.pack(pady=5)

        tk.Label(frame, text="베팅 금액:").pack(side="left")
        self.bet_entry = tk.Entry(frame, width=10)
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0,"1000")

        self.charge_button = tk.Button(frame, text="돈 충전", font=("Dotum",10), command=self.charge_chips)
        self.charge_button.pack(side="left", padx=5)
        self.update_charge_button()

        tk.Button(self, text="게임 시작", font=("Dotum",14), width=20, height=2,
                  command=self.start_game).pack(pady=10)
        tk.Button(self, text="랭킹 보기", font=("Dotum",14), width=20, height=2,
                  command=open_ranking_window).pack(pady=10)

    def start_game(self):
        bet = int(self.bet_entry.get())
        if bet > self.chips:
            messagebox.showwarning("베팅 오류", "보유 돈보다 큰 금액은 베팅할 수 없습니다.")
            return
        self.withdraw()
        BlackjackGUI(self, self, bet)

    def update_chip_label(self):
        self.chip_label.config(text=f"보유 돈: ${self.chips}")
        self.update_charge_button()

    def charge_chips(self):
        if self.chips >= 5000:
            messagebox.showinfo("충전 불가", "보유 돈이 5,000 이상이므로 충전할 수 없습니다.")
        elif self.chips <= 3000:
            self.chips = 5000
            self.update_chip_label()
            messagebox.showinfo("충전 완료", "보유 돈이 5,000으로 충전되었습니다.")

    def update_charge_button(self):
        if self.chips >= 5000:
            self.charge_button.config(state="disabled")
        elif self.chips <= 3000:
            self.charge_button.config(state="normal")
        else:
            self.charge_button.config(state="disabled")

# =========================
# 로그인 창
# =========================
def attempt_login(event=None):
    username = username_entry.get()
    password = password_entry.get()
    messagebox.showinfo("로그인 성공", f"{username or '게스트'}님, 환영합니다!")
    login_win.destroy()
    MainMenu().mainloop()

if __name__=="__main__":
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

    tk.Button(main_frame, text="로그인", width=12, font=("Dotum",11,"bold"), command=attempt_login).grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum",11,"bold"), command=login_win.destroy).grid(row=2, column=1, pady=20, padx=5, sticky="w")

    login_win.bind('<Return>', attempt_login)
    login_win.mainloop()
