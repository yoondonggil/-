import json
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapper import create_driver  # 기존 scrapper.py의 driver 생성 함수 재사용


YEAR_SELECT_ID = "cphContents_cphContents_cphContents_ddlSeason_ddlSeason"
ROW_SELECTOR = "div.record_result table.tData01 tbody tr"

BATTER_URL = "https://www.koreabaseball.com/Record/Player/HitterBasic/BasicOld.aspx"
PITCHER_URL = "https://www.koreabaseball.com/Record/Player/PitcherBasic/BasicOld.aspx"

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]


def wait_for_table(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ROW_SELECTOR))
    )


def collect_table(driver, url, year, player_type):
    driver.get(url)
    wait_for_table(driver)

    # 연도 드롭다운이 이미 원하는 연도가 아니면 변경
    year_select = Select(driver.find_element(By.ID, YEAR_SELECT_ID))
    if year_select.first_selected_option.text.strip() != str(year):
        year_select.select_by_visible_text(str(year))
        time.sleep(1.5)
        wait_for_table(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select(ROW_SELECTOR)

    results = []
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 4:
            continue

        try:
            if player_type == "타자":
                results.append({
                    "year": year,
                    "type": "타자",
                    "rank": tds[0].get_text(strip=True),
                    "name": tds[1].get_text(strip=True),
                    "team": tds[2].get_text(strip=True),
                    "average": tds[3].get_text(strip=True),
                })
            else:
                results.append({
                    "year": year,
                    "type": "투수",
                    "rank": tds[0].get_text(strip=True),
                    "name": tds[1].get_text(strip=True),
                    "team": tds[2].get_text(strip=True),
                    "era": tds[3].get_text(strip=True),
                })
        except IndexError:
            continue

    return results


def collect_all(target_count=300):
    driver = create_driver()
    all_data = []

    try:
        for year in YEARS:
            batters = collect_table(driver, BATTER_URL, year, "타자")
            all_data.extend(batters)
            print(f"{year}년 타자: {len(batters)}명 (누적 {len(all_data)}개)")

            if len(all_data) >= target_count:
                break

            pitchers = collect_table(driver, PITCHER_URL, year, "투수")
            all_data.extend(pitchers)
            print(f"{year}년 투수: {len(pitchers)}명 (누적 {len(all_data)}개)")

            if len(all_data) >= target_count:
                break

    finally:
        driver.quit()

    return all_data[:target_count]


if __name__ == "__main__":
    data = collect_all(target_count=300)

    with open("players_db.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(data)}개 데이터를 players_db.json에 저장했습니다.")