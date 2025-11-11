import tkinter as tk
from tkinter import messagebox
import hashlib
import os
import sqlite3

# [중요] 같은 폴더 레벨의 'view'와 'model'을 임포트합니다.
import src.model.database as db
import src.model.game_logic as gc
import src.view.ui_view as view # UI 클래스를 임포트

# --- 상수 ---
DB_NAME = db.DB_FILE

# --- 1. DB 초기화 로직 ---
def setup_database():
    """ 프로그램 시작 시 DB와 테이블을 초기화합니다. """
    try:
        conn = sqlite3.connect(DB_NAME) 
        db.initialize_db(conn) 
        conn.close()
    except Exception as e:
        print(f"DB 초기화 실패: {e}")
        messagebox.showerror("치명적 오류", f"DB 초기화 실패: {e}\n프로그램을 종료합니다.")
        return False
    return True

# --- 2. 로그인/회원가입 로직 ---
class AuthController:
    """ 로그인/회원가입 '컨트롤러' """
    def __init__(self):
        # View(UI)에서 사용할 Entry 위젯들을 저장할 변수
        self.username_entry = None
        self.password_entry = None
        self.login_win = None

    def start_login_window(self):
        """ 로그인 창을 '생성'하고 '이벤트'를 '연결'합니다. """
        # 'view.ui_view'에 정의된 '순수 UI' 함수를 호출
        self.login_win, self.username_entry, self.password_entry = view.main_login_window()
        
        # 'view'의 버튼들에 'controller'의 함수를 '연결(bind)'
        self.login_win.bind('<Return>', self.handle_login_click)
        
        # 'view'가 아닌 'controller'에서 버튼을 찾아 command를 설정
        for widget in self.login_win.winfo_children()[0].winfo_children():
            if widget.cget("text") == "회원가입":
                widget.config(command=self.handle_signup_click)
            elif widget.cget("text") == "로그인":
                widget.config(command=self.handle_login_click)
        
        self.login_win.mainloop()

    def handle_signup_click(self):
        """ [컨트롤러] 회원가입 로직 """
        username = self.username_entry.get()
        password = self.password_entry.get()
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

    def handle_login_click(self, event=None):
        """ [컨트롤러] 로그인 로직 """
        username = self.username_entry.get()
        password = self.password_entry.get()
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
                self.login_win.destroy() # 로그인창 닫기
                
                user_data = {
                    "id": user_id,
                    "username": username,
                    "bankroll": bankroll
                }
                
                # [흐름] 로그인 성공 시 '메인메뉴 컨트롤러' 실행
                main_menu_controller = MainMenuController(user_data)
                main_menu_controller.start_main_menu()
                
            else:
                messagebox.showerror("실패", "비밀번호가 틀렸습니다.")

        except Exception as e:
            messagebox.showerror("DB 오류", f"오류 발생: {e}")

# --- 3. 메인메뉴 로직 ---
class MainMenuController:
    """ 메인 메뉴 '컨트롤러' """
    def __init__(self, user_data: dict):
        self.user_data = user_data
        self.chips = user_data["bankroll"]
        self.view = None # 'view.MainMenu' 클래스 인스턴스가 저장될 곳

    def start_main_menu(self):
        """ 메인 메뉴를 '생성'하고 '이벤트'를 '연결'합니다. """
        # 'view.ui_view'의 'MainMenu' UI 클래스 생성
        self.view = view.MainMenu(self.user_data)
        
        # 'view'의 버튼들에 'controller'의 함수를 '연결(bind)'
        self.view.charge_button.config(command=self.charge_chips)
        self.view.start_game_button.config(command=self.start_game)
        self.view.ranking_button.config(command=self.open_ranking) # 랭킹창도 컨트롤러 경유
        self.view.logout_button.config(command=self.handle_logout)
        
        self.view.mainloop()

    def start_game(self):
        """ [컨트롤러] 게임 시작 로직 """
        try:
            bet = int(self.view.bet_entry.get())
        except ValueError:
            messagebox.showwarning("베팅 오류", "베팅액은 숫자로 입력하세요.")
            return
        
        if bet <= 0:
            messagebox.showwarning("베팅 오류", "베팅액은 0보다 커야 합니다.")
            return
        if bet > self.chips:
            messagebox.showwarning("베팅 오류", "보유 돈보다 큰 금액은 베팅할 수 없습니다.")
            return
        
        self.view.withdraw() # 메인메뉴(View) 숨기기
        
        # [흐름] '게임 컨트롤러' 실행
        game_controller = GameController(self.view, self.user_data, bet)
        game_controller.start_game_window()

    def charge_chips(self):
        """ [컨트롤러] 칩 충전 로직 """
        new_bankroll = self.chips + 100 
        
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_bankroll(conn, self.user_data["id"], new_bankroll)
            conn.close()
            
            self.chips = new_bankroll
            # 'view'에 칩 업데이트 '요청'
            self.view.update_chip_label(self.chips) 
            messagebox.showinfo("충전 완료", "100칩이 충전되었습니다.")
            
        except Exception as e:
            messagebox.showerror("DB 오류", f"충전 실패: {e}")

    def handle_logout(self):
        """ [컨트롤러] 로그아웃 로직 """
        self.view.destroy() 
        # [흐름] '로그인 컨트롤러' 다시 실행
        auth_controller = AuthController()
        auth_controller.start_login_window()
        
    def open_ranking(self):
        """ [컨트롤러] 랭킹창 로직 """
        # 'view'의 랭킹창 UI 생성
        ranking_win = view.open_ranking_window()
        
        # 'controller'가 DB에서 데이터를 가져옴
        try:
            conn = sqlite3.connect(DB_NAME)
            rank_data = db.get_ranking(conn) 
            conn.close()
            
            # 'view'에 데이터 채워넣기
            view.populate_ranking_data(ranking_win, rank_data)
            
        except Exception as e:
            messagebox.showerror("DB 오류", f"랭킹 로드 실패: {e}")


# --- 4. 블랙잭 게임 로직 ---
class GameController:
    """ 블랙잭 게임 '컨트롤러' """
    def __init__(self, main_menu_view, user_data: dict, bet_amount: int):
        self.main_window_view = main_menu_view # 메인메뉴 View
        self.user_data = user_data
        self.bet_amount = bet_amount
        self.game_is_over = False
        
        # '모델'('룰') 객체 생성
        self.game_model = gc.BlackjackGame() 
        self.current_bankroll = user_data["bankroll"]
        
        self.view = None # 'view.BlackjackGUI' 인스턴스가 저장될 곳

    def start_game_window(self):
        """ 게임 창을 '생성'하고 '이벤트'를 '연결'합니다. """
        # 'view.ui_view'의 'BlackjackGUI' UI 클래스 생성
        self.view = view.BlackjackGUI(self.main_window_view, self.user_data, self.bet_amount, self.current_bankroll)
        
        # 'view'의 버튼들에 'controller'의 함수를 '연결(bind)'
        self.view.root.protocol("WM_DELETE_WINDOW", self.back_to_main)
        self.view.main_menu_button.config(command=self.back_to_main)
        self.view.stand_button.config(command=self.handle_stand)
        self.view.hit_button.config(command=self.handle_hit)
        self.view.reset_button.config(command=self.reset_game)

        # 게임 시작 (컨트롤러가 모델과 뷰를 조작)
        self.start_new_game()

    def start_new_game(self):
        """ [컨트롤러] 새 게임 시작 로직 """
        # '모델'('룰') 호출
        initial_state = self.game_model.start_game(bet=self.bet_amount)
        
        # '뷰'에 카드 그리기 '요청'
        self.view.update_gui_cards(initial_state['player_hand'], initial_state['dealer_hand_hidden'])
        
        # '뷰'에 상태 업데이트 '요청'
        player_score = self.game_model.calculate_score(initial_state['player_hand'])
        self.view.status_label.config(text=f"플레이어 점수: {player_score}. Hit / Stand?")

    def handle_hit(self):
        """ [컨트롤러] Hit 로직 """
        hit_result = self.game_model.player_hit()
        
        self.view.update_gui_cards(hit_result['player_hand'], self.view.current_dealer_hand_hidden)
        self.view.status_label.config(text=f"새 카드! 현재 점수: {hit_result['score']}")

        if hit_result['status'] == 'Bust':
            self.view.status_label.config(text=f"Bust! (점수: {hit_result['score']}) 😭")
            self.finalize_game(result="Lose (Bust)", payout=-self.bet_amount)

    def handle_stand(self):
        """ [컨트롤러] Stand 로직 """
        dealer_final_hand = self.game_model.dealer_turn()
        self.view.update_gui_cards(self.game_model.player_hand, dealer_final_hand)
        
        final_result = self.game_model.check_result()
        
        result_msg = final_result['result_msg']
        p_score = final_result['player_score']
        d_score = final_result['dealer_score']
        self.view.status_label.config(text=f"결과: {result_msg}! (플레이어: {p_score} vs 딜러: {d_score})")

        self.finalize_game(result=final_result['result_msg'], payout=final_result['payout'])

    def finalize_game(self, result: str, payout: int):
        """ [컨트롤러] 게임 종료 및 DB 저장 로직 """
        if self.game_is_over: 
            return
        self.game_is_over = True 

        # '뷰'의 버튼 상태 업데이트 '요청'
        self.view.hit_button.config(state="disabled")
        self.view.stand_button.config(state="disabled")
        self.view.reset_button.config(state="normal") 

        # '컨트롤러'가 칩 계산
        self.current_bankroll += payout
        
        # '뷰'에 칩 라벨 업데이트 '요청'
        emoji = "🎉" if payout > 0 else "💸" if payout < 0 else "🤝"
        self.view.chip_label.config(text=f"남은 돈: ${self.current_bankroll} (결과: {payout:+} {emoji})")
        
        # '컨트롤러'가 DB('모델')에 저장
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
            db.save_game(conn, self.user_data['id'], self.bet_amount, result, payout)
            conn.close()
        except Exception as e:
            messagebox.showerror("DB 오류", f"게임 결과 저장 실패: {e}")
    
    def reset_game(self):
        self.back_to_main() 

    def back_to_main(self):
        """ [컨트롤러] 메인 메뉴 복귀 로직 """
        if not self.game_is_over:
            try:
                conn = sqlite3.connect(DB_NAME)
                db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
                conn.close()
            except Exception as e:
                messagebox.showerror("DB 오류", f"칩 저장 실패: {e}")
        
        self.view.root.destroy()
        # 부모 View('메인메뉴')의 칩 상태 업데이트 '요청'
        self.main_window_view.chips = self.current_bankroll
        self.main_window_view.update_chip_label(self.current_bankroll) 
        self.main_window_view.deiconify()