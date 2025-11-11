import tkinter as tk
from tkinter import messagebox
import os
import glob
from PIL import Image, ImageTk

# --- 상수 ---
IMAGE_DIR = "img" 

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
    
    for rank, (name, score) in enumerate(rank_data, 1):
        medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"{rank}."
        text = f"{medal} {name}: ${score}"
        tk.Label(ranking_win, text=text, font=("Dotum",12), anchor="w").pack(fill="x", pady=2, padx=20)

# =========================
# 메인 메뉴 (View)
# =========================
class MainMenu(tk.Tk):
    """ '순수' 메인 메뉴 UI (껍데기) """
    def __init__(self, user_data: dict):
        super().__init__()
        self.title("BLACK JACK 메인 화면")
        self.geometry("800x500")
        
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

        # [중요] command 제거! (Controller가 설정할 것)
        self.charge_button = tk.Button(frame, text="돈 충전 (+100)", font=("Dotum",10))
        self.charge_button.pack(side="left", padx=5)

        self.start_game_button = tk.Button(self, text="게임 시작", font=("Dotum",14), width=20, height=2)
        self.start_game_button.pack(pady=10)
        
        self.ranking_button = tk.Button(self, text="랭킹 보기", font=("Dotum",14), width=20, height=2)
        self.ranking_button.pack(pady=10) 
        
        self.logout_button = tk.Button(self, text="로그아웃", font=("Dotum", 14), width=20, height=2)
        self.logout_button.pack(pady=10)

    def update_chip_label(self, new_chips):
        """ [View] 컨트롤러의 요청을 받아 칩 라벨 업데이트 """
        self.chips = new_chips
        self.chip_label.config(text=f"보유 돈: ${self.chips}")

# =========================
# 블랙잭 GUI (View)
# =========================
class BlackjackGUI:
    """ '순수' 블랙잭 게임 UI (껍데기) """
    def __init__(self, main_menu_root, user_data: dict, bet_amount: int, current_bankroll: int):
        
        self.main_window = main_menu_root
        self.root = tk.Toplevel(main_menu_root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("1286x886")
        self.root.configure(bg="green")
        
        # [중요] 로직(모델) 객체 생성 제거!
        # self.game = gc.BlackjackGame() ➡️ 삭제 (Controller가 담당)
        
        self.card_images = self.load_card_images()
        self.current_dealer_hand_hidden = [] 

        # [중요] command 제거! (Controller가 설정할 것)
        self.main_menu_button = tk.Button(self.root, text="메인 화면으로", width=11, height=2, font=("Arial",7,"bold"))
        self.main_menu_button.place(x=3, y=3)

        self.dealer_frame = tk.LabelFrame(self.root, text="딜러", font=("Arial",16,"bold"), fg="white", bg="green", labelanchor="n")
        self.dealer_frame.pack(fill="x", padx=20, pady=(50,10))
        self.dealer_inner_frame = tk.Frame(self.dealer_frame, bg="green")
        self.dealer_inner_frame.pack(pady=10)

        self.status_label = tk.Label(self.root, text="베팅 완료! Hit / Stand를 선택하세요.", bg="green", fg="yellow", font=("Arial",20,"bold"))
        self.status_label.pack(pady=15)

        self.player_frame = tk.LabelFrame(self.root, text="플레이어", font=("Arial",16,"bold"), fg="white", bg="green", labelanchor="n")
        self.player_frame.pack(fill="x", padx=20, pady=(10,0))
        self.player_inner_frame = tk.Frame(self.player_frame, bg="green")
        self.player_inner_frame.pack(pady=10)

        # [중요] 칩 계산 로직 제거! (Controller가 계산한 값을 받아옴)
        self.chip_label = tk.Label(self.root, text=f"남은 돈: ${current_bankroll - bet_amount} (베팅: ${bet_amount})", bg="green", fg="white", font=("Arial",16,"bold"))
        self.chip_label.pack(pady=10)

        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20)

        btn_width = 15
        btn_height = 2
        btn_font = ("Arial", 10, "bold")

        # [중요] command 제거! (Controller가 설정할 것)
        self.double_button = tk.Button(self.button_frame, text="더블다운", width=btn_width, height=btn_height, font=btn_font, state="disabled")
        self.double_button.grid(row=0, column=0, padx=30)
        
        self.split_button = tk.Button(self.button_frame, text="스플릿", width=btn_width, height=btn_height, font=btn_font, state="disabled")
        self.split_button.grid(row=0, column=1, padx=30)
        
        self.stand_button = tk.Button(self.button_frame, text="스탠드", width=btn_width, height=btn_height, font=btn_font, state="normal")
        self.stand_button.grid(row=0, column=2, padx=30)
        
        self.hit_button = tk.Button(self.button_frame, text="히트", width=btn_width, height=btn_height, font=btn_font, state="normal")
        self.hit_button.grid(row=0, column=3, padx=30)
        
        self.reset_button = tk.Button(self.button_frame, text="다시하기", width=btn_width, height=btn_height, font=btn_font, state="disabled")
        self.reset_button.grid(row=0, column=4, padx=30)

    def load_card_images(self):
        """ [View] 카드 이미지 로드 (이건 View의 책임) """
        images = {}
        card_size = (100, 150) 
        
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
        
        if not image_paths:
            print(f"경고: '{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다. (예: S_A.png)")
            messagebox.showwarning("이미지 오류", f"'{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
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
        
        for widget in self.player_inner_frame.winfo_children():
            widget.destroy()
        for widget in self.dealer_inner_frame.winfo_children():
            widget.destroy()

        for card in player_hand:
            card_name = str(card)
            if card_name in self.card_images:
                tk.Label(self.player_inner_frame, image=self.card_images[card_name], bg="green").pack(side=tk.LEFT, padx=5)
            else:
                tk.Label(self.player_inner_frame, text=card_name, font=("Arial", 16), bg="green", fg="white").pack(side=tk.LEFT, padx=5)

        for card in dealer_hand:
            card_name = "BACK" if card == '?' else str(card)
            if card_name in self.card_images:
                tk.Label(self.dealer_inner_frame, image=self.card_images[card_name], bg="green").pack(side=tk.LEFT, padx=5)
            else:
                tk.Label(self.dealer_inner_frame, text=card_name, font=("Arial", 16), bg="green", fg="white").pack(side=tk.LEFT, padx=5)

# =========================
# 로그인 창 (View)
# =========================
def main_login_window():
    """ 로그인 UI 생성 """
    global login_win, username_entry, password_entry # (Controller에서 접근해야 하므로 global 유지)

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

    tk.Button(main_frame, text="회원가입", width=12, font=("Dotum",11,"bold")).grid(row=2, column=1, pady=20, padx=5, sticky="w")
    tk.Button(main_frame, text="로그인", width=12, font=("Dotum",11,"bold")).grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum",11,"bold"), command=login_win.destroy).grid(row=2, column=2, pady=20, padx=5, sticky="w") 

    return login_win, username_entry, password_entry