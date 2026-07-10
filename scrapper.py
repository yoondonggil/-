import requests
from bs4 import BeautifulSoup

def search_incruit(keyword,page=5):
    jobs=[]

    for i in range(page):
        page=30*i
        url=f"https://search.incruit.com/list/search.asp?col=job&kw={keyword}&startno={page}"
        r = requests.get(url)
        #print(r.text)
        soup=BeautifulSoup(r.text,"html.parser")
        lis= soup.find_all("li",class_="c_col")
       

        for li in lis:
            company=li.find("a",class_="cpname").text
            title=li.find("div",class_="cell_mid").find("div",class_="cl_top").find("a").text
            location=li.find("div",class_="cl_md").find_all("span")[0].text
            link=li.find("div",class_="cell_mid").find("div",class_="cl_top").find("a").get("href")
        
            job_data={
            "company":company,
            "title":title,
            "location":location,
            "link":link
        }

            jobs.append(job_data)


    return jobs

def search_hrd24(keyword):
    url=("https://www.work24.go.kr/cm/f/c/0100/selectUnifySearch.do"
        f"?topQuerySearchArea=tb_workinfo&topQueryData={keyword}"
    )
    r = requests.get(url)
    soup=BeautifulSoup(r.text,"html.parser")
    lis=soup.find()

    


    

        

        

