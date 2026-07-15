import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


KBO_BASE_URL = "https://www.koreabaseball.com"
ROW_SELECTOR = "div.record_result table.tData01 tbody tr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    )
}

# (목록 URL, 선수 유형, 리그 구분)
# GAME_CN(경기수) 정렬 = 누적기록이라 보직/기록 종류에 상관없이 골고루 잡힘
SOURCES = [
    (f"{KBO_BASE_URL}/Record/Player/HitterBasic/Basic1.aspx?sort=GAME_CN", "타자", "1군"),
    (f"{KBO_BASE_URL}/Record/Player/PitcherBasic/Basic1.aspx?sort=GAME_CN", "투수", "1군"),
    (f"{KBO_BASE_URL}/Futures/Player/Hitter.aspx", "타자", "2군"),
    (f"{KBO_BASE_URL}/Futures/Player/Pitcher.aspx", "투수", "2군"),
]


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument(f"--user-agent={HEADERS['User-Agent']}")
    return webdriver.Chrome(options=options)


def clean_header(text):
    text = text.replace("\n", "").replace("\r", "").replace(" ", "").strip()

    header_map = {
        "팀명": "TEAM", "팀": "TEAM",
        "타율": "AVG", "AVG": "AVG",
        "경기": "G", "G": "G",
        "타석": "PA", "PA": "PA",
        "타수": "AB", "AB": "AB",
        "득점": "R", "R": "R",
        "안타": "H", "피안타": "H", "H": "H",
        "홈런": "HR", "피홈런": "HR", "HR": "HR",
        "타점": "RBI", "RBI": "RBI",
        "평균자책점": "ERA", "ERA": "ERA",
        "승": "W", "W": "W",
        "패": "L", "L": "L",
        "세이브": "SV", "SV": "SV",
        "홀드": "HLD", "HLD": "HLD",
        "승률": "WPCT", "WPCT": "WPCT",
        "이닝": "IP", "IP": "IP",
        "볼넷": "BB", "BB": "BB",
        "사구": "HBP", "HBP": "HBP",
        "탈삼진": "SO", "SO": "SO",
        "실점": "R_ALLOWED", "자책점": "ER",
        "WHIP": "WHIP"
    }

    return header_map.get(text, text)


def extract_player_id(tag):
    source = " ".join([tag.get("href", ""), tag.get("onclick", ""), str(tag)])
    patterns = [r"playerId=(\d+)", r"playerId['\"\s,:=()]+(\d+)"]

    for pattern in patterns:
        match = re.search(pattern, source, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


def find_player_candidates(keyword):
    """
    1군 타자 → 1군 투수 → 2군 타자 → 2군 투수 순서로 검색한다.
    목록 페이지 이동은 실제 브라우저(Selenium)로 버튼을 직접 클릭해서
    ASP.NET postback 방식을 안정적으로 처리한다.
    1군에서 찾으면 2군까지 뒤지지 않고 바로 멈춰서 속도를 아낀다.
    """

    candidates = []
    used_ids = set()

    for list_url, player_type, league in SOURCES:
        driver = create_driver()

        try:
            driver.get(list_url)
            time.sleep(1.5)

            page_num = 1
            while page_num <= 20:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                rows = soup.select(ROW_SELECTOR)

                if not rows:
                    break

                for row in rows:
                    name_tag = row.find("a")
                    if name_tag is None:
                        continue

                    name_text = name_tag.get_text(strip=True)
                    if name_text == "":
                        continue

                    if keyword not in name_text and name_text not in keyword:
                        continue

                    player_id = extract_player_id(name_tag)
                    if player_id == "" or player_id in used_ids:
                        continue

                    used_ids.add(player_id)
                    tds = row.find_all("td")
                    team = tds[2].get_text(strip=True) if len(tds) > 2 else ""

                    candidates.append({
                        "name": name_text,
                        "player_id": player_id,
                        "team": team,
                        "position": player_type,
                        "league": league,
                    })

                if candidates:
                    break  # 이 소스에서 찾았으면 다음 페이지 안 넘어감

                moved = False
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, f"a[id*='btnNo{page_num + 1}']")
                    next_btn.click()
                    time.sleep(1.2)
                    page_num += 1
                    moved = True
                except NoSuchElementException:
                    pass

                if not moved:
                    try:
                        next_group_btn = driver.find_element(By.CSS_SELECTOR, "a[id*='btnNext']")
                        next_group_btn.click()
                        time.sleep(1.2)
                        page_num += 1
                        moved = True
                    except NoSuchElementException:
                        pass

                if not moved:
                    break

        finally:
            driver.quit()

        if candidates and league == "1군":
            break

    return candidates


def get_player_basic_information(soup):
    result = {"name": "", "team": "", "position": ""}

    player_info = soup.find(
        "div",
        class_=lambda value: value is not None and "player_info" in value
    )

    if player_info is None:
        return result

    text = player_info.get_text(" ", strip=True)

    name_match = re.search(r"선수명\s*:\s*([^\s]+)", text)
    position_match = re.search(r"포지션\s*:\s*(.+?)(?=신장/체중|경력|입단|$)", text)

    if name_match:
        result["name"] = name_match.group(1).strip()
    if position_match:
        result["position"] = position_match.group(1).strip()

    for image in player_info.find_all("img", alt=True):
        alt = image.get("alt", "").strip()
        if alt and alt != result["name"]:
            result["team"] = alt
            break

    if result["team"] == "":
        h4_tag = player_info.find("h4")
        if h4_tag:
            result["team"] = h4_tag.get_text(" ", strip=True)

    return result


def find_current_season_tables(soup):
    season_heading = None

    for heading in soup.find_all(["h5", "h6"]):
        heading_text = heading.get_text(" ", strip=True)
        if re.fullmatch(r"\d{4}\s*성적", heading_text):
            season_heading = heading
            break

    if season_heading is None:
        return []

    tables = []
    current = season_heading.find_next_sibling()

    while current is not None:
        if current.name in ["h5", "h6"]:
            break
        if hasattr(current, "find_all"):
            if current.name == "table":
                tables.append(current)
            tables.extend(current.find_all("table"))
        current = current.find_next_sibling()

    unique_tables = []
    used_table_ids = set()
    for table in tables:
        table_id = id(table)
        if table_id not in used_table_ids:
            used_table_ids.add(table_id)
            unique_tables.append(table)

    return unique_tables


def table_to_record(table):
    thead = table.find("thead")
    tbody = table.find("tbody")

    if thead is None or tbody is None:
        return {}

    row = tbody.find("tr")
    if row is None:
        return {}

    row_text = row.get_text(" ", strip=True)
    if "기록이 없습니다" in row_text:
        return {}

    headers = [clean_header(tag.get_text(strip=True)) for tag in thead.find_all(["th", "td"])]
    values = [td.get_text(" ", strip=True) for td in row.find_all("td")]

    return dict(zip(headers, values))


def extract_current_season_record(soup):
    record = {}
    tables = find_current_season_tables(soup)

    for table in tables:
        table_record = table_to_record(table)
        for key, value in table_record.items():
            if key not in record or record[key] == "":
                record[key] = value

    return record


def open_player_detail(candidate):
    """상세페이지는 서버 렌더링이라 requests로 빠르게 처리한다."""

    position = candidate["position"]
    player_id = candidate["player_id"]
    league = candidate.get("league", "1군")

    player_type = "투수" if "투수" in position else "타자"
    detail_page = "PitcherDetail" if player_type == "투수" else "HitterDetail"

    if league == "2군":
        detail_url = f"{KBO_BASE_URL}/Futures/Player/{detail_page}.aspx?playerId={player_id}"
    else:
        detail_url = f"{KBO_BASE_URL}/Record/Player/{detail_page}/Basic.aspx?playerId={player_id}"

    r = requests.get(detail_url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    information = get_player_basic_information(soup)
    record = extract_current_season_record(soup)

    if not record:
        return None

    team = record.get("TEAM", "") or candidate["team"] or information["team"]
    detail_position = information["position"] or candidate["position"]

    if player_type == "타자":
        if record.get("AVG", "") == "" or record.get("G", "") == "":
            return None

        return {
            "type": "타자", "name": candidate["name"], "team": team,
            "position": f"{detail_position} ({league})",
            "average": record.get("AVG", ""), "games": record.get("G", ""),
            "plate_appearances": record.get("PA", ""), "at_bats": record.get("AB", ""),
            "runs": record.get("R", ""), "hits": record.get("H", ""),
            "homerun": record.get("HR", ""), "rbi": record.get("RBI", ""),
            "era": "", "wins": "", "losses": "", "saves": "", "holds": "",
            "innings": "", "walks": "", "strikeouts": "", "whip": "",
            "link": detail_url
        }

    if record.get("ERA", "") == "" or record.get("G", "") == "":
        return None

    return {
        "type": "투수", "name": candidate["name"], "team": team,
        "position": f"{detail_position} ({league})",
        "average": "", "plate_appearances": "", "at_bats": "", "runs": "", "rbi": "",
        "era": record.get("ERA", ""), "games": record.get("G", ""),
        "wins": record.get("W", ""), "losses": record.get("L", ""),
        "saves": record.get("SV", ""), "holds": record.get("HLD", ""),
        "innings": record.get("IP", ""), "hits": record.get("H", ""),
        "homerun": record.get("HR", ""), "walks": record.get("BB", ""),
        "strikeouts": record.get("SO", ""), "whip": record.get("WHIP", ""),
        "link": detail_url
    }


def search_kbo_player_record(keyword):
    candidates = find_player_candidates(keyword)

    for candidate in candidates:
        player = open_player_detail(candidate)
        if player is not None:
            return [player]

    return []


def search_baseball_news(keyword, limit=20):
    """다음 뉴스 검색은 정적 렌더링이라 requests로 충분하다."""

    news = []
    search_url = f"https://search.daum.net/search?w=news&q={quote(keyword + ' 야구')}"

    try:
        r = requests.get(search_url, headers=HEADERS, timeout=10)
    except requests.RequestException:
        return news

    soup = BeautifulSoup(r.text, "html.parser")

    title_tags = soup.select(
        "a.tit_main, a.f_link_b, a[data-tiara-layer='title'], "
        "a[data-tiara-action-name='제목'], strong.tit_thumb a"
    )

    if not title_tags:
        title_tags = soup.find_all("a", href=True)

    used_links = set()

    for tag in title_tags:
        title = tag.get_text(" ", strip=True)
        link = tag.get("href", "").strip()

        if title == "" or link == "" or keyword not in title:
            continue

        if link.startswith("//"):
            link = "https:" + link
        if not link.startswith("http"):
            link = urljoin("https://search.daum.net", link)

        if link in used_links:
            continue
        if any(b in link for b in ["search.daum.net/search?", "accounts.kakao.com", "cs.daum.net"]):
            continue

        used_links.add(link)
        parent = tag.find_parent(["li", "div", "article"])
        info = ""

        if parent is not None:
            info = parent.get_text(" ", strip=True)
            if info.startswith(title):
                info = info[len(title):].strip()

        news.append({"title": title, "info": info, "source": "다음 뉴스", "link": link})

        if len(news) >= limit:
            break

    return news