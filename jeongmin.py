import random
import sys

# =======================================
# SYS-01, SYS-02 : 로그인 / 회원가입 로직
# =======================================
class UserDB:
    def __init__(self):
        self.users = {}  # {id: password}

    def register(self, user_id, password):
        if user_id in self.users:
            return False, "이미 존재하는 ID입니다."
        self.users[user_id] = password
        return True, "회원가입 성공!"

    def login(self, user_id, password):
        if user_id not in self.users:
            return False, "존재하지 않는 ID입니다."
        if self.users[user_id] != password:
            return False, "비밀번호가 올바르지 않습니다."
        return True, "로그인 성공!"


# =======================================
# L-01 ~ L-06 : 블랙잭 게임 로직
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
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop()


class BlackjackGame:
    def __init__(self, player_name, bet_amount):
        self.deck = Deck()
        self.player_name = player_name
        self.bet_amount = bet_amount
        self.balance = 1000  # 초기 칩
        self.player_hand = []
        self.dealer_hand = []
        self.start_game()

    # L-01 게임 세팅
    def start_game(self):
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]

    # L-02 점수 계산 (Ace 규칙 포함)
    def calculate_score(self, hand):
        total = 0
        aces = 0
        for card in hand:
            total += values[card.rank]
            if card.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    # L-03 플레이어 액션 처리
    def player_hit(self):
        self.player_hand.append(self.deck.deal())
        score = self.calculate_score(self.player_hand)
        if score > 21:
            return "Bust!"
        return f"Hit 완료! 현재 점수: {score}"

    def player_surrender(self):
        self.balance -= self.bet_amount // 2
        return f"항복! 베팅액 절반({self.bet_amount // 2})이 차감되었습니다."

    # L-04 딜러 턴 진행
    def dealer_turn(self):
        while self.calculate_score(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal())

    # L-05 결과 판정
    def check_result(self):
        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand)

        if player_score > 21:
            return self.settle("lose")
        elif dealer_score > 21:
            return self.settle("win")
        elif player_score > dealer_score:
            return self.settle("win")
        elif player_score < dealer_score:
            return self.settle("lose")
        else:
            return self.settle("push")

    # L-06 배팅 정산
    def settle(self, result):
        if result == "win":
            self.balance += self.bet_amount
            msg = f"승리! +{self.bet_amount}칩"
        elif result == "lose":
            self.balance -= self.bet_amount
            msg = f"패배! -{self.bet_amount}칩"
        else:
            msg = "무승부! 칩 변동 없음."
        return {
            "결과": result,
            "플레이어": self.player_hand,
            "딜러": self.dealer_hand,
            "플레이어 점수": self.calculate_score(self.player_hand),
            "딜러 점수": self.calculate_score(self.dealer_hand),
            "잔액": self.balance,
            "메시지": msg
        }


# =======================================
# 메인 루프 (회원가입 → 로그인 → 게임)
# =======================================
def main():
    db = UserDB()

    print("===== 🃏 블랙잭 게임 시스템 =====")
    while True:
        print("\n1. 회원가입")
        print("2. 로그인")
        print("3. 종료")
        choice = input("번호를 선택하세요: ")

        if choice == "1":
            user_id = input("새 ID: ")
            pw = input("새 PW: ")
            ok, msg = db.register(user_id, pw)
            print(msg)

        elif choice == "2":
            user_id = input("ID: ")
            pw = input("PW: ")
            ok, msg = db.login(user_id, pw)
            print(msg)
            if ok:
                start_blackjack(user_id)
        elif choice == "3":
            print("프로그램을 종료합니다.")
            sys.exit()
        else:
            print("잘못된 입력입니다.")


def start_blackjack(user_name):
    print(f"\n🎮 {user_name}님, 블랙잭 게임을 시작합니다.")
    bet = int(input("베팅 금액을 입력하세요 (예: 100): "))
    game = BlackjackGame(player_name=user_name, bet_amount=bet)

    while True:
        print("\n===== 현재 상황 =====")
        print(f"플레이어 패: {game.player_hand} (점수: {game.calculate_score(game.player_hand)})")
        print(f"딜러 패: [{game.dealer_hand[0]}, ?]")
        print("======================")

        action = input("행동 선택 (Hit / Stand / Surrender): ").lower()

        if action == "hit":
            result = game.player_hit()
            print(result)
            if "Bust" in result:
                final = game.settle("lose")
                show_result(final)
                break

        elif action == "stand":
            game.dealer_turn()
            final = game.check_result()
            show_result(final)
            break

        elif action == "surrender":
            msg = game.player_surrender()
            print(msg)
            break

        else:
            print("잘못된 입력입니다.")


def show_result(result):
    print("\n===== 🧾 게임 결과 =====")
    print(f"플레이어 패: {result['플레이어']} (점수: {result['플레이어 점수']})")
    print(f"딜러 패: {result['딜러']} (점수: {result['딜러 점수']})")
    print(f"결과: {result['결과'].upper()} / {result['메시지']}")
    print(f"현재 잔액: {result['잔액']}")
    print("=======================")


# =======================================
# 실행
# =======================================
if __name__ == "__main__":
    main()
