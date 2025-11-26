import tkinter as tk
from tkinter import messagebox, simpledialog
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
        result = view.main_login_window()
        self.login_win = result[0]
        self.username_entry = result[1]
        self.password_entry = result[2]
        
        # 버튼 객체가 반환되는 경우 직접 연결
        if len(result) >= 5:
            login_btn = result[3]
            signup_btn = result[4]
            login_btn.config(command=self.handle_login_click)
            signup_btn.config(command=self.handle_signup_click)
        else:
            # 하위 호환성: 기존 방식으로 버튼 찾기
            for widget in self.login_win.winfo_children()[0].winfo_children():
                if widget.cget("text") == "회원가입":
                    widget.config(command=self.handle_signup_click)
                elif widget.cget("text") == "로그인":
                    widget.config(command=self.handle_login_click)
        
        self.login_win.bind('<Return>', self.handle_login_click)
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
        self.view.controller = self  # GameController가 메인 컨트롤러에 접근할 수 있도록 참조 저장
        
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
        self.user_data["bankroll"] = self.chips
        
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
            self.user_data["bankroll"] = self.chips
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
        self.pending_npc_turn_summary = None
        self.npc_step_delay_ms = 2000
        self._resolving_round = False
        self.npc_balances = {}  # NPC 잔액 저장
        self._npc_turn_in_progress = False  # NPC 턴 진행 중 플래그

        # NPC 잔액 로드
        self._load_npc_balances()
        
        # '모델'('룰') 객체 생성 (NPC 잔액 정보 전달)
        self.game_model = gc.BlackjackGame(npc_balances=self.npc_balances)
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
    
    def _load_npc_balances(self):
        """DB에서 NPC 잔액을 로드합니다."""
        try:
            conn = sqlite3.connect(DB_NAME)
            npc_data = db.get_all_npcs(conn)
            conn.close()
            
            self.npc_balances = {}
            for name, npc_type, balance in npc_data:
                # NPC 잔액이 100 이하이면 자동으로 100 충전
                if balance <= 100:
                    balance = 100
                    self._update_npc_balance_in_db(name, balance)
                self.npc_balances[name] = balance
        except Exception as e:
            print(f"NPC 잔액 로드 실패: {e}")
            # 기본값 설정
            self.npc_balances = {
                "NPC-1 (안정형)": 1000,
                "NPC-2 (공격형)": 1000,
                "NPC-3 (특이형)": 1000
            }
    
    def _update_npc_balance_in_db(self, npc_name: str, new_balance: int):
        """DB에 NPC 잔액을 업데이트합니다."""
        try:
            conn = sqlite3.connect(DB_NAME)
            db.update_npc_bankroll(conn, npc_name, new_balance)
            conn.close()
        except Exception as e:
            print(f"NPC 잔액 업데이트 실패: {e}")

    def start_new_game(self):
        """ [컨트롤러] 새 게임 시작 로직 """
        self.game_is_over = False
        self.player_stood = False
        self.force_action_pending = False
        self.item_used_this_round = False
        self.pending_npc_turn_summary = None
        self._resolving_round = False
        self.view.set_item_button_state("normal") # 아이템 버튼 활성화

        # NPC 잔액 다시 로드 (자동 충전 확인)
        self._load_npc_balances()
        
        # 게임 모델에 NPC 잔액 전달
        self.game_model = gc.BlackjackGame(npc_balances=self.npc_balances)
        
        # '모델'('룰') 호출
        initial_state = self.game_model.start_game(bet=self.bet_amount)
        
        # NPC 배팅 금액 정보 생성
        npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
        
        # 🌟 View에 카드 그리기 '요청' (NPC 핸드, 잔액, 배팅 포함)
        self.view.update_gui_cards(
            initial_state['player_hand'], 
            initial_state['dealer_hand_hidden'],
            initial_state.get('npc_hands', {}),
            initial_state.get('npc_dialogues', {})
        )
        
        # NPC 잔액 및 배팅 금액 업데이트
        npc_balances_dict = self.game_model.get_npc_balances()
        self.view.update_npc_balances_and_bets(npc_balances_dict, npc_bets)

        self.current_npc_visible_hands = copy.deepcopy(initial_state.get('npc_hands', {}))
        self.current_npc_dialogues = copy.deepcopy(initial_state.get('npc_dialogues', {}))
        
        player_score = self.game_model.calculate_score(initial_state['player_hand'])
        self.view.status_label.config(text=f"베팅: ${self.bet_amount} / 플레이어 점수: {player_score}. Hit / Stand?")
        self.view.update_chip_label(self.current_bankroll - self.bet_amount)
        self.view.hit_button.config(state="normal")
        self.view.stand_button.config(state="normal")
        self.view.reset_button.config(state="disabled")

    def handle_item_use(self, item_type: str):
        """ [컨트롤러] 아이템 구매 및 사용 로직 (카드 표시 + 상태 갱신) """
        if self.game_is_over:
            return

        result = self.game_model.purchase_and_use_item(item_type, self.current_bankroll)

        if result['status'] == 'InsufficientFunds':
            messagebox.showerror("구매 실패", f"잔액이 부족합니다. 필요한 칩: {result['cost']}")
            return
        if result['status'] == 'InvalidItem':
            messagebox.showerror("오류", "잘못된 아이템입니다.")
            return

        self.current_bankroll -= result['cost']
        self.view.update_chip_label(self.current_bankroll)

        self.view.update_gui_cards(
            result['player_hand'],
            self.view.current_dealer_hand_hidden,
            self.current_npc_visible_hands,
            self.current_npc_dialogues,
            highlight_player_card=result['new_card']
        )
        self.view.root.update_idletasks()

        self._refresh_npc_dialogues()

        self.view.status_label.config(text=f"아이템 사용! {result['new_card']} 받음. 현재 점수: {result['score']}")

        self.item_used_this_round = True
        self.view.set_item_button_state("disabled")

        if self.force_action_pending and not self.game_is_over:
            self._complete_forced_action_requirement("아이템 사용으로 패시브 조건을 충족했습니다. 다시 Stand가 가능합니다.")

        if 'Bust' in result['status']:
            self.view.status_label.config(text=f"Bust! (점수: {result['score']}) 😭")
            self.player_stood = True
            self._disable_player_controls()
            self._start_resolution_pipeline()


    def handle_hit(self):
        """ [컨트롤러] Hit 로직 """
        if self.game_is_over or self._npc_turn_in_progress:
            return
            
        hit_result = self.game_model.player_hit()
        
        self.view.update_gui_cards(
            hit_result['player_hand'],
            self.view.current_dealer_hand_hidden,
            self.current_npc_visible_hands,
            self.current_npc_dialogues,
            highlight_player_card=hit_result['new_card']
        )
        self._refresh_npc_dialogues()
        self.view.status_label.config(text=f"새 카드! 현재 점수: {hit_result['score']}")

        if hit_result['status'] == 'Bust':
            self.view.status_label.config(text=f"Bust! (점수: {hit_result['score']}) 😭")
            self.player_stood = True
            self._disable_player_controls()
            self._start_resolution_pipeline()
        else:
            # 플레이어가 Hit한 후 NPC들이 한 번씩 행동
            self._disable_player_controls()
            self._play_npc_single_round()

    def handle_stand(self):
        """ [컨트롤러] Stand 로직 (공격형 NPC 패시브 체크 포함) """
        if self.game_is_over or self.player_stood or self._npc_turn_in_progress:
            return
        
        self.player_stood = True
        self.view.status_label.config(text="Stand! 결과를 기다리는 중...")
        self._disable_player_controls()

        # 🌟 L-22: 공격형 NPC 패시브 체크 (Model 호출)
        is_passive_triggered, msg, aggressive_name = self.game_model.check_aggressive_passive()

        if is_passive_triggered:
            messagebox.showinfo("🚨 패시브 발동", msg)
            self._enter_forced_action_state(aggressive_name)
            return 
        
        # Stand 시 남은 NPC들만 처리
        self._start_resolution_pipeline()

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
        """새 라운드를 같은 창에서 바로 시작한다."""
        if self.view is None:
            return
        if not self.game_is_over:
            messagebox.showinfo("알림", "게임이 끝난 후에만 새 라운드를 시작할 수 있습니다.")
            return

        new_bet = simpledialog.askinteger(
            "새 라운드",
            "베팅 금액을 입력하세요:",
            initialvalue=self.bet_amount,
            minvalue=1,
            parent=self.view.root,
        )
        if new_bet is None:
            return
        if new_bet > self.current_bankroll:
            messagebox.showwarning("베팅 오류", "보유 칩보다 많은 금액을 베팅할 수 없습니다.")
            return

        self.bet_amount = new_bet
        # NPC 잔액 다시 로드 (자동 충전 확인)
        self._load_npc_balances()
        self.game_model = gc.BlackjackGame(npc_balances=self.npc_balances)
        self.start_new_game()

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
        controller_ref = getattr(self.main_window_view, "controller", None)
        if controller_ref is not None:
            controller_ref.chips = self.current_bankroll
            controller_ref.user_data["bankroll"] = self.current_bankroll

    def _disable_player_controls(self):
        self.view.hit_button.config(state="disabled")
        self.view.stand_button.config(state="disabled")
        self.view.set_item_button_state("disabled")
    
    def _enable_player_controls(self):
        """플레이어 컨트롤 활성화 (게임이 끝나지 않았고, NPC 턴이 아닐 때만)"""
        if self.game_is_over or self.player_stood or self._npc_turn_in_progress:
            return
        self.view.hit_button.config(state="normal")
        self.view.stand_button.config(state="normal")
        if not self.item_used_this_round:
            self.view.set_item_button_state("normal")

    def _start_resolution_pipeline(self):
        """플레이어 Stand 후 남은 NPC들 처리"""
        if self._resolving_round:
            return
        self._resolving_round = True
        
        # 남은 NPC들만 처리 (이미 Stand한 NPC는 round_completed=True이므로 건너뜀)
        # npcs_play_turn은 모든 NPC를 처리하지만, round_completed가 True인 NPC는 
        # 내부적으로 처리하지 않거나 이미 완료된 상태로 처리됨
        npc_turn_summary, npc_steps = self.game_model.npcs_play_turn(capture_steps=True)
        self.pending_npc_turn_summary = npc_turn_summary
        steps_queue = list(npc_steps or [])
        self._play_npc_steps(steps_queue, self._after_npc_phase)

    def _play_npc_single_round(self):
        """플레이어 Hit 후 NPC들이 한 번씩 행동하는 턴"""
        if self._npc_turn_in_progress:
            return
        
        self._npc_turn_in_progress = True
        self.view.status_label.config(text="NPC 턴 진행 중...")
        
        # 각 NPC가 한 번씩 행동
        npc_steps = self.game_model.npc_single_round_step()
        
        if not npc_steps:
            # 모든 NPC가 이미 Stand했거나 Bust한 경우
            self._npc_turn_in_progress = False
            self._enable_player_controls()
            self.view.status_label.config(text="NPC 턴 종료. 플레이어 턴입니다.")
            return
        
        # NPC 행동을 순차적으로 표시
        steps_queue = list(npc_steps)
        self._play_npc_single_steps(steps_queue, self._after_npc_single_round)
    
    def _play_npc_single_steps(self, steps_queue: list, on_complete):
        """NPC들이 한 번씩 행동하는 단계를 순차적으로 표시"""
        if not steps_queue:
            npc_balances = self.game_model.get_npc_balances()
            npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
            self.view.update_npc_hands(self.current_npc_visible_hands, self.current_npc_dialogues, npc_balances, npc_bets)
            on_complete()
            return

        step = steps_queue.pop(0)
        name = step.get("name")
        if name:
            self.current_npc_visible_hands[name] = step.get("hand", [])
            self.current_npc_dialogues[name] = step.get("dialogues", [])
        npc_balances = self.game_model.get_npc_balances()
        npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
        self.view.update_npc_hands(self.current_npc_visible_hands, self.current_npc_dialogues, npc_balances, npc_bets)
        self.view.root.after(self.npc_step_delay_ms, lambda: self._play_npc_single_steps(steps_queue, on_complete))
    
    def _after_npc_single_round(self):
        """NPC 한 턴이 끝난 후 플레이어 턴으로 복귀"""
        self._npc_turn_in_progress = False
        self._enable_player_controls()
        
        # 모든 NPC가 Stand했는지 확인
        all_npcs_stand = all(npc.round_completed for npc in self.game_model.npcs)
        if all_npcs_stand:
            self.view.status_label.config(text="모든 NPC가 Stand했습니다. 플레이어 턴입니다.")
        else:
            self.view.status_label.config(text="NPC 턴 종료. 플레이어 턴입니다.")
    
    def _play_npc_steps(self, steps_queue: list, on_complete):
        """게임 종료 시 모든 NPC 행동을 표시 (기존 로직 유지)"""
        if not steps_queue:
            npc_balances = self.game_model.get_npc_balances()
            npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
            self.view.update_npc_hands(self.current_npc_visible_hands, self.current_npc_dialogues, npc_balances, npc_bets)
            on_complete()
            return

        step = steps_queue.pop(0)
        name = step.get("name")
        if name:
            self.current_npc_visible_hands[name] = step.get("hand", [])
            self.current_npc_dialogues[name] = step.get("dialogues", [])
        npc_balances = self.game_model.get_npc_balances()
        npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
        self.view.update_npc_hands(self.current_npc_visible_hands, self.current_npc_dialogues, npc_balances, npc_bets)
        self.view.root.after(self.npc_step_delay_ms, lambda: self._play_npc_steps(steps_queue, on_complete))

    def _after_npc_phase(self):
        if self.pending_npc_turn_summary:
            for name, data in self.pending_npc_turn_summary.items():
                if "hand" in data:
                    self.current_npc_visible_hands[name] = data["hand"]
                if "dialogues" in data:
                    self.current_npc_dialogues[name] = data["dialogues"]
            npc_balances = self.game_model.get_npc_balances()
            npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
            self.view.update_npc_hands(self.current_npc_visible_hands, self.current_npc_dialogues, npc_balances, npc_bets)
        self.pending_npc_turn_summary = None
        self._run_dealer_phase_and_finalize()

    def _run_dealer_phase_and_finalize(self):
        dealer_final_hand = self.game_model.dealer_turn()
        
        # 딜러 카드를 먼저 BACK으로 표시 (뒤집기 전 상태)
        dealer_back_list = ['BACK'] * len(dealer_final_hand)
        self.view.update_gui_cards(
            self.game_model.player_hand,
            dealer_back_list,
            self.current_npc_visible_hands,
            self.current_npc_dialogues
        )
        
        # 딜러 카드를 순차적으로 뒤집고, 모든 카드가 뒤집힌 후 1초 후에 결과 표시
        self.view.reveal_dealer_hand(dealer_final_hand, on_complete=self._after_dealer_cards_revealed)
    
    def _after_dealer_cards_revealed(self):
        """딜러 카드가 모두 뒤집힌 후 호출되는 콜백"""
        final_result = self.game_model.check_result()
        self.npc_final_settlement = final_result['npc_results']
        
        # NPC 잔액 업데이트 (DB에 저장)
        npc_balances = final_result.get('npc_balances', {})
        for npc_name, new_balance in npc_balances.items():
            # NPC 잔액이 100 이하이면 자동으로 100 충전
            if new_balance <= 100:
                new_balance = 100
            self._update_npc_balance_in_db(npc_name, new_balance)
            self.npc_balances[npc_name] = new_balance
        
        # UI에 NPC 잔액 업데이트
        npc_bets = {npc.name: npc.bet for npc in self.game_model.npcs}
        self.view.update_npc_balances_and_bets(npc_balances, npc_bets)
        
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

        self.finalize_game(result=final_result['result_msg'], payout=final_result['payout'])
        self._resolving_round = False
        self._show_final_summary(final_result)

    def _show_final_summary(self, final_result: dict):
        """라운드 종료 후 결과/패시브/잔액 요약을 메시지 박스로 보여준다."""
        lines = []
        result_msg = final_result.get('result_msg', '결과 미상')
        p_score = final_result.get('player_score', '-')
        d_score = final_result.get('dealer_score', '-')
        payout = final_result.get('payout', 0)

        lines.append(f"플레이어 결과: {result_msg} (P:{p_score} vs D:{d_score})")
        lines.append(f"베팅: ${self.bet_amount} / 정산: {payout:+}")

        npc_lines = []
        for name, details in (self.npc_final_settlement or {}).items():
            npc_lines.append(f"- {name}: {details.get('result', '결과 미상')}")
        if npc_lines:
            lines.append("")
            lines.append("NPC 결과:")
            lines.extend(npc_lines)

        passive_dialogues = final_result.get('passive_dialogues', {})
        passive_lines = []
        for name, texts in passive_dialogues.items():
            if not texts:
                continue
            passive_lines.append(f"- {name}: " + " / ".join(texts))
        lines.append("")
        if passive_lines:
            lines.append("NPC 패시브:")
            lines.extend(passive_lines)
        else:
            lines.append("NPC 패시브: 발동 없음")

        lines.append("")
        lines.append(f"남은 돈: ${self.current_bankroll}")

        messagebox.showinfo("라운드 요약", "\n".join(lines), parent=self.view.root)

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