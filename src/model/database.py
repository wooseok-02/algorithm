import sqlite3

# 데이터베이스 파일 이름을 바꾸고 싶을 때 이 한 줄만 바꾸면 됨.
DB_FILE = "blackjack.db"    

def initialize_db(conn):

    cur = conn.cursor()

    # 사용자 정보를 저장하는 users 테이블 생성
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, -- 사용자의 고유 번호 (자동 증가)
        username TEXT UNIQUE NOT NULL,       -- 사용자 아이디 (중복 불가)
        hashed_password TEXT NOT NULL,       -- (로직 팀이) 암호화한 비밀번호
        salt TEXT NOT NULL,                  -- 암호화에 사용된 '솔트' 값
        bankroll INTEGER DEFAULT 100         -- 사용자의 보유 칩 (기본값 100)
    )
    """)

    # 게임 기록을 저장하는 games 테이블 생성
    cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 게임 한 판의 고유 번호 (자동 증가)
        player_id INTEGER,                       -- 게임을 한 사용자 ID (users.id)
        bet INTEGER,                             -- 베팅한 금액
        result TEXT,                             -- 게임 결과 (예: "Win", "Lose")
        payout INTEGER,                          -- 이기거나 잃은 금액
        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 게임이 끝난 시간 (자동 기록)
        FOREIGN KEY(player_id) REFERENCES users(id)  -- users 테이블의 id를 참조
    )
    """)
    conn.commit()    

def create_user(conn, username: str, hashed_password: str, salt: str) -> bool:
    """[로직 팀이 호출] 암호화된 비밀번호와 salt를 받아 새 사용자를 DB에 생성합니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        username: 사용자 이름
        hashed_password: (로직 팀이 암호화한) 해시된 비밀번호
        salt: (로직 팀이 생성한) 솔트 값

    Returns:
        bool: 생성 성공 시 True, 사용자 이름 중복 시 False
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, hashed_password, salt) VALUES (?, ?, ?)",
            (username, hashed_password, salt)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    

def get_user_by_username(conn, username: str) -> tuple | None:
    """[로직 팀이 호출] 사용자 이름으로 (id, 해시, 솔트, 칩) 정보를 조회합니다.

    Args:
        conn: 데이터베이스 커넥션 객체
        username: 조회할 사용자 이름

    Returns:
        tuple | None: 사용자 정보가 담긴 튜플 또는 None
    """
    cur = conn.cursor()
    cur.execute("SELECT id, hashed_password, salt, bankroll FROM users WHERE username=?", (username,))
    return cur.fetchone()


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

