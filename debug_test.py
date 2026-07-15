from scrapper import iter_all_pages, SOURCES, ROW_SELECTOR

keyword = "한동희"

list_url = SOURCES[0][0]  # 1군 타자 URL
print("URL:", list_url)

page_count = 0
all_names = []

for soup in iter_all_pages(list_url):
    page_count += 1
    rows = soup.select(ROW_SELECTOR)
    names_here = [row.find("a").get_text(strip=True) for row in rows if row.find("a")]
    print(f"--- {page_count}페이지, {len(names_here)}명 ---")
    print(names_here)
    all_names.extend(names_here)

    if keyword in names_here:
        print(f"\n★★★ {page_count}페이지에서 '{keyword}' 발견 ★★★")

    if page_count >= 20:
        break

print(f"\n=== 총 {page_count}페이지, {len(all_names)}명 수집 ===")
print(f"'{keyword}' 목록에 있는지: {keyword in all_names}")