import sqlite3
import hashlib  # 비밀번호 암호화(해싱)를 위한 라이브러리
import os       # 암호화용 무작위 값(salt) 생성을 위한 라이브러리

# 데이터베이스 파일 이름을 바꾸고 싶을 때 이 한 줄만 바꾸면 됨.
DB_FILE = "blackjack.db"    

def initialize_db(conn):
    """데이터베이스 연결을 받아 테이블들을 초기화합니다.

    users 테이블과 games 테이블이 없으면 새로 생성합니다.
    """
    cur = conn.cursor()

    # 사용자 정보를 저장하는 users 테이블 생성
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        salt TEXT NOT NULL,
        bankroll INTEGER DEFAULT 100
    )
    """)

     # 게임 기록을 저장하는 games 테이블 생성
    cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        bet INTEGER,
        result TEXT,
        payout INTEGER,
        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(player_id) REFERENCES users(id)
    )
    """)
    conn.commit()

def _hash_password(password: str, salt: bytes) -> str: 
    """비밀번호와 무작위 값(salt)를 받아서 PBKDF2-SHA256 해시(암호화된 결과물)를 생성하는 함수입니다.

    내부적으로만 사용되는 헬퍼(helper) 함수입니다.
    """
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()

def register_user(conn, username: str, password: str) -> bool:
    """새로운 사용자를 등록하고 DB에 저장하는 함수입니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        username: 등록할 사용자 이름
        password: 등록할 사용자의 비밀번호

    Returns:
        bool: 회원가입 성공 시 True, 사용자 이름 중복 시 False를 반환합니다.
    """
    salt = os.urandom(16)   # os 도구를 써서 나만의 무작위 값(salt)을 16글자 만듦
    hashed_pass = _hash_password(password, salt)    # _hash_password 함수한테 password랑 salt값을 줘서 아무도 못 알아보게 암호화 (hashed_pass)
    try:                    
        cur = conn.cursor() 
        cur.execute("INSERT INTO users (username, hashed_password, salt) VALUES (?, ?, ?)", (username, hashed_pass, salt.hex())) # users 테이블에 username, hashed_pass, salt를 저장하라고 명령(execute)
        conn.commit()       
        return True         # 성공했으면 True
    except sqlite3.IntegrityError: 
        # 저장을 시도하다가 사용자 이름 중복 시 IntegrityError가 발생함(user 테이블 username에 UNIQUE 제약조건이 있음)
        return False        
    
def login_user(conn, username: str, password: str) -> tuple | None:
    """사용자 이름과 비밀번호를 검증하여 로그인합니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        username: 로그인할 사용자 이름
        password: 로그인할 사용자의 비밀번호

    Returns:
        tuple | None: 로그인 성공 시 (user_id, bankroll) 튜플을, 실패 시 None을 반환합니다.
    """
    cur = conn.cursor()
    cur.execute("SELECT id, hashed_password, salt, bankroll FROM users WHERE username=?", (username,)) 
    # users 테이블에서 username이 일치하는 사용자를 찾아서, 그 사람의 id, hashed_password, salt, 칩 개수(bankroll)를 전부 가져오기
    user_data = cur.fetchone()
    if user_data:
        user_id, stored_hash, salt_hex, bankroll = user_data
        salt = bytes.fromhex(salt_hex)
        if _hash_password(password, salt) == stored_hash: # 입력된 password를 저장된 salt로 해싱하여 그 결과가 DB에 원래 저장되어있던 해시값과 일치하는지 비교
            return user_id, bankroll
    return None # 사용자를 못 찾았거나, 비밀번호를 암호화한 결과가 DB의 값과 달랐다면 로그인 실패

def update_bankroll(conn, user_id: int, new_amount: int):
    """특정 사용자의 칩 개수(bankroll)를 업데이트합니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        user_id: 칩 개수를 변경할 사용자의 ID
        new_amount: 새로 설정할 칩의 총량
    """
    cur = conn.cursor()
    cur.execute("UPDATE users SET bankroll=? WHERE id=?", (new_amount, user_id)) 
    # users 테이블의 정보를 수정(UPDATE)할 건데, 단,(WHERE) id가 user_id와 일치하는 사람만 bankroll 값을 new_amount로 바꿈.
    conn.commit() 


def save_game(conn, player_id: int, bet: int, result: str, payout: int):
    """한 판의 게임 결과를 DB의 games 테이블에 기록합니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        player_id: 게임을 한 플레이어의 고유 ID
        bet: 플레이어가 베팅한 금액
        result: 게임 결과 ('Win', 'Loss', 'Push' 등)
        payout: 플레이어가 얻거나 잃은 금액 (상금)
    """
    cur = conn.cursor()
    cur.execute("INSERT INTO games (player_id, bet, result, payout) VALUES (?, ?, ?, ?)", (player_id, bet, result, payout))
    # games 테이블에 새로운 데이터를 추가(INSERT INTO)함. player_id, bet, result, payout 각 항목에 받은 값들을 순서대로 넣음.
    conn.commit()

def get_ranking(conn) -> list[tuple]: 
    """칩(bankroll) 보유량 기준 상위 10명의 랭킹을 조회합니다.

    Returns:
        list[tuple]: (username, bankroll) 튜플이 담긴 리스트를 반환합니다.
    """
    cur = conn.cursor()
    cur.execute("SELECT username, bankroll FROM users ORDER BY bankroll DESC LIMIT 10") 
    # users 테이블에서 모든 사용자의 username과 bankroll을 선택(SELECT)
    # 선택된 결과를 bankroll 기준으로 정렬(ORDER BY)하는데, DESC(내림차순)니까 많은 사람부터 적은 사람 순으로 정렬
    return cur.fetchall()