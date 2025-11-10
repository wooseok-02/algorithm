import tkinter as tk
from tkinter import messagebox
import ctypes

import hashlib
import os
import sqlite3
import src.model.database as db
import src.model.game_logic as gc # 게임 컨트롤러 임포트

# [추가] 5단계: Pillow(PIL) 라이브러리 임포트
from PIL import Image, ImageTk
import glob # 이미지 파일을 쉽게 찾기 위해

# =========================
# 고해상도 DPI 지원 (Windows 전용)
# =========================
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# =========================
# DB 이름
# =========================
DB_NAME = db.DB_FILE
IMAGE_DIR = "img" # [추가] 5단계: 이미지 폴더 경로

# =========================
# 랭킹창 
# =========================
def open_ranking_window():
    ranking_win = tk.Toplevel()
    ranking_win.title("🏆 게임 랭킹")
    ranking_win.geometry("300x400")
    ranking_win.resizable(False, False)
    tk.Label(ranking_win, text="랭킹 순위", font=("Dotum",16,"bold"), pady=15).pack()

    # [추가] DB에서 랭킹 가져오기
    try:
        conn = sqlite3.connect(DB_NAME)
        rank_data = db.get_ranking(conn) 
        conn.close()
        
        if not rank_data:
            tk.Label(ranking_win, text="아직 랭킹이 없습니다.", font=("Dotum",12)).pack(pady=5)
        
        for rank, (name, score) in enumerate(rank_data, 1):
            medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"{rank}."
            text = f"{medal} {name}: ${score}"
            tk.Label(ranking_win, text=text, font=("Dotum",12), anchor="w").pack(fill="x", pady=2, padx=20)
            
    except Exception as e:
        messagebox.showerror("DB 오류", f"랭킹 로드 실패: {e}")

    tk.Button(ranking_win, text="닫기", command=ranking_win.destroy).pack(pady=15)

# =========================
# (이식 2) 메인 메뉴 (UI 이식 + '진짜' DB 연동)
# =========================
class MainMenu(tk.Tk):

    def __init__(self, user_data: dict):

        super().__init__()
        self.title("BLACK JACK 메인 화면")
        self.geometry("800x500")
        
        self.user_data = user_data
        self.chips = user_data["bankroll"] 

        tk.Label(self, text=f"🎲 {self.user_data['username']}님, 환영합니다!", font=("Dotum",18,"bold"), pady=20).pack()
        self.chip_label = tk.Label(self, text=f"보유 돈: ${self.chips}", font=("Dotum",14,"bold"))
        self.chip_label.pack(pady=5)

        frame = tk.Frame(self)
        frame.pack(pady=5)

        tk.Label(frame, text="베팅 금액:").pack(side="left")
        self.bet_entry = tk.Entry(frame, width=10)
        self.bet_entry.pack(side="left", padx=5)
        self.bet_entry.insert(0,"100") 

        self.charge_button = tk.Button(frame, text="돈 충전 (+100)", font=("Dotum",10), command=self.charge_chips)
        self.charge_button.pack(side="left", padx=5)

        tk.Button(self, text="게임 시작", font=("Dotum",14), width=20, height=2,
                  command=self.start_game).pack(pady=10)
        tk.Button(self, text="랭킹 보기", font=("Dotum",14), width=20, height=2,
                  command=open_ranking_window).pack(pady=10) 
        tk.Button(self, text="로그아웃", font=("Dotum", 14), width=20, height=2,
                  command=self.handle_logout).pack(pady=10)

    def start_game(self):
        """ [수정됨] '진짜' BlackjackGUI를 호출하도록 변경 """
        try:
            bet = int(self.bet_entry.get())
        except ValueError:
            messagebox.showwarning("베팅 오류", "베팅액은 숫자로 입력하세요.")
            return
        
        if bet <= 0:
            messagebox.showwarning("베팅 오류", "베팅액은 0보다 커야 합니다.")
            return
        if bet > self.chips:
            messagebox.showwarning("베팅 오류", "보유 돈보다 큰 금액은 베팅할 수 없습니다.")
            return
        
        self.withdraw() # 메인메뉴 숨기기
        
        BlackjackGUI(self, self.user_data, bet)

    def update_chip_label(self):
        self.chip_label.config(text=f"보유 돈: ${self.chips}")

    def charge_chips(self):
        new_bankroll = self.chips + 100 
        
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_bankroll(conn, self.user_data["id"], new_bankroll)
            conn.close()
            
            self.chips = new_bankroll
            self.update_chip_label()
            messagebox.showinfo("충전 완료", "100칩이 충전되었습니다.")
            
        except Exception as e:
            messagebox.showerror("DB 오류", f"충전 실패: {e}")

    def handle_logout(self):
        """ [추가] 로그아웃 시 로그인 창으로 복귀 """
        self.destroy() 
        main_login_window() 

# =========================
# 블랙잭 GUI
# =========================
class BlackjackGUI:
    def __init__(self, main_menu_root, user_data: dict, bet_amount: int):
        
        self.main_window = main_menu_root
        self.user_data = user_data
        self.bet_amount = bet_amount
        self.game_is_over = False

        self.root = tk.Toplevel(main_menu_root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("1286x886")
        self.root.configure(bg="green")
        
        self.game = gc.BlackjackGame() 
        self.current_bankroll = user_data["bankroll"]
        
        self.root.protocol("WM_DELETE_WINDOW", self.back_to_main)

        # [추가] 5단계: 카드 이미지 미리 로드
        self.card_images = self.load_card_images()
        self.current_dealer_hand_hidden = [] # 딜러의 숨겨진 패 저장용

        self.main_menu_button = tk.Button(self.root, text="메인 화면으로", width=11, height=2, font=("Arial",7,"bold"), command=self.back_to_main)
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

        self.current_bankroll -= self.bet_amount 
        self.chip_label = tk.Label(self.root, text=f"남은 돈: ${self.current_bankroll} (베팅: ${self.bet_amount})", bg="green", fg="white", font=("Arial",16,"bold"))
        self.chip_label.pack(pady=10)

        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20)

        btn_width = 15
        btn_height = 2
        btn_font = ("Arial", 10, "bold")

        self.double_button = tk.Button(self.button_frame, text="더블다운", width=btn_width, height=btn_height, font=btn_font, state="disabled")
        self.double_button.grid(row=0, column=0, padx=30)
        
        self.split_button = tk.Button(self.button_frame, text="스플릿", width=btn_width, height=btn_height, font=btn_font, state="disabled")
        self.split_button.grid(row=0, column=1, padx=30)
        
        self.stand_button = tk.Button(self.button_frame, text="스탠드", width=btn_width, height=btn_height, font=btn_font, command=self.handle_stand, state="normal")
        self.stand_button.grid(row=0, column=2, padx=30)
        
        self.hit_button = tk.Button(self.button_frame, text="히트", width=btn_width, height=btn_height, font=btn_font, command=self.handle_hit, state="normal")
        self.hit_button.grid(row=0, column=3, padx=30)
        
        self.reset_button = tk.Button(self.button_frame, text="다시하기", width=btn_width, height=btn_height, font=btn_font, command=self.reset_game, state="disabled")
        self.reset_button.grid(row=0, column=4, padx=30)
        
        self.start_new_game()

    # [추가] 5단계: Pillow 이미지 로드 함수
    def load_card_images(self):
        """ 'img/' 폴더에서 카드 이미지를 로드하여 딕셔너리로 반환 """
        images = {}
        # 이미지 크기 조절 (예: 100x150)
        card_size = (100, 150) 
        
        # 'img/*.png' 패턴으로 모든 png 파일 경로를 가져옴
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
        
        if not image_paths:
            print(f"경고: '{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다. (예: S_A.png)")
            return {}
            
        for path in image_paths:
            filename = os.path.basename(path) # 'S_A.png'
            card_name = filename.split('.')[0] # 'S_A'
            
            try:
                # Pillow로 이미지 열기, 리사이즈, Tkinter용 이미지로 변환
                img = Image.open(path).resize(card_size)
                images[card_name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"이미지 로드 실패: {path} / {e}")
        
        if "BACK" not in images:
            print(f"경고: '{IMAGE_DIR}/BACK.png' (뒷면) 이미지를 찾을 수 없습니다.")
            
        return images

    # [추가] 5단계: 카드 이미지를 GUI에 그리는 함수
    def update_gui_cards(self, player_hand, dealer_hand):
        """ 딜러와 플레이어의 프레임을 지우고 카드를 새로 그림 """
        # 1. 기존 카드 이미지 모두 삭제
        for widget in self.player_inner_frame.winfo_children():
            widget.destroy()
        for widget in self.dealer_inner_frame.winfo_children():
            widget.destroy()

        # 2. 플레이어 카드 그리기
        for card in player_hand: # card는 'S_A' 같은 Card 객체
            card_name = str(card)
            if card_name in self.card_images:
                # 이미지가 있으면 Label에 이미지 추가
                tk.Label(self.player_inner_frame, image=self.card_images[card_name], bg="green").pack(side=tk.LEFT, padx=5)
            else:
                # (Fallback) 이미지가 없으면 텍스트로 표시
                tk.Label(self.player_inner_frame, text=card_name, font=("Arial", 16), bg="green", fg="white").pack(side=tk.LEFT, padx=5)

        # 3. 딜러 카드 그리기
        for card in dealer_hand: # card는 '?' 또는 Card 객체
            card_name = "BACK" if card == '?' else str(card)
            if card_name in self.card_images:
                tk.Label(self.dealer_inner_frame, image=self.card_images[card_name], bg="green").pack(side=tk.LEFT, padx=5)
            else:
                # (Fallback) 이미지가 없으면 텍스트로 표시
                tk.Label(self.dealer_inner_frame, text=card_name, font=("Arial", 16), bg="green", fg="white").pack(side=tk.LEFT, padx=5)

    def start_new_game(self):
        """ [수정됨] 5단계: print() 대신 GUI 카드 그리기 호출 """
        initial_state = self.game.start_game(bet=self.bet_amount)
        # print(...) ➡️ 삭제
        
        # [수정] 5단계: 딜러의 숨겨진 패를 저장 (Hit 시 필요)
        self.current_dealer_hand_hidden = initial_state['dealer_hand_hidden']
        
        # [수정] 5단계: 카드 이미지 그리기 함수 호출
        self.update_gui_cards(initial_state['player_hand'], self.current_dealer_hand_hidden)
        
        # [추가] 5단계: 점수도 status_label에 표시
        player_score = self.game.calculate_score(initial_state['player_hand'])
        self.status_label.config(text=f"플레이어 점수: {player_score}. Hit / Stand?")

    def handle_hit(self):
        """ [수정됨] 5단계: print() 대신 GUI 카드/상태 업데이트 """
        hit_result = self.game.player_hit()
        # print(...) ➡️ 삭제
        
        # [수정] 5단계: 카드 이미지 새로 그리기
        self.update_gui_cards(hit_result['player_hand'], self.current_dealer_hand_hidden)
        
        # [수정] 5단계: 상태 라벨 업데이트
        self.status_label.config(text=f"새 카드! 현재 점수: {hit_result['score']}")

        if hit_result['status'] == 'Bust':
            self.status_label.config(text=f"Bust! (점수: {hit_result['score']}) 😭")
            self.finalize_game(result="Lose (Bust)", payout=-self.bet_amount)

    def handle_stand(self):
        """ [수정됨] 5단계: print() 대신 GUI 카드/상태 업데이트 """
        # print(...) ➡️ 삭제
        
        dealer_final_hand = self.game.dealer_turn()
        # print(...) ➡️ 삭제
        
        # [수정] 5단계: 딜러의 최종 패를 포함하여 카드 새로 그리기
        self.update_gui_cards(self.game.player_hand, dealer_final_hand)
        
        final_result = self.game.check_result()
        # print(...) ➡️ 삭제
        
        # [수정] 5단계: 최종 결과 GUI에 표시
        result_msg = final_result['result_msg']
        p_score = final_result['player_score']
        d_score = final_result['dealer_score']
        self.status_label.config(text=f"결과: {result_msg}! (플레이어: {p_score} vs 딜러: {d_score})")

        self.finalize_game(result=final_result['result_msg'], payout=final_result['payout'])

    def finalize_game(self, result: str, payout: int):
        """ [수정됨] 4단계: DB 저장 로직 (수정 없음) """
        
        if self.game_is_over: 
            return
        self.game_is_over = True 

        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")
        self.reset_button.config(state="normal") 

        self.current_bankroll += payout
        # [수정] 5단계: 칩 라벨에 승패 이모지 추가
        emoji = "🎉" if payout > 0 else "💸" if payout < 0 else "🤝"
        self.chip_label.config(text=f"남은 돈: ${self.current_bankroll} (결과: {payout:+} {emoji})")
        
        # [수정] 4단계: DB 저장 (print만 삭제)
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
            db.save_game(conn, self.user_data['id'], self.bet_amount, result, payout)
            conn.close()
            # print(...) ➡️ 삭제 (GUI로 확인되니까)
        except Exception as e:
            messagebox.showerror("DB 오류", f"게임 결과 저장 실패: {e}")
    
    def reset_game(self):
        """ 게임 판 리셋 (메인화면으로 복귀) """
        self.back_to_main() 

    def back_to_main(self):
        """ [수정됨] 4단계: 메인 메뉴 복귀 시, 칩 DB 저장 (수정 없음) """
        
        if not self.game_is_over:
            try:
                conn = sqlite3.connect(DB_NAME)
                db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
                conn.close()
                # print(...) ➡️ 삭제
            except Exception as e:
                messagebox.showerror("DB 오류", f"칩 저장 실패: {e}")
        
        self.root.destroy()
        self.main_window.chips = self.current_bankroll
        self.main_window.update_chip_label() 
        self.main_window.deiconify()         

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

# =========================
# 회원가입
# =========================
def handle_signup_click():
    """ (우석의 원본 코드. 수정 없음) """
    username = username_entry.get()
    password = password_entry.get()
    if not username or not password:
        messagebox.showerror("오류", "ID와 비밀번호를 모두 입력하세요.")
        return

    salt = os.urandom(16) 
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000
    )

    try:
        conn = sqlite3.connect(DB_NAME)
        success = db.create_user(conn, username, hashed_password, salt)
        conn.close()

        if success:
            messagebox.showinfo("성공", "회원가입 성공! 이제 로그인하세요.")
        else:
            messagebox.showerror("오류", "이미 존재하는 ID입니다.")
    except Exception as e:
        messagebox.showerror("DB 오류", f"오류 발생: {e}")

# =========================
# 로그인
# =========================
def handle_login_click(event=None):
    """ [수정됨] 로그인 성공 시 MainMenu를 호출 """
    username = username_entry.get()
    password = password_entry.get()
    if not username or not password:
        messagebox.showerror("오류", "ID와 비밀번호를 모두 입력하시오.")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        user_record = db.get_user_by_username(conn, username)
        conn.close()

        if user_record is None:
            messagebox.showerror("실패", "존재하지 않는 ID입니다.")
            return

        user_id, stored_hash, salt, bankroll = user_record
        provided_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, 100000
        )

        if provided_hash == stored_hash:
            messagebox.showinfo("로그인 성공", f"{username}님, 환영합니다!")
            login_win.destroy() 
            
            user_data = {
                "id": user_id,
                "username": username,
                "bankroll": bankroll
            }
            
            MainMenu(user_data).mainloop() 
            
        else:
            messagebox.showerror("실패", "비밀번호가 틀렸습니다.")

    except Exception as e:
        messagebox.showerror("DB 오류", f"오류 발생: {e}")

# =========================
# 프로그램 실행
# =========================
def setup_database():
    conn = sqlite3.connect(db.DB_FILE) 
    db.initialize_db(conn) 
    conn.close()

# =========================
# 프로그램 실행
# =========================
if __name__ == "__main__":
    setup_database()    
    main_login_window()