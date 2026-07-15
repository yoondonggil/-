from flask import (
    Flask,
    render_template,
    request,
    redirect,
    send_file
)

from scrapper import (
    search_kbo_player_record,
    search_baseball_news
)

from file import save_to_csv


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    if keyword == "":
        return redirect("/")

    players = search_kbo_player_record(keyword)
    news = search_baseball_news(keyword)

    count = len(players) + len(news)

    print("검색어:", keyword)
    print("선수 기록:", len(players))
    print("관련 뉴스:", len(news))

    return render_template(
        "search.html",
        keyword=keyword,
        players=players,
        news=news,
        count=count
    )


@app.route("/file")
def download_file():
    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    if keyword == "":
        return redirect("/")

    players = search_kbo_player_record(keyword)
    news = search_baseball_news(keyword)

    save_to_csv(
        players,
        news
    )

    return send_file(
        "./downloads.csv",
        as_attachment=True,
        download_name=f"{keyword}_KBO_검색결과.csv"
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )

import json

# ... 기존 import들 아래에 추가

def load_players_db():
    try:
        with open("players_db.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


@app.route("/players")
def players_list():
    all_players = load_players_db()

    # 필터링 옵션 (선택)
    player_type = request.args.get("type", "")  # "타자" or "투수"
    year = request.args.get("year", "")

    filtered = all_players
    if player_type:
        filtered = [p for p in filtered if p["type"] == player_type]
    if year:
        filtered = [p for p in filtered if str(p["year"]) == year]

    return render_template(
        "players.html",
        players=filtered,
        count=len(filtered),
        total=len(all_players)
    )