import tkinter as tk
from tkinter import messagebox
import hashlib
import os
import sqlite3

# [중요] 같은 폴더 레벨의 'view'와 'model'을 임포트합니다.
import copy
import src.model.database as db
import src.model.new_logic as gc
import src.view.new_view as view # UI 클래스를 임포트

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
        self.username_entry = None
        self.password_entry = None
        self.login_win = None

    def start_login_window(self):
        """ 로그인 창을 '생성'하고 '이벤트'를 '연결'합니다. """
        self.login_win, self.username_entry, self.password_entry = view.main_login_window()
        
        self.login_win.bind('<Return>', self.handle_login_click)
        
        # 'view'가 아닌 'controller'에서 버튼을 찾아 command를 설정
        # (view.main_login_window가 반환한 login_win의 첫 번째 자식 프레임 내 위젯을 탐색)
        # 이 프레임은 'main_frame'입니다.
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
                self.login_win.withdraw() # 로그인창을 닫지 않고 숨김 (Toplevel 생성을 위해)
                
                user_data = {
                    "id": user_id,
                    "username": username,
                    "bankroll": bankroll
                }
                
                # [흐름] 로그인 성공 시 '메인메뉴 컨트롤러' 실행
                # View의 MainMenu가 tk.Toplevel로 바뀌었으므로, 부모 윈도우(login_win)를 전달합니다.
                main_menu_controller = MainMenuController(self.login_win, user_data)
                main_menu_controller.start_main_menu()
                
            else:
                messagebox.showerror("실패", "비밀번호가 틀렸습니다.")

        except Exception as e:
            messagebox.showerror("DB 오류", f"오류 발생: {e}")

# --- 3. 메인메뉴 로직 ---
class MainMenuController:
    """ 메인 메뉴 '컨트롤러' """
    # 생성자 시그니처 수정: master_win 인수를 추가하여 부모 위젯을 받음
    def __init__(self, master_win: tk.Tk, user_data: dict):
        self.master_win = master_win # 부모 위젯 (로그인 창)
        self.user_data = user_data
        self.chips = user_data["bankroll"]
        self.view = None 

    def start_main_menu(self):
        """ 메인 메뉴를 '생성'하고 '이벤트'를 '연결'합니다. """
        # View의 MainMenu가 Toplevel로 바뀌었으므로 master_win을 전달합니다.
        self.view = view.MainMenu(self.master_win, self.user_data)
        
        # 'view'의 버튼들에 'controller'의 함수를 '연결(bind)'
        self.view.charge_button.config(command=self.charge_chips)
        self.view.start_game_button.config(command=self.start_game)
        self.view.ranking_button.config(command=self.open_ranking) 
        self.view.logout_button.config(command=self.handle_logout)

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
            self.view.update_chip_label(self.chips) 
            messagebox.showinfo("충전 완료", "100칩이 충전되었습니다.")
            
        except Exception as e:
            messagebox.showerror("DB 오류", f"충전 실패: {e}")

    def handle_logout(self):
        """ [컨트롤러] 로그아웃 로직 """
        self.view.destroy() # 메인메뉴 닫기
        self.master_win.destroy() # 부모 윈도우(숨겨진 로그인창)도 닫기
        
        # [흐름] '로그인 컨트롤러' 다시 실행 (새로운 Tkinter 루트 윈도우를 생성)
        auth_controller = AuthController()
        auth_controller.start_login_window()
        
    def open_ranking(self):
        """ [컨트롤러] 랭킹창 로직 """
        # 'view'의 랭킹창 UI 생성 (Toplevel 객체를 받음)
        ranking_win, data_frame = view.open_ranking_window()
        
        # 'controller'가 DB에서 데이터를 가져옴
        try:
            conn = sqlite3.connect(DB_NAME)
            rank_data = db.get_ranking(conn) 
            conn.close()
            
            # 'view'에 데이터 채워넣기 (데이터 프레임을 함께 전달)
            view.populate_ranking_data(data_frame, rank_data)
            
        except Exception as e:
            messagebox.showerror("DB 오류", f"랭킹 로드 실패: {e}")

# --- 4. 블랙잭 게임 로직 (최종 수정 버전) ---
class GameController:
    """ 블랙잭 게임 '컨트롤러' """
    def __init__(self, main_menu_view: view.MainMenu, user_data: dict, bet_amount: int):
        self.main_window_view = main_menu_view # 메인메뉴 View (부모)
        self.user_data = user_data
        self.bet_amount = bet_amount
        self.game_is_over = False
        self.player_stood = False 
        self.npc_final_settlement = {} # NPC 정산 결과를 저장할 변수
        self.current_npc_visible_hands = {}
        self.current_npc_dialogues = {}
        self.force_action_pending = False
        self.item_used_this_round = False

        # '모델'('룰') 객체 생성
        self.game_model = gc.BlackjackGame() 
        self.current_bankroll = user_data["bankroll"]
        
        self.view = None 

    def start_game_window(self):
        """ 게임 창을 '생성'하고 '이벤트'를 '연결'합니다. """
        # View의 BlackjackGUI 생성 시 부모 뷰(main_menu_view)를 전달합니다.
        self.view = view.BlackjackGUI(self.main_window_view, self.user_data, self.bet_amount, self.current_bankroll)
        
        self.view.root.protocol("WM_DELETE_WINDOW", self.back_to_main)
        self.view.main_menu_button.config(command=self.back_to_main)
        self.view.stand_button.config(command=self.handle_stand)
        self.view.hit_button.config(command=self.handle_hit)
        self.view.reset_button.config(command=self.reset_game)

        # 🌟 L-20: 아이템 버튼 연결
        self.view.item_low_button.config(command=lambda: self.handle_item_use('item_low'))
        self.view.item_high_button.config(command=lambda: self.handle_item_use('item_high'))

        self.start_new_game()

    def start_new_game(self):
        """ [컨트롤러] 새 게임 시작 로직 """
        self.game_is_over = False
        self.player_stood = False
        self.force_action_pending = False
        self.item_used_this_round = False
        self.view.set_item_button_state("normal") # 아이템 버튼 활성화

        # '모델'('룰') 호출
        initial_state = self.game_model.start_game(bet=self.bet_amount)
        
        # 🌟 View에 카드 그리기 '요청' (NPC 핸드 포함)
        self.view.update_gui_cards(
            initial_state['player_hand'], 
            initial_state['dealer_hand_hidden'],
            initial_state.get('npc_hands', {}),
            initial_state.get('npc_dialogues', {})
        )

        self.current_npc_visible_hands = copy.deepcopy(initial_state.get('npc_hands', {}))
        self.current_npc_dialogues = copy.deepcopy(initial_state.get('npc_dialogues', {}))
        
        player_score = self.game_model.calculate_score(initial_state['player_hand'])
        self.view.status_label.config(text=f"플레이어 점수: {player_score}. Hit / Stand?")

    def handle_item_use(self, item_type: str):
        """ [컨트롤러] 아이템 구매 및 사용 로직 """
        if self.game_is_over:
            return

        result = self.game_model.purchase_and_use_item(item_type, self.current_bankroll)

        if result['status'] == 'InsufficientFunds':
            messagebox.showerror("구매 실패", f"잔액이 부족합니다. 필요한 칩: {result['cost']}")
            return
        elif result['status'] == 'InvalidItem':
            messagebox.showerror("오류", "잘못된 아이템입니다.")
            return

        self.current_bankroll -= result['cost'] # 비용 차감
        self.view.update_chip_label(self.current_bankroll) 
        self.view.update_gui_cards(
            result['player_hand'],
            self.view.current_dealer_hand_hidden,
            self.current_npc_visible_hands,
            self.current_npc_dialogues
        )
        self._refresh_npc_dialogues()
        
        self.view.status_label.config(text=f"아이템 사용! {result['new_card']} 받음. 현재 점수: {result['score']}")
        self.item_used_this_round = True
        self.view.set_item_button_state("disabled") # 아이템 라운드당 1회 사용

        if self.force_action_pending and not self.game_is_over:
            self._complete_forced_action_requirement("아이템 사용으로 패시브 조건을 충족했습니다. 다시 Stand가 가능합니다.")

        if 'Bust' in result['status']:
            self.finalize_game(result="Lose (Bust)", payout=-self.bet_amount)


    def handle_hit(self):
        """ [컨트롤러] Hit 로직 """
        if self.game_is_over:
            return
            
        hit_result = self.game_model.player_hit()
        
        self.view.update_gui_cards(
            hit_result['player_hand'],
            self.view.current_dealer_hand_hidden,
            self.current_npc_visible_hands,
            self.current_npc_dialogues
        )
        self._refresh_npc_dialogues()
        self.view.status_label.config(text=f"새 카드! 현재 점수: {hit_result['score']}")

        if self.force_action_pending and not self.game_is_over:
            self._complete_forced_action_requirement("Hit을 수행했습니다. 다시 Stand가 가능합니다.")

        if hit_result['status'] == 'Bust':
            self.view.status_label.config(text=f"Bust! (점수: {hit_result['score']}) 😭")
            self.finalize_game(result="Lose (Bust)", payout=-self.bet_amount)

    def handle_stand(self):
        """ [컨트롤러] Stand 로직 (공격형 NPC 패시브 체크 포함) """
        if self.game_is_over or self.player_stood:
            return
        
        self.player_stood = True
        self.view.status_label.config(text="Stand! 결과를 기다리는 중...")
        self.view.hit_button.config(state="disabled")
        self.view.stand_button.config(state="disabled")
        self.view.set_item_button_state("disabled")

        # 🌟 L-22: 공격형 NPC 패시브 체크 (Model 호출)
        is_passive_triggered, msg, aggressive_name = self.game_model.check_aggressive_passive()

        if is_passive_triggered:
            messagebox.showinfo("🚨 패시브 발동", msg)
            self._enter_forced_action_state(aggressive_name)
            return 
        
        # --- 정상적인 라운드 종료 ---
        
        # 🌟 L-23: NPC 턴 실행 (Model 호출)
        npc_turn_summary = self.game_model.npcs_play_turn()
        npc_hands = {name: data["hand"] for name, data in npc_turn_summary.items()}
        npc_dialogues = {name: data.get("dialogues", []) for name, data in npc_turn_summary.items()}

        # NPC의 최종 패/대사 업데이트
        self.view.update_gui_cards(
            self.game_model.player_hand,
            self.view.current_dealer_hand_hidden,
            npc_hands,
            npc_dialogues
        )
        self.current_npc_visible_hands = copy.deepcopy(npc_hands)
        self.current_npc_dialogues = copy.deepcopy(npc_dialogues)

        # 딜러 턴
        dealer_final_hand = self.game_model.dealer_turn()
        hidden_back_list = ['BACK'] * len(dealer_final_hand)
        self.view.update_gui_cards(
            self.game_model.player_hand,
            hidden_back_list,
            self.current_npc_visible_hands,
            self.current_npc_dialogues
        )
        self.view.reveal_dealer_hand(dealer_final_hand)
        
        # 최종 정산
        final_result = self.game_model.check_result()
        
        self.npc_final_settlement = final_result['npc_results'] # NPC 정산 결과 저장
        
        result_msg = final_result['result_msg']
        p_score = final_result['player_score']
        d_score = final_result['dealer_score']
        
        npc_res_msg = ", ".join([f"{name}: {details['result']}" for name, details in self.npc_final_settlement.items()])
        self.view.status_label.config(text=f"결과: {result_msg}! (P:{p_score} vs D:{d_score}) / NPC: {npc_res_msg}")
        passive_dialogues = final_result.get('passive_dialogues', {})
        if passive_dialogues:
            for name, lines in passive_dialogues.items():
                if lines:
                    self.current_npc_dialogues[name] = lines
            self.view.update_npc_dialogues_only(passive_dialogues)

        # 정산 로직으로 이동
        self.finalize_game(result=final_result['result_msg'], payout=final_result['payout'])

    def finalize_game(self, result: str, payout: int):
        """ [컨트롤러] 게임 종료 및 DB 저장 로직 (NPC 결과 반영) """
        if self.game_is_over: 
            return
        self.game_is_over = True 

        self.view.hit_button.config(state="disabled")
        self.view.stand_button.config(state="disabled")
        self.view.reset_button.config(state="normal") 
        self.view.set_item_button_state("disabled")

        self.current_bankroll += payout
        
        emoji = "🎉" if payout > 0 else "💸" if payout < 0 else "🤝"
        self.view.chip_label.config(text=f"남은 돈: ${self.current_bankroll} (결과: {payout:+} {emoji})")
        
        # '컨트롤러'가 DB('모델')에 저장
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
            db.save_game(conn, self.user_data['id'], self.bet_amount, result, payout)
            
            # TODO: NPC의 정산 결과(self.npc_final_settlement)를 DB에 저장하는 로직이 있다면 여기에 추가
            
            conn.close()
        except Exception as e:
            messagebox.showerror("DB 오류", f"게임 결과 저장 실패: {e}")
    
    def reset_game(self):
        self.back_to_main() 

    def back_to_main(self):
        """ [컨트롤러] 메인 메뉴 복귀 로직 """
        # 게임이 끝나지 않았다면 현재 잔액을 DB에 저장합니다.
        if not self.game_is_over:
            try:
                conn = sqlite3.connect(DB_NAME)
                db.update_bankroll(conn, self.user_data['id'], self.current_bankroll)
                conn.close()
            except Exception as e:
                messagebox.showerror("DB 오류", f"칩 저장 실패: {e}")
        
        self.view.root.destroy()
        # 부모 View('메인메뉴')의 칩 상태 업데이트 '요청' 후 복원
        self.main_window_view.chips = self.current_bankroll
        self.main_window_view.update_chip_label(self.current_bankroll) 
        self.main_window_view.deiconify()

    def _enter_forced_action_state(self, aggressive_name: str):
        self.force_action_pending = True
        self.player_stood = False
        warning_text = "패시브 발동! Hit 또는 아이템을 사용해야 다시 Stand할 수 있습니다."
        self.view.status_label.config(text=warning_text)
        self.view.hit_button.config(state="normal")
        if self.item_used_this_round:
            self.view.set_item_button_state("disabled")
        else:
            self.view.set_item_button_state("normal")
        self.view.stand_button.config(state="disabled")

        if aggressive_name:
            self.current_npc_dialogues[aggressive_name] = ["[행동교란] 지금 멈추겠다고? 그럴 순 없다!"]
            self.view.update_npc_dialogues_only({aggressive_name: self.current_npc_dialogues[aggressive_name]})

    def _complete_forced_action_requirement(self, message: str):
        if not self.force_action_pending:
            return
        self.force_action_pending = False
        if not self.game_is_over:
            self.view.stand_button.config(state="normal")
            current = self.view.status_label.cget("text")
            combined = f"{current}\n{message}" if current else message
            self.view.status_label.config(text=combined)
        if self.item_used_this_round:
            self.view.set_item_button_state("disabled")
        else:
            self.view.set_item_button_state("normal")

    def _refresh_npc_dialogues(self):
        snapshot = self.game_model.get_current_npc_dialogues()
        if not snapshot:
            return
        self.current_npc_dialogues = copy.deepcopy(snapshot)
        self.view.update_npc_dialogues_only(snapshot)