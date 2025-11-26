import tkinter as tk
from tkinter import messagebox
import os
import glob
from PIL import Image, ImageTk
# import json, hashlib, re (DB/인증 관련 라이브러리 제거)

# --- 상수 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 🚨 이미지 경로 원본 유지 (Controller에서 이 경로가 맞도록 설정해야 함)
IMAGE_DIR = os.path.join(BASE_DIR, "img")
SUIT_SYMBOL_TO_LETTER = {
    "♠": "S",
    "♣": "C",
    "♥": "H",
    "♦": "D",
}
# USERS_FILE = os.path.join(BASE_DIR, "users.json") (제거)
# 랭킹창 (View)
# =========================
def open_ranking_window():
    ranking_win = tk.Toplevel()
    ranking_win.title("🏆 게임 랭킹")
    ranking_win.geometry("300x400")
    ranking_win.resizable(False, False)
    tk.Label(ranking_win, text="랭킹 순위", font=("Dotum",16,"bold"), pady=15).pack()
    tk.Button(ranking_win, text="닫기", command=ranking_win.destroy).pack(pady=15)
    
    # 랭킹 데이터를 채울 공간을 반환 (Controller용)
    data_frame = tk.Frame(ranking_win)
    data_frame.pack(fill="x", padx=10)
    return ranking_win, data_frame # 튜플로 반환하도록 수정

def populate_ranking_data(data_frame, rank_data):
    """ Controller에서 받은 데이터를 UI에 채웁니다. (data_frame을 인수로 받도록 수정)"""
    if not rank_data:
        tk.Label(data_frame, text="아직 랭킹이 없습니다.", font=("Dotum",12)).pack(pady=5)
        return
    
    # data_frame의 기존 위젯을 지우는 로직이 Controller에서 필요하지 않다면 생략
    for rank, data in enumerate(rank_data, 1):
        # 데이터 형식: (name, bankroll, type) 또는 (name, bankroll) (하위 호환성)
        if len(data) == 3:
            name, score, rank_type = data
        else:
            name, score = data
            rank_type = 'player'  # 기본값
        
        medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"{rank}."
        
        # NPC인 경우 아이콘 추가
        if rank_type == 'npc':
            icon = "🤖"
            text = f"{medal} {icon} {name}: ${score}"
        else:
            text = f"{medal} {name}: ${score}"
        
        tk.Label(data_frame, text=text, font=("Dotum",12), anchor="w").pack(fill="x", pady=2, padx=20)


# =========================
# 메인 메뉴 (View)
# =========================
# 🚨 수정: tk.Tk를 tk.Toplevel로 변경하고 master 인수를 추가합니다.
class MainMenu(tk.Toplevel):
    def __init__(self, master, user_data: dict):
        super().__init__(master) # master를 Toplevel 생성자에 전달
        self.title("BLACK JACK 메인 화면")
        self.geometry("800x500")
        self.resizable(False, False)
        self.user_data = user_data
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

        # 🚨 수정: 모든 내부 로직 호출 제거 (Controller에 위임)
        self.charge_button.config(command=lambda: print("Controller 연결 예정"))
        self.start_game_button.config(command=lambda: print("Controller 연결 예정"))
        self.ranking_button.config(command=lambda: print("Controller 연결 예정"))
        self.logout_button.config(command=lambda: print("Controller 연결 예정"))
        # 원본의 _charge_money, _on_start_game, _on_ranking, _on_logout 함수는 Controller에서 구현되므로 제거됨

    def update_chip_label(self, new_chips):
        self.chips = new_chips
        self.chip_label.config(text=f"보유 돈: ${self.chips}")

# =========================
# 블랙잭 GUI (View) - NPC 및 아이템 지원 추가
# =========================
class BlackjackGUI:
    def __init__(self, main_menu_root, user_data: dict, bet_amount: int, current_bankroll: int):
        self.main_window = main_menu_root
        self.root = tk.Toplevel(main_menu_root)
        self.root.title("♠️ Blackjack Game")
        self.root.geometry("1200x800") # 창 크기 확장
        self.root.configure(bg="green")

        self.card_images_pil = {}
        self.card_images_tk_cached = {}
        self.card_size = (80, 120) # 카드 크기 축소 (공간 확보)
        self.load_card_images()
        self.current_dealer_hand_hidden = []


        # --- 상단 버튼 및 상태 ---
        top_frame = tk.Frame(self.root, bg="green")
        top_frame.pack(fill="x", pady=5)
        
        self.main_menu_button = tk.Button(top_frame, text="메인 화면으로", width=11, height=2, font=("Arial",9,"bold"), command=self.root.destroy)
        self.main_menu_button.pack(side="left", padx=5)

        self.chip_label = tk.Label(top_frame, text=f"남은 돈: ${current_bankroll - bet_amount}", bg="green", fg="white", font=("Arial",12,"bold"))
        self.chip_label.pack(side="right", padx=10)
        
        self.status_label = tk.Label(self.root, text=f"베팅: ${bet_amount} / 새 게임 시작", bg="green", fg="yellow", font=("Arial",16,"bold"))
        self.status_label.pack(pady=10)

        # 🌟 1. NPC 구역 추가
        tk.Label(self.root, text="NPC 플레이어들", bg="green", fg="yellow", font=("Arial", 14, "bold")).pack(pady=(10,0))
        self.npc_frame = tk.Frame(self.root, bg="green", width=1000)
        self.npc_frame.pack(pady=5, fill="x")
        self.npc_inner_frame = tk.Frame(self.npc_frame, bg="green")
        self.npc_inner_frame.pack(anchor="center")

        self.npc_card_frames = {} # NPC 카드 라벨 저장소
        self.npc_dialogue_labels = {}
        self.npc_balance_labels = {}  # NPC 잔액 라벨 저장소
        self.npc_bet_labels = {}  # NPC 배팅 금액 라벨 저장소
        self.npc_sections = {}

        # --- 2. 딜러 구역 (원본 유지) ---
        tk.Label(self.root, text="딜러", bg="green", fg="white", font=("Arial", 14, "bold")).pack(pady=(10,0))
        self.dealer_frame = tk.Frame(self.root, bg="green", width=800)
        self.dealer_frame.pack(pady=5, fill="x")
        self.dealer_card_area = tk.Frame(self.dealer_frame, bg="green")
        self.dealer_card_area.pack(expand=True)

        # --- 3. 플레이어 구역 (원본 유지) ---
        tk.Label(self.root, text=f"{user_data['username']}", bg="green", fg="white", font=("Arial", 14, "bold")).pack(pady=(10,0))
        self.player_frame = tk.Frame(self.root, bg="green", width=800)
        self.player_frame.pack(pady=5, fill="x")
        self.player_card_area = tk.Frame(self.player_frame, bg="green")
        self.player_card_area.pack(expand=True)

        # --- 4. 버튼 및 아이템 구역 ---
        self.button_frame = tk.Frame(self.root, bg="green")
        self.button_frame.pack(pady=20, side="bottom")

        # 🌟 아이템 버튼 추가
        item_frame = tk.Frame(self.button_frame, bg="green")
        item_frame.pack(side="left", padx=20)
        self.item_low_button = tk.Button(item_frame, text="🛒 Item 1 (1~5)", font=("Arial", 17), width=12)
        self.item_low_button.pack(side="left", padx=5)
        self.item_high_button = tk.Button(item_frame, text="🛒 Item 2 (6~10)", font=("Arial", 17), width=12)
        self.item_high_button.pack(side="left", padx=5)

        # 게임 액션 버튼 (원본 유지)
        action_frame = tk.Frame(self.button_frame, bg="green")
        action_frame.pack(side="left", padx=20)
        self.hit_button = tk.Button(action_frame, text="Hit", font=("Arial", 18), width=10)
        self.hit_button.pack(side="left", padx=5)
        self.stand_button = tk.Button(action_frame, text="Stand", font=("Arial", 18), width=10)
        self.stand_button.pack(side="left", padx=5)
        
        # 🚨 수정: Double/Split/Surrender 버튼 제거 (기획에서 제외)
        self.reset_button = tk.Button(action_frame, text="New Round", font=("Arial", 18), width=10, state="disabled")
        self.reset_button.pack(side="left", padx=5)
        dummy_player_hand = ['C_2', 'C_3']
        dummy_dealer_hand = ['BACK', 'BACK']
        self.update_gui_cards(dummy_player_hand, dummy_dealer_hand)
        self._center_window(self.root)

    def update_chip_label(self, amount: int):
        """게임 상단 칩 표시를 갱신합니다."""
        self.chip_label.config(text=f"남은 돈: ${amount}")

    def _center_window(self, win):
        """ 창을 화면의 중앙에 배치합니다. """
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

    # --- 기존 메서드 (원본 유지) ---
    def load_card_images(self):
        """이미지 폴더에서 모든 카드 PNG를 불러온다."""
        card_size = self.card_size
        image_paths = glob.glob(os.path.join(IMAGE_DIR, "*.[pP][nN][gG]"))
        if not image_paths:
            print(f"경고: '{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
            messagebox.showwarning("이미지 오류", f"'{IMAGE_DIR}/' 폴더에서 카드 이미지를 찾을 수 없습니다.")
            return

        for path in image_paths:
            filename = os.path.basename(path)
            card_name = os.path.splitext(filename)[0]
            try:
                img = Image.open(path).convert("RGBA")
                img_resized = img.resize(card_size, Image.LANCZOS)
                self.card_images_pil[card_name] = img_resized
            except Exception as e:
                print(f"이미지 로드 실패: {path} / {e}")

        if "BACK" not in self.card_images_pil:
            print(f"경고: '{IMAGE_DIR}/BACK.png' (뒷면) 이미지를 찾을 수 없습니다.")

    def _normalize_card_id(self, card):
        """Card 객체나 문자열을 이미지 키 문자열로 변환한다."""
        if isinstance(card, str):
            return card
        if hasattr(card, "suit") and hasattr(card, "rank"):
            suit_symbol = card.suit
            suit_letter = SUIT_SYMBOL_TO_LETTER.get(suit_symbol, suit_symbol[:1].upper())
            return f"{suit_letter}_{card.rank}"
        return str(card)

    def _get_tk_image(self, card_name, width=None):
        """PIL 이미지를 PhotoImage로 변환하며 크기별 캐시 생성."""
        card_key = self._normalize_card_id(card_name)
        if card_key not in self.card_images_pil:
            return None

        full_w, full_h = self.card_size
        target_w = width if width is not None else full_w
        target_h = full_h
        key = (card_key, target_w)

        cached = self.card_images_tk_cached.get(key)
        if cached:
            return cached

        if target_w <= 0:
            target_w = 1

        pil_img = self.card_images_pil[card_key].resize((int(target_w), int(target_h)), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        self.card_images_tk_cached[key] = tk_img
        return tk_img
        
    # 🌟 수정: NPC 인수를 받도록 시그니처 확장 및 NPC 업데이트 위임
    def update_gui_cards(
        self,
        player_hand: list,
        dealer_hand: list,
        npc_hands: dict = None,
        npc_dialogues: dict = None,
        highlight_player_card=None,
    ):
        """ 플레이어, 딜러, NPC 패를 업데이트합니다. highlight_player_card는 화면에서 강조할 카드입니다. """
        highlight_key = None
        if highlight_player_card is not None:
            highlight_key = self._normalize_card_id(highlight_player_card)
        
        # (딜러 패 업데이트 로직 유지)
        for widget in self.dealer_card_area.winfo_children():
            widget.destroy()
        for card_name in dealer_hand:
            tkimg = self._get_tk_image(card_name)
            lbl = tk.Label(self.dealer_card_area, image=tkimg, bg="green")
            if tkimg: lbl.image = tkimg
            lbl.pack(side="left", padx=5)
        self.current_dealer_hand_hidden = dealer_hand 

        # (플레이어 패 업데이트 로직 유지)
        for widget in self.player_card_area.winfo_children():
            widget.destroy()
        for card_name in player_hand:
            card_key = self._normalize_card_id(card_name)
            tkimg = self._get_tk_image(card_name)
            lbl = tk.Label(self.player_card_area, image=tkimg, bg="green")
            if highlight_key and card_key == highlight_key:
                lbl.config(highlightbackground="#ffd700", highlightthickness=3, bd=2)
            if tkimg: lbl.image = tkimg
            lbl.pack(side="left", padx=5)
            
        # 🌟 NPC 패 업데이트 위임
        if npc_hands is not None:
            self.update_npc_hands(npc_hands, npc_dialogues)

    def reveal_dealer_hand(self, dealer_final_hand: list):
        """딜러 패를 순차적으로 뒤집으며 최종 카드 이미지를 보여준다."""
        normalized = [self._normalize_card_id(card) for card in dealer_final_hand]
        self.current_dealer_hand_hidden = normalized

        for idx, card_name in enumerate(normalized):
            delay = idx * 350
            self.root.after(delay, lambda i=idx, c=card_name: self.flip_dealer_card(i, c))

    def flip_dealer_card(self, index, final_card_name):
        """카드 뒷면 이미지를 점진적으로 앞면으로 전환한다."""
        widgets = self.dealer_card_area.winfo_children()
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

        widths_shrink = [int(full_w * (1 - i / steps)) for i in range(steps)]
        if widths_shrink[-1] <= 0:
            widths_shrink[-1] = 1
        widths_expand = [int(full_w * (i / steps)) for i in range(1, steps + 1)]

        def do_shrink(i=0):
            if i >= len(widths_shrink):
                if front_exists:
                    tkimg_inner = self._get_tk_image(final_card_name, width=1)
                    if tkimg_inner:
                        label.config(image=tkimg_inner)
                        label.image = tkimg_inner
                do_expand(0)
                return

            w = widths_shrink[i]
            src = "BACK" if back_exists else final_card_name
            tkimg_inner = self._get_tk_image(src, width=w)
            if tkimg_inner:
                label.config(image=tkimg_inner)
                label.image = tkimg_inner
            self.root.after(interval, lambda: do_shrink(i + 1))

        def do_expand(i=0):
            if i >= len(widths_expand):
                final_img = self._get_tk_image(final_card_name)
                if final_img:
                    label.config(image=final_img)
                    label.image = final_img
                return

            w = widths_expand[i]
            tkimg_inner = self._get_tk_image(final_card_name, width=w)
            if tkimg_inner:
                label.config(image=tkimg_inner)
                label.image = tkimg_inner
            self.root.after(interval, lambda: do_expand(i + 1))

        do_shrink(0)

    # 🌟 신규 메서드: NPC 핸드 업데이트 추가
    def update_npc_hands(self, npc_hands: dict, npc_dialogues: dict = None, npc_balances: dict = None, npc_bets: dict = None):
        """ NPC 플레이어들의 패와 대사를 업데이트합니다. """
        for name, hand in npc_hands.items():
            section = self.npc_sections.get(name)
            if section is None:
                npc_sub_frame = tk.Frame(self.npc_inner_frame, bg="green", padx=10, pady=5)
                npc_sub_frame.pack(side="left", padx=15, fill="y")

                # NPC 이름 라벨
                name_label = tk.Label(npc_sub_frame, text=name, bg="green", fg="white", font=("Arial", 12, "bold"))
                name_label.pack()
                
                # NPC 잔액 라벨
                balance_label = tk.Label(
                    npc_sub_frame, 
                    text="잔액: $0", 
                    bg="green", 
                    fg="yellow", 
                    font=("Arial", 10, "bold")
                )
                balance_label.pack()
                self.npc_balance_labels[name] = balance_label
                
                # NPC 배팅 금액 라벨
                bet_label = tk.Label(
                    npc_sub_frame, 
                    text="배팅: $0", 
                    bg="green", 
                    fg="cyan", 
                    font=("Arial", 10)
                )
                bet_label.pack()
                self.npc_bet_labels[name] = bet_label
                
                card_frame = tk.Frame(npc_sub_frame, bg="green")
                card_frame.pack(pady=(4, 2))

                dialogue_label = tk.Label(
                    npc_sub_frame,
                    text=" ",
                    bg="#0b4510",
                    fg="#f8f5d7",
                    font=("Helvetica", 12, "italic"),
                    justify="left",
                    anchor="nw",
                    wraplength=220,
                    width=28,
                    height=4,
                    padx=8,
                    pady=6,
                    relief="ridge",
                    bd=2
                )
                dialogue_label.pack(fill="x", pady=(8, 0))

                self.npc_sections[name] = {
                    "frame": npc_sub_frame,
                    "cards": card_frame,
                    "dialogue": dialogue_label,
                }
                self.npc_card_frames[name] = card_frame
                self.npc_dialogue_labels[name] = dialogue_label

            card_frame = self.npc_card_frames[name]
            for widget in card_frame.winfo_children():
                widget.destroy()

            for card_name in hand:
                tkimg = self._get_tk_image(card_name)
                lbl = tk.Label(card_frame, image=tkimg, bg="green")
                if tkimg:
                    lbl.image = tkimg
                lbl.pack(side="left", padx=2)

            dialogue_lines = []
            if npc_dialogues and name in npc_dialogues:
                dialogue_lines = npc_dialogues[name]
            dialogue_text = "\n".join(dialogue_lines) if dialogue_lines else " "
            self.npc_dialogue_labels[name].config(text=dialogue_text)
            
            # NPC 잔액 및 배팅 금액 업데이트
            if npc_balances and name in npc_balances:
                if name in self.npc_balance_labels:
                    self.npc_balance_labels[name].config(text=f"잔액: ${npc_balances[name]}")
            if npc_bets and name in npc_bets:
                if name in self.npc_bet_labels:
                    self.npc_bet_labels[name].config(text=f"배팅: ${npc_bets[name]}")

    def update_npc_dialogues_only(self, npc_dialogues: dict):
        if not npc_dialogues:
            return
        for name, lines in npc_dialogues.items():
            if name not in self.npc_dialogue_labels:
                continue
            text = "\n".join(lines) if lines else " "
            self.npc_dialogue_labels[name].config(text=text)
    
    def update_npc_balances_and_bets(self, npc_balances: dict, npc_bets: dict):
        """NPC 잔액과 배팅 금액만 업데이트합니다."""
        for name, balance in npc_balances.items():
            if name in self.npc_balance_labels:
                self.npc_balance_labels[name].config(text=f"잔액: ${balance}")
        for name, bet in npc_bets.items():
            if name in self.npc_bet_labels:
                self.npc_bet_labels[name].config(text=f"배팅: ${bet}")

    # 🌟 신규 메서드: 아이템 버튼 상태 제어 추가
    def set_item_button_state(self, state: str):
        """ 아이템 버튼의 상태를 변경합니다 ('normal' 또는 'disabled'). """
        self.item_low_button.config(state=state)
        self.item_high_button.config(state=state)
        
# =========================
# 로그인 창 (View)
# =========================
def main_login_window():
    global login_win, username_entry, password_entry
    
    # 🚨 수정: DB/인증 로직 제거
    # users_store = load_users() (제거)
    
    login_win = tk.Tk()
    login_win.title("BLACK JACK 로그인")
    login_win.geometry("600x600")
    login_win.resizable(False, False)

    logo_path = os.path.join(IMAGE_DIR, "blackjack_logo.png")
    if not os.path.exists(logo_path):
        logo_label = tk.Label(
            login_win,
            text="BLACKJACK",
            font=("Dotum", 30, "bold"),
            fg="gold",
            bg="darkblue",
            width=25,
            height=4,
        )
    else:
        try:
            original_image = Image.open(logo_path)
            resized_image = original_image.resize((400, 200), Image.LANCZOS)
            logo_image = ImageTk.PhotoImage(resized_image)
            logo_label = tk.Label(login_win, image=logo_image)
            logo_label.image = logo_image
        except Exception as e:
            messagebox.showerror("이미지 로드 실패", f"로그인 로고 이미지 로드 중 오류 발생: {e}")
            logo_label = tk.Label(
                login_win,
                text="BLACKJACK",
                font=("Dotum", 30, "bold"),
                fg="gold",
                bg="darkblue",
            )

    logo_label.pack(pady=20)
    main_frame = tk.Frame(login_win, padx=30, pady=30)
    main_frame.pack(expand=True)

    tk.Label(main_frame, text="사용자 이름:", font=("Dotum", 12, "bold")).grid(row=0, column=0, sticky="w", pady=10)
    username_entry = tk.Entry(main_frame, font=("Dotum", 12))
    username_entry.grid(row=0, column=1, padx=5, pady=10)

    tk.Label(main_frame, text="비밀번호:", font=("Dotum", 12, "bold")).grid(row=1, column=0, sticky="w", pady=10)
    password_entry = tk.Entry(main_frame, font=("Dotum", 12), show="*")
    password_entry.grid(row=1, column=1, padx=5, pady=10)

    signup_btn = tk.Button(main_frame, text="회원가입", width=12, font=("Dotum", 11, "bold"))
    signup_btn.grid(row=2, column=1, pady=20, padx=5, sticky="w")
    login_btn = tk.Button(main_frame, text="로그인", width=12, font=("Dotum", 11, "bold"))
    login_btn.grid(row=2, column=0, pady=20, sticky="e")
    tk.Button(main_frame, text="닫기", width=12, font=("Dotum", 11, "bold"), command=login_win.destroy).grid(
        row=2, column=2, pady=20, padx=5, sticky="w"
    )

    # 🚨 내부 command 연결은 Controller가 담당하므로 설정하지 않음
    return login_win, username_entry, password_entry