# [파일 이름: game_controller.py]
# '문제의 백엔드 코드'에서 쓸모없는 것(UserDB, main, print)을 모두 제거하고
# GUI와 DB에 '연결'할 수 있도록 '부품'만 추출하고 수정한 파일입니다.

import random

# =======================================
# L-01 ~ L-06 : 블랙잭 게임 로직 (핵심 부품)
# =======================================

# 1. 카드/덱 관련 (이식) - 이 부분은 완벽해서 수정 없음
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
        """ GUI가 카드 이미지를 찾을 수 있도록 'S_A', 'H_10' 같은 형식으로 변경 """
        # (Pillow 이미지가 'H10.png'가 아니라 'H_10.png'일 것 같아서 수정)
        return f"{self.suit[0]}_{self.rank}" # 예: '♠A' -> 'S_A'

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in suits for r in ranks]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop()

# 2. 블랙잭 게임 클래스 (대대적 수술)
class BlackjackGame:
    def __init__(self):
        """ 
        [수정됨]
        - 클래스 생성 시 덱만 준비합니다. 
        - 칩(bankroll)이나 베팅액은 여기서 관리하지 않습니다.
        - player_hand, dealer_hand는 start_game에서 생성됩니다.
        """
        self.deck = Deck()
        self.player_hand = []
        self.dealer_hand = []
        self.bet_amount = 0 # 이번 판의 베팅액

    # L-01 게임 세팅 (수정됨)
    def start_game(self, bet: int):
        """
        [수정됨]
        - GUI에서 '게임 시작' 시 베팅액을 받아 게임을 세팅합니다.
        - 덱을 새로 셔플하고, 2장씩 카드를 뽑습니다.
        """
        self.bet_amount = bet
        self.deck.shuffle() # 매 게임 새로 셔플
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        
        # GUI에 전달할 초기 상태 반환
        return {
            "player_hand": self.player_hand,
            "dealer_hand_hidden": [self.dealer_hand[0], '?'] # 딜러 1장 숨김
        }

    # A 관련 판정 로직
    def calculate_score(self, hand):
        total = 0
        aces = 0
        for card in hand:
            if card == '?': continue # 숨겨진 카드는 계산 안 함
            total += values[card.rank]
            if card.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    # L-03 플레이어 액션 (수정됨)
    def player_hit(self):
        """
        [수정됨]
        - Hit 액션을 처리하고, GUI가 업데이트할 데이터를 반환(return)합니다.
        - print() 대신 return을 사용합니다.
        """
        new_card = self.deck.deal()
        self.player_hand.append(new_card)
        score = self.calculate_score(self.player_hand)
        
        status = "Hit"
        if score > 21:
            status = "Bust"
            
        return {
            "new_card": new_card,
            "player_hand": self.player_hand,
            "score": score,
            "status": status  # "Hit" or "Bust"
        }

    # 딜러턴 / 스탠스 시 함수 호출
    def dealer_turn(self):
        while self.calculate_score(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal())
        return self.dealer_hand # GUI 업데이트를 위해 딜러의 최종 패 반환

    # L-05/06 결과 판정 및 정산 (대대적 수술)
    def check_result(self):

        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand)

        if player_score > 21:
            result, payout = "Lose (Bust)", -self.bet_amount
        elif dealer_score > 21:
            result, payout = "Win (Dealer Bust)", self.bet_amount
        elif player_score > dealer_score:
            result, payout = "Win", self.bet_amount
        elif player_score < dealer_score:
            result, payout = "Lose", -self.bet_amount
        else:
            result, payout = "Push (Tie)", 0
            
        # (블랙잭 룰 추가)
        if player_score == 21 and len(self.player_hand) == 2:
            result, payout = "Blackjack!", int(self.bet_amount * 1.5)

        return {
            "result_msg": result,    # 예: "Win", "Lose", "Blackjack!"
            "payout": payout,        # 예: 100, -100, 150, 0
            "player_hand": self.player_hand,
            "dealer_hand": self.dealer_hand,
            "player_score": player_score,
            "dealer_score": dealer_score
        }

    # (참고) Surrender는 L-03의 player_surrender()인데, 
    # 이건 GUI에서 버튼 클릭 시 바로 -bet//2를 계산하면 되므로 
    # 이 클래스에 굳이 만들 필요는 없어 보입니다. (GUI에서 처리)