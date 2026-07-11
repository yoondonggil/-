import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}


def search_incruit(keyword, page=1):
    jobs = []
    for i in range(page):
        startno = 30 * i
        url = f"https://search.incruit.com/list/search.asp?col=job&kw={keyword}&startno={startno}"
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        lis = soup.find_all("li", class_="c_col")

        for li in lis:
            try:
                company = li.find("a", class_="cpname").text.strip()
                title = (
                    li.find("div", class_="cell_mid")
                    .find("div", class_="cl_top")
                    .find("a")
                    .text.strip()
                )
                location = (
                    li.find("div", class_="cl_md")
                    .find_all("span")[0]
                    .text.strip()
                )
                link = (
                    li.find("div", class_="cell_mid")
                    .find("div", class_="cl_top")
                    .find("a")
                    .get("href")
                )

                jobs.append({
                    "company": company,
                    "title": title,
                    "location": location,
                    "link": link
                })
            except AttributeError:
                continue

        time.sleep(0.5)

    return jobs


def search_work24(keyword):
    url = f"https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do?searchMode=Y&srcKeyword={keyword}&pageIndex=1&resultCnt=60"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    trs = soup.select("tr:has(a.cp_name)")

    jobs = []
    for tr in trs:
        try:
            company = tr.find("a", class_="cp_name").text.strip()
            title = tr.find("a", class_="t3_sb").text.strip()
            location = tr.find("li", class_="site").find("p").text.strip()
            link = "https://www.work24.go.kr" + tr.find("a", class_="t3_sb").get("href")

            jobs.append({
                "company": company,
                "title": title,
                "location": location,
                "link": link
            })
        except AttributeError:
            continue

    return jobs