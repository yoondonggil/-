from scrapper import create_driver, ROW_SELECTOR, SOURCES
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time

keyword = "나승엽"
list_url = SOURCES[0][0]  # 1군 타자 URL
print("URL:", list_url)

driver = create_driver()
driver.get(list_url)
time.sleep(1.5)

page_num = 1
all_names = []

while page_num <= 15:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select(ROW_SELECTOR)
    print(f"\n--- {page_num}페이지, 행 개수: {len(rows)} ---")

    if not rows:
        print("행이 없음. 중단.")
        break

    names_here = [row.find("a").get_text(strip=True) for row in rows if row.find("a")]
    print("이 페이지 이름들:", names_here)
    all_names.extend(names_here)

    if keyword in names_here:
        print(f"\n★★★ {page_num}페이지에서 '{keyword}' 발견! ★★★")
        break

    moved = False
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, f"a[id*='btnNo{page_num + 1}']")
        print(f"btnNo{page_num + 1} 버튼 찾음, 클릭")
        next_btn.click()
        time.sleep(1.2)
        page_num += 1
        moved = True
    except NoSuchElementException:
        print(f"btnNo{page_num + 1} 버튼 없음")

    if not moved:
        try:
            next_group = driver.find_element(By.CSS_SELECTOR, "a[id*='btnNext']")
            print("btnNext 버튼 찾음, 클릭")
            next_group.click()
            time.sleep(1.2)
            page_num += 1
            moved = True
        except NoSuchElementException:
            print("btnNext 버튼도 없음")

    if not moved:
        print("더 이상 이동 불가. 중단.")
        break

driver.quit()

print(f"\n=== 총 {page_num}페이지, {len(all_names)}명 수집 ===")
print(f"'{keyword}' 목록에 있는지: {keyword in all_names}")