import random

# =======================================
# L-01 ~ L-06 : 블랙잭 게임 로직 (핵심 부품)
# =======================================

# 1. 카드/덱 관련 
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
        return f"{self.suit[0]}_{self.rank}" 

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in suits for r in ranks]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        """ 일반 카드 뽑기 """
        if not self.cards:
            self.cards = [Card(s, r) for s in suits for r in ranks]
            self.shuffle()
        return self.cards.pop()

    # L-08 아이템 1: 1~5 사이의 카드 뽑기 (A 포함)
    def deal_low_card(self):
        low_ranks = ['A', '2', '3', '4', '5']
        filtered_cards = [c for c in self.cards if c.rank in low_ranks]
        
        # 덱에 해당 카드가 없으면 일반 deal로 대체 (재고 부족)
        if not filtered_cards:
            return self.deal() 
        
        card_to_deal = random.choice(filtered_cards)
        self.cards.remove(card_to_deal) 
        return card_to_deal
        
    # L-09 아이템 2: 6~10 사이의 카드 뽑기
    def deal_high_card(self):
        high_ranks = ['6', '7', '8', '9', '10']
        filtered_cards = [c for c in self.cards if c.rank in high_ranks]
        
        if not filtered_cards:
            return self.deal()
            
        card_to_deal = random.choice(filtered_cards)
        self.cards.remove(card_to_deal)
        return card_to_deal
        
    def peek_next_card(self):
        """ NPC-1(안정형) 스킬을 위한 다음 카드 미리보기 (뽑지 않고 확인만) """
        if not self.cards:
            return None # 덱이 비었을 경우
        return self.cards[-1]

# 2. NPC 클래스 추가 (L-07)
class NPC:
    def __init__(self, name, npc_type, bet_amount, balance=1000):
        self.name = name
        self.type = npc_type  # 'SAFE', 'AGGRESSIVE', 'UNIQUE'
        self.hand = []
        self.bet = bet_amount
        self.balance = balance  # NPC의 잔액
        self.used_skill_this_round = False # 능동 스킬 사용 여부
        self.round_completed = False
        
    def score(self, game_ref):
        """ BlackjackGame의 점수 계산 함수를 사용합니다. """
        return game_ref.calculate_score(self.hand)

# 3. Dealer 클래스 (유지)
class Dealer:
    def __init__(self):
        self.hand = []
    def play_turn(self, deck, game_ref):
        while game_ref.calculate_score(self.hand) < 17:
            self.hand.append(deck.deal())
        return self.hand

class BlackjackGame:
    # L-17 아이템 가격 정의
    ITEM_PRICES = {
        'item_low': 50,  # 1~5 카드 뽑기
        'item_high': 80   # 6~10 카드 뽑기
    }
    
    def __init__(self, npc_balances=None):
        """
        Args:
            npc_balances: dict, NPC 이름을 키로 하고 잔액을 값으로 하는 딕셔너리
                          예: {"NPC-1 (안정형)": 1000, "NPC-2 (공격형)": 800, ...}
        """
        self.deck = Deck()
        self.player_hand = []
        self.dealer_hand = []
        self.bet_amount = 0 
        
        # L-10 NPC 인스턴스 생성 (잔액 정보 포함)
        if npc_balances is None:
            npc_balances = {}
        
        self.npcs = [
            NPC("NPC-1 (안정형)", 'SAFE', 100, npc_balances.get("NPC-1 (안정형)", 1000)), 
            NPC("NPC-2 (공격형)", 'AGGRESSIVE', 100, npc_balances.get("NPC-2 (공격형)", 1000)),
            NPC("NPC-3 (특이형)", 'UNIQUE', 100, npc_balances.get("NPC-3 (특이형)", 1000))
        ]
        
        # NPC의 정산 결과를 저장할 딕셔너리
        self.npc_round_results = {}
        
        # 공격형 NPC 패시브 발동 여부 추적 (라운드당 1회만)
        self.aggressive_passive_used_this_round = False 

    # L-01 게임 세팅 (NPC 초기화 포함)
    def start_game(self, bet: int):
        self.bet_amount = bet
        self.deck.shuffle() 
        self.player_hand = [self.deck.deal(), self.deck.deal()]
        self.dealer_hand = [self.deck.deal(), self.deck.deal()]
        
        # 공격형 NPC 패시브 발동 여부 초기화
        self.aggressive_passive_used_this_round = False
        
        # L-12 NPC에게도 카드 지급 및 상태 초기화
        for npc in self.npcs:
            # NPC 잔액이 100 이하이면 자동으로 100 충전
            if npc.balance <= 100:
                npc.balance = 100
            
            # NPC가 배팅할 수 있는 최대 금액은 잔액과 배팅 금액 중 작은 값
            npc.bet = min(bet, npc.balance)
            
            npc.hand = [self.deck.deal(), self.deck.deal()]
            npc.used_skill_this_round = False
            npc.round_completed = False
            
        initial_dialogues = self.get_current_npc_dialogues()
        # GUI에 전달할 초기 상태 반환
        return {
            "player_hand": self.player_hand,
            "dealer_hand_hidden": [self.dealer_hand[0], 'BACK'],
            "npc_hands": {n.name: [n.hand[0], 'BACK'] for n in self.npcs},
            "npc_dialogues": initial_dialogues
        }

    # A 관련 판정 로직 (유지)
    def calculate_score(self, hand):
        total = 0
        aces = 0
        for card in hand:
            # Note: Card.__repr__이 'S_A' 형태이므로, 이 함수는 Card 객체의 리스트를 받아야 합니다.
            if card == '?': continue 
            total += values[card.rank]
            if card.rank == 'A':
                aces += 1
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    # L-03 플레이어 액션 (유지)
    def player_hit(self):
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
            "status": status 
        }

    # L-18 아이템 구매 및 사용 함수 (재정의됨)
    def purchase_and_use_item(self, item_type: str, player_balance: int):
        price = self.ITEM_PRICES.get(item_type)
        if price is None:
            return {"status": "InvalidItem", "cost": 0}
            
        if player_balance < price:
            return {"status": "InsufficientFunds", "cost": price}

        cost = price
        
        if item_type == 'item_low':
            new_card = self.deck.deal_low_card()
        else:
            new_card = self.deck.deal_high_card()
            
        self.player_hand.append(new_card)
        score = self.calculate_score(self.player_hand)
        
        status = "ItemUsed"
        if score > 21:
            status = "BustAfterItem"
            
        return {
            "status": status,
            "cost": cost,                   
            "new_card": new_card,
            "player_hand": self.player_hand,
            "score": score
        }

    # L-19 공격형 NPC 패시브 체크 함수 (Controller에서 Stand 전에 호출)
    def check_aggressive_passive(self):
        # 라운드당 1회만 발동되도록 체크
        if self.aggressive_passive_used_this_round:
            return False, "", None
        
        player_score = self.calculate_score(self.player_hand)
        
        # 1. 플레이어 점수 17 이상 확인
        if player_score < 17 or player_score > 21:
            return False, "", None 
            
        # 2. 공격형 NPC 점수 17 이상 확인
        aggressive_npc = next((n for n in self.npcs if n.type == 'AGGRESSIVE'), None)
        if aggressive_npc is None:
            return False, "", None
            
        # NPC는 카드 1장이 히든이 아니므로 현재 핸드로 점수 계산
        npc_score = self.calculate_score(aggressive_npc.hand) 
        if npc_score < 17 or npc_score > 21:
            return False, "", aggressive_npc.name
            
        # 3. 40% 확률 발동 (조건 만족 시 무조건 발동)
        if random.random() < 0.6:
            self.aggressive_passive_used_this_round = True  # 발동 플래그 설정
            return True, f"{aggressive_npc.name}의 패시브 발동! 플레이어 강제 HIT.", aggressive_npc.name
            
        return False, "", aggressive_npc.name
    
    # L-13 NPC 턴 (능동 스킬 + 대사)
    def npc_single_round_step(self):
        """각 NPC가 한 번씩 행동하는 단계를 반환합니다."""
        steps = []
        for npc in self.npcs:
            if getattr(npc, "round_completed", False):
                continue
            step = self._npc_take_step(npc)
            if step:
                steps.append(step)
        return steps

    def _npc_take_step(self, npc: NPC):
        dialogues = []
        score = self.calculate_score(npc.hand)

        if score > 21:
            dialogues.extend(self._npc_bust_lines(npc.type))
            npc.round_completed = True
            return {
                "name": npc.name,
                "hand": list(npc.hand),
                "dialogues": dialogues,
                "state": "bust"
            }

        if npc.type == 'AGGRESSIVE':
            decision = self._play_aggressive_turn(npc, score, dialogues)
        elif npc.type == 'SAFE':
            decision = self._play_safe_turn(npc, score, dialogues)
        else:
            decision = self._play_unique_turn(npc, score, dialogues)

        if decision != "continue":
            npc.round_completed = True
        else:
            npc.round_completed = False

        return {
            "name": npc.name,
            "hand": list(npc.hand),
            "dialogues": dialogues,
            "state": decision
        }

    def npcs_play_turn(self, capture_steps: bool = False):
        turn_results = {}
        action_steps = [] if capture_steps else None

        for npc in self.npcs:
            # 이미 Stand하거나 Bust한 NPC는 건너뛰기
            if npc.round_completed:
                # 이미 완료된 NPC의 현재 상태를 결과에 포함
                npc_score = self.calculate_score(npc.hand)
                if npc_score > 21:
                    final_state = "bust"
                else:
                    final_state = "stand"
                turn_results[npc.name] = {
                    "hand": list(npc.hand),
                    "dialogues": [],
                    "final_score": npc_score,
                    "state": final_state
                }
                continue
            
            dialogues = []
            final_state = "stand"

            def record_step(state_label: str):
                if action_steps is None:
                    return
                action_steps.append({
                    "name": npc.name,
                    "hand": list(npc.hand),
                    "dialogues": list(dialogues),
                    "state": state_label
                })

            while True:
                score = self.calculate_score(npc.hand)

                if score > 21:
                    dialogues.extend(self._npc_bust_lines(npc.type))
                    final_state = "bust"
                    npc.round_completed = True
                    record_step("bust")
                    break

                if npc.type == 'AGGRESSIVE':
                    decision = self._play_aggressive_turn(npc, score, dialogues)
                elif npc.type == 'SAFE':
                    decision = self._play_safe_turn(npc, score, dialogues)
                else:
                    decision = self._play_unique_turn(npc, score, dialogues)

                record_step(decision)

                if decision == "continue":
                    npc.round_completed = False
                    continue

                final_state = decision
                npc.round_completed = True
                break

            turn_results[npc.name] = {
                "hand": list(npc.hand),
                "dialogues": dialogues,
                "final_score": self.calculate_score(npc.hand),
                "state": final_state
            }

        if capture_steps:
            return turn_results, action_steps

        return turn_results

    def _play_aggressive_turn(self, npc: NPC, score: int, dialogues: list):
        if not npc.used_skill_this_round and 9 <= score <= 11:
            dialogues.append("찬스는 놓칠 수 없죠!")
            dialogues.append("[스킬 : 더블 다운] 발동")
            npc.bet *= 2
            npc.hand.append(self.deck.deal())
            npc.used_skill_this_round = True
            return "double_down"

        if 12 <= score <= 16:
            dialogues.append("가보는 겁니다!")
            npc.hand.append(self.deck.deal())
            return "continue"

        if score == 17:
            dialogues.append("에이 17점은 너무 낮아요")
            npc.hand.append(self.deck.deal())
            return "continue"

        if 18 <= score <= 21:
            dialogues.append("이 정도면 만족하죠")
            return "stand"

        if score <= 8:
            dialogues.append("더 가야죠!")
            npc.hand.append(self.deck.deal())
            return "continue"

        return "stand"

    def _play_safe_turn(self, npc: NPC, score: int, dialogues: list):
        if 4 <= score <= 11:
            dialogues.append("음, 나쁘지 않네요.")
            npc.hand.append(self.deck.deal())
            return "continue"

        if 12 <= score <= 16:
            dialogues.append("아... 이거 애매한데요...")
            dialogues.append("[스킬: 위기 감지] 발동")
            npc.used_skill_this_round = True
            next_card = self.deck.peek_next_card()
            if not next_card:
                dialogues.append("덱이 비었네요. 여기서 멈출게요.")
                return "stand"

            temp_score = self.calculate_score(npc.hand + [next_card])
            if temp_score > 21:
                dialogues.append("다음 카드가 위험해요. 그냥 스탠드하겠습니다.")
                return "stand"

            dialogues.append("괜찮을 것 같네요. 한 장 더.")
            npc.hand.append(self.deck.deal())
            return "continue"

        if 17 <= score <= 19:
            dialogues.append("이 정도면 충분하네요.")
            return "stand"

        if score >= 20:
            dialogues.append("이 정도면 완벽합니다.")
            return "stand"

        dialogues.append("조심스럽게 한 장 더.")
        npc.hand.append(self.deck.deal())
        return "continue"

    def _play_unique_turn(self, npc: NPC, score: int, dialogues: list):
        if score <= 12:
            dialogues.append("한 장 더.")
            npc.hand.append(self.deck.deal())
            return "continue"

        if 13 <= score <= 16:
            if not npc.used_skill_this_round:
                dialogues.append("이런 끔찍한 패로는 안돼. 다시 받겠다!")
                dialogues.append("[스킬 : 리로드] 발동")
                npc.hand = [self.deck.deal(), self.deck.deal()]
                npc.used_skill_this_round = True
                return "continue"

            dialogues.append("아직 부족해. 한 장 더.")
            npc.hand.append(self.deck.deal())
            return "continue"

        if 17 <= score <= 21:
            dialogues.append("어디 한번 이겨보시지!")
            return "stand"

        return "stand"

    def _npc_bust_lines(self, npc_type: str):
        if npc_type == 'AGGRESSIVE':
            return ["안돼... 이럴 리가..", "패배다..."]
        if npc_type == 'SAFE':
            return ["어, 이런... 버스트네요.", "다음엔 더 조심해야겠어요."]
        return ["으... 계획이 어긋났군.", "다음 판을 노리지."]

    def _npc_preview_dialogue(self, npc: NPC):
        score = self.calculate_score(npc.hand)
        if npc.type == 'AGGRESSIVE':
            if 9 <= score <= 11:
                return ["찬스는 놓칠 수 없죠!", "[스킬 : 더블 다운] 준비 중"]
            if 12 <= score <= 16:
                return ["가보는 겁니다!", f"현재 점수: {score}"]
            if score == 17:
                return ["에이 17점은 너무 낮아요"]
            if 18 <= score <= 21:
                return ["이 정도면 만족하죠"]
            return [f"준비 중... (점수 {score})"]

        if npc.type == 'SAFE':
            if 4 <= score <= 11:
                return ["음, 나쁘지 않네요."]
            if 12 <= score <= 16:
                return ["아... 이거 애매한데요...", "[스킬: 위기 감지] 준비 중"]
            if 17 <= score <= 19:
                return ["이 정도면 충분하네요."]
            return [f"조심스럽게 보겠습니다. (점수 {score})"]

        # UNIQUE
        if score <= 12:
            return ["한 장 더 생각 중이다."]
        if 13 <= score <= 16:
            return ["이런 끔찍한 패로는 안돼. 다시 받겠다!", "[스킬 : 리로드] 준비 중"]
        if 17 <= score <= 21:
            return ["어디 한번 이겨보시지!"]
        return [f"지켜본다... (점수 {score})"]

    # 딜러턴 (유지)
    def dealer_turn(self):
        while self.calculate_score(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal())
        return self.dealer_hand 

    # L-05/06 결과 판정 및 정산 (NPC 패시브 추가)
    def check_result(self):
        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand)
        
        # --- 1. 플레이어 VS 딜러 기본 정산 ---
        player_payout = 0
        player_result = "Push (Tie)"
        
        if player_score > 21:
            player_result, player_payout = "Lose (Bust)", -self.bet_amount
        elif dealer_score > 21:
            player_result, player_payout = "Win (Dealer Bust)", self.bet_amount
        elif player_score > dealer_score:
            player_result, player_payout = "Win", self.bet_amount
        elif player_score < dealer_score:
            player_result, player_payout = "Lose", -self.bet_amount
        
        # 블랙잭 룰 적용
        if player_score == 21 and len(self.player_hand) == 2 and player_result != "Lose": 
            player_result, player_payout = "Blackjack!", int(self.bet_amount * 1.5)


        # --- 2. NPC VS 딜러 기본 정산 및 패시브 적용 ---
        
        total_additional_loss = 0 # 특이 NPC 패시브 적용 시 플레이어의 추가 손실
        npc_settlement_details = {}
        passive_dialogues = {n.name: [] for n in self.npcs}
        teamwork_bonus = 0

        for npc in self.npcs:
            npc_score = self.calculate_score(npc.hand)
            npc_payout = 0
            npc_result = "Push (Tie)"

            if npc_score > 21:
                npc_result, npc_payout = "Lose (Bust)", -npc.bet
            elif dealer_score > 21:
                npc_result, npc_payout = "Win (Dealer Bust)", npc.bet
            elif npc_score > dealer_score:
                npc_result, npc_payout = "Win", npc.bet
            elif npc_score < dealer_score:
                npc_result, npc_payout = "Lose", -npc.bet
            
            
            # L-15 안정형 NPC 패시브 적용: (플레이어 Win & NPC Win) -> +30% 보너스
            if npc.type == 'SAFE' and player_result.startswith("Win") and npc_result.startswith("Win"):
                bonus = int(self.bet_amount * 0.3)
                teamwork_bonus += bonus
                passive_dialogues[npc.name].append("[팀워크] 우리가 해냈습니다! 믿고 있었다구요!")
                
            # L-16 특이 NPC 패시브 적용: (플레이어 Lose & NPC Win) -> 플레이어 추가 20% 손실
            elif npc.type == 'UNIQUE' and player_result.startswith("Lose") and npc_result.startswith("Win"):
                additional_loss = int(self.bet_amount * 0.2)
                total_additional_loss += additional_loss
                passive_dialogues[npc.name].append("[견제] 이런, 아쉽게 됐네요")
                
            
            # NPC 잔액 업데이트
            npc.balance += npc_payout
            
            npc_settlement_details[npc.name] = {
                "result": npc_result,
                "payout": npc_payout,
                "score": npc_score,
                "new_balance": npc.balance
            }

        # --- 3. 최종 플레이어 정산 ---
        final_player_payout = player_payout + teamwork_bonus - total_additional_loss

        # NPC 잔액 정보 딕셔너리 생성
        npc_balances = {npc.name: npc.balance for npc in self.npcs}

        return {
            "result_msg": player_result, 
            "payout": final_player_payout,      
            "player_hand": self.player_hand,
            "dealer_hand": self.dealer_hand,
            "player_score": player_score,
            "dealer_score": dealer_score,
            "npc_results": npc_settlement_details,
            "passive_dialogues": passive_dialogues,
            "teamwork_bonus": teamwork_bonus,
            "unique_penalty": total_additional_loss,
            "npc_balances": npc_balances
        }

    def get_current_npc_dialogues(self):
        return {npc.name: self._npc_preview_dialogue(npc) for npc in self.npcs}
    
    def get_npc_balances(self):
        """현재 NPC들의 잔액 정보를 반환합니다."""
        return {npc.name: npc.balance for npc in self.npcs}