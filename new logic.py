import random
import sys

# =======================================
# UserDB : 회원가입 / 로그인 + 잔액 관리
# =======================================
class UserDB:
    def __init__(self):
        # users: id -> {pw: str, balance: int}
        self.users = {}

    def register(self, user_id, password):
        if user_id in self.users:
            return False, "이미 존재하는 ID입니다."
        self.users[user_id] = {"pw": password, "balance": 1000}
        return True, "회원가입 성공! 초기 잔액 1000칩 지급."

    def login(self, user_id, password):
        if user_id not in self.users:
            return False, "존재하지 않는 ID입니다."
        if self.users[user_id]["pw"] != password:
            return False, "비밀번호가 올바르지 않습니다."
        return True, "로그인 성공!"

    def get_balance(self, user_id):
        return self.users[user_id]["balance"]

    def set_balance(self, user_id, amount):
        self.users[user_id]["balance"] = amount

# =======================================
# 카드 / 덱
# =======================================
suits = ['♠', '♥', '♦', '♣']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
values = {
    'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10
}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    def __repr__(self):
        return f"{self.suit}{self.rank}"

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in suits for r in ranks]
        random.shuffle(self.cards)
    def deal(self):
        if not self.cards:
            # 재생성 및 셔플 (간단 재초기화)
            self.__init__()
        return self.cards.pop()

# =======================================
# NPC (A: 안정형, B: 공격형, C: 패교체형)
# =======================================
class NPC:
    def __init__(self, npc_type, name, bet):
        self.type = npc_type  # 'A','B','C'
        self.name = name
        self.bet = bet
        self.hand = []
        self.balance = 1000
        self.used_skill = False

    def score(self):
        total = 0
        aces = 0
        for c in self.hand:
            total += values[c.rank]
            if c.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def play_turn(self, deck):
        s = self.score()
        # 안정형 A: <12 Hit, 12~16 hold, 17+ stand. 위기 감지는 간략화해서 이미 적용됨
        if self.type == 'A':
            while s < 12:
                self.hand.append(deck.deal()); s = self.score()
            if 12 <= s <= 16:
                return
            while s < 17:
                self.hand.append(deck.deal()); s = self.score()
            return

        # 공격형 B: first-turn double down if 9~11, else hit <17 (B형 hits on 17 as earlier versions? We'll keep <17)
        if self.type == 'B':
            if not self.used_skill and 9 <= s <= 11:
                self.bet *= 2
                self.hand.append(deck.deal())
                self.used_skill = True
                return
            while s < 17:
                self.hand.append(deck.deal()); s = self.score()
            return

        # 패 교체형 C: first-turn reload if 13~16 then play like others
        if self.type == 'C':
            if not self.used_skill and 13 <= s <= 16:
                self.hand = [deck.deal(), deck.deal()]
                self.used_skill = True
                s = self.score()
            while s < 17:
                self.hand.append(deck.deal()); s = self.score()
            return

# =======================================
# Dealer
# =======================================
class Dealer:
    def __init__(self):
        self.hand = []
    def score(self):
        total = 0
        aces = 0
        for c in self.hand:
            total += values[c.rank]
            if c.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total
    def play_turn(self, deck):
        while self.score() < 17:
            self.hand.append(deck.deal())

# =======================================
# BlackjackGame : 전체 게임 로직 (스킬 사용 조건 포함)
# =======================================
class BlackjackGame:
    def __init__(self, user_db, user_id, bet):
        self.user_db = user_db
        self.user_id = user_id
        self.bet = bet
        self.deck = Deck()

        # 상태
        self.player_hand = []
        self.player_used_skill = False

        # participants
        self.dealer = Dealer()
        self.npcs = [NPC('A','NPC_A',bet), NPC('B','NPC_B',bet), NPC('C','NPC_C',bet)]

        # 초기 지급
        self.start_round()

    def start_round(self):
        self.player_used_skill = False
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.dealer.hand = [self.deck.deal(), self.deck.deal()]
        for npc in self.npcs:
            npc.hand = [self.deck.deal(), self.deck.deal()]

    def calc(self, hand):
        total = 0
        aces = 0
        for c in hand:
            total += values[c.rank]
            if c.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    # ---------------------------
    # 불리한 상황 판단 함수
    # 조건 (하나라도 참이면 '불리'):
    # 1) 플레이어 점수 <= 14
    # 2) 딜러 오픈 카드 값 >= 7
    # 3) NPC 평균 점수 > 플레이어 점수
    # ---------------------------
    def is_bad_situation(self):
        player_score = self.calc(self.player_hand)
        # dealer up card
        dealer_up_val = values[self.dealer.hand[0].rank]
        npc_avg = sum(n.score() for n in self.npcs) / len(self.npcs)
        if player_score <= 14:
            return True
        if dealer_up_val >= 7:
            return True
        if npc_avg > player_score:
            return True
        return False

    # ---------------------------
    # 플레이어 스킬들 (라운드당 1회)
    # 1) Precision Draw: 6~10 카드
    # 2) Safe Draw: A~5 카드
    # 3) Swap Card: 플레이어가 선택한 인덱스 카드 한 장을 버리고 덱에서 1장 뽑음
    # ---------------------------
    def skill_precision_draw(self):
        if self.player_used_skill:
            return "이미 스킬을 사용했습니다."
        rank = random.choice(['6','7','8','9','10'])
        card = Card(random.choice(suits), rank)
        self.player_hand.append(card)
        self.player_used_skill = True
        return f"Precision Draw -> {card}"

    def skill_safe_draw(self):
        if self.player_used_skill:
            return "이미 스킬을 사용했습니다."
        rank = random.choice(['A','2','3','4','5'])
        card = Card(random.choice(suits), rank)
        self.player_hand.append(card)
        self.player_used_skill = True
        return f"Safe Draw -> {card}"

    def skill_swap_card(self):
        if self.player_used_skill:
            return "이미 스킬을 사용했습니다."
        # 플레이어가 교환할 카드 인덱스 선택
        if not self.player_hand:
            return "손패가 없습니다."
        print(f"현재 손패: {self.player_hand}")
        while True:
            try:
                idx = int(input(f"교체할 카드 인덱스 (0 ~ {len(self.player_hand)-1}): "))
                if 0 <= idx < len(self.player_hand):
                    break
                print("유효한 인덱스를 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
        removed = self.player_hand.pop(idx)
        new_card = self.deck.deal()
        self.player_hand.append(new_card)
        self.player_used_skill = True
        return f"Swap: 버린 카드 {removed} -> 새 카드 {new_card}"

    # ---------------------------
    # 플레이어 행동
    # ---------------------------
    def player_hit(self):
        card = self.deck.deal()
        self.player_hand.append(card)
        score = self.calc(self.player_hand)
        return card, score

    # ---------------------------
    # NPC & Dealer 턴
    # ---------------------------
    def npcs_turns(self):
        for npc in self.npcs:
            npc.play_turn(self.deck)

    def dealer_turn(self):
        self.dealer.play_turn(self.deck)

    # ---------------------------
    # 정산: 플레이어 & NPCs
    # 베팅: 플레이어는 self.bet, NPC는 npc.bet
    # 승리: +bet, 패배: -bet, 무승부: 0
    # ---------------------------
    def settle(self):
        results = {}
        player_score = self.calc(self.player_hand)
        dealer_score = self.dealer.score()

        # player vs dealer
        if player_score > 21:
            results['player'] = 'lose'
            player_diff = -self.bet
        elif dealer_score > 21:
            results['player'] = 'win'
            player_diff = +self.bet
        elif player_score > dealer_score:
            results['player'] = 'win'
            player_diff = +self.bet
        elif player_score < dealer_score:
            results['player'] = 'lose'
            player_diff = -self.bet
        else:
            results['player'] = 'draw'
            player_diff = 0

        # update user's balance
        cur_bal = self.user_db.get_balance(self.user_id)
        new_bal = cur_bal + player_diff
        self.user_db.set_balance(self.user_id, new_bal)

        # NPCs vs dealer
        npc_results = {}
        for npc in self.npcs:
            ns = npc.score()
            if ns > 21:
                res = 'lose'; diff = -npc.bet
            elif dealer_score > 21:
                res = 'win'; diff = npc.bet
            elif ns > dealer_score:
                res = 'win'; diff = npc.bet
            elif ns < dealer_score:
                res = 'lose'; diff = -npc.bet
            else:
                res = 'draw'; diff = 0
            npc.balance += diff
            npc_results[npc.name] = (res, diff, npc.balance)
        results['player_diff'] = player_diff
        results['player_balance'] = new_bal
        results['dealer_score'] = dealer_score
        results['npc_results'] = npc_results
        results['player_result'] = results['player']
        return results

    # ---------------------------
    # 스킬 사용 기회 제공 (불리한 상황일 때만)
    # ---------------------------
    def try_offer_skill(self):
        if self.player_used_skill:
            return False, "이미 스킬 사용됨."
        if not self.is_bad_situation():
            return False, "현재는 스킬 사용 조건(불리한 상황)이 아닙니다."
        # 제공
        print("\n=== 불리한 상황 감지: 스킬 사용 가능 ===")
        print("1) Precision Draw (6~10 카드 추가)")
        print("2) Safe Draw (A~5 카드 추가)")
        print("3) Swap Card (손패 한 장을 버리고 덱에서 1장 뽑음)")
        print("0) 사용 안함")
        choice = input("스킬 선택: ").strip()
        if choice == '1':
            msg = self.skill_precision_draw()
            return True, msg
        elif choice == '2':
            msg = self.skill_safe_draw()
            return True, msg
        elif choice == '3':
            msg = self.skill_swap_card()
            return True, msg
        else:
            return False, "스킬 사용 안함."

# =======================================
# UI / 메인 루프
# =======================================
def start_game_loop():
    db = UserDB()
    print("===== NPC 블랙잭 (스킬: 불리할 때만 사용) =====")
    while True:
        print("\n1. 회원가입  2. 로그인  3. 종료")
        cmd = input("선택: ").strip()
        if cmd == '1':
            uid = input("ID: ").strip()
            pw = input("PW: ").strip()
            ok, msg = db.register(uid, pw)
            print(msg)
        elif cmd == '2':
            uid = input("ID: ").strip()
            pw = input("PW: ").strip()
            ok, msg = db.login(uid, pw)
            print(msg)
            if ok:
                user_loop(db, uid)
        elif cmd == '3':
            print("종료합니다.")
            break
        else:
            print("올바른 선택을 하세요.")

def user_loop(db, uid):
    print(f"\n환영합니다 {uid} (잔액: {db.get_balance(uid)}칩)")
    while True:
        bal = db.get_balance(uid)
        print(f"\n현재 잔액: {bal}칩")
        print("1. 새 라운드  2. 로그아웃")
        cmd = input("선택: ").strip()
        if cmd == '2':
            print("로그아웃합니다.")
            break
        if cmd != '1':
            print("잘못된 입력")
            continue
        # 베팅
        try:
            bet = int(input("베팅 금액 입력 (0: 취소): ").strip())
        except ValueError:
            print("숫자를 입력하세요.")
            continue
        if bet == 0:
            continue
        if bet < 0:
            print("양수를 입력하세요.")
            continue
        if bet > bal:
            print("잔액 부족.")
            continue

        # 라운드 실행
        game = BlackjackGame(db, uid, bet)
        print("\n--- 초기 패 ---")
        print(f"플레이어: {game.player_hand} (점수: {game.calc(game.player_hand)})")
        print(f"딜러 오픈카드: {game.dealer.hand[0]}")
        for npc in game.npcs:
            print(f"{npc.name}: [{npc.hand[0]}, ?]")

        # 스킬 기회(라운드 시작 시 조건에 따라 제공)
        offered, msg = game.try_offer_skill()
        if offered:
            print(msg)
            print(f"현재 손패: {game.player_hand} (점수: {game.calc(game.player_hand)})")
        else:
            # msg may explain reason
            if msg:
                print(msg)

        # 플레이어 턴 (Hit/Stand), 스킬은 Hit 후에도 한 번 더 체크할 수 있도록 루프에서 try_offer_skill 호출
        while True:
            print(f"\n내 패: {game.player_hand} (점수: {game.calc(game.player_hand)})")
            act = input("행동 선택 (hit / stand): ").strip().lower()
            if act == 'hit':
                card, score = game.player_hit()
                print(f"카드 받음: {card} -> 점수: {score}")
                if score > 21:
                    print("버스트!")
                    break
                # Hit 후 불리 상황이면 다시 스킬 제안
                offered, msg = game.try_offer_skill()
                if offered:
                    print(msg)
                    print(f"현재 손패: {game.player_hand} (점수: {game.calc(game.player_hand)})")
                continue
            elif act == 'stand':
                break
            else:
                print("잘못된 입력")

        # NPC 및 딜러 턴
        game.npcs_turns()
        game.dealer_turn()

        # 결과 및 정산
        res = game.settle()
        print("\n===== 라운드 결과 =====")
        print(f"딜러 패: {game.dealer.hand} (점수: {res['dealer_score']})")
        print(f"플레이어 패: {game.player_hand} (점수: {game.calc(game.player_hand)}) -> {res['player_result']}")
        print(f"플레이어 잔액 변화: {res['player_diff']} -> 잔액: {res['player_balance']}")

        print("\nNPC 결과:")
        for name, (r, diff, bal) in res['npc_results'].items():
            print(f"{name}: {r} / 변화: {diff} / 잔액: {bal}")

        print("\n라운드 종료.")

if __name__ == "__main__":
    start_game_loop()
