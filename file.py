import csv


def save_to_csv(players, news):
    with open(
        "./downloads.csv",
        "w",
        newline="",
        encoding="cp949",
        errors="replace"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "KBO 선수 시즌 기록"
        ])

        if not players:
            writer.writerow([
                "선수 기록을 찾지 못했습니다."
            ])

        for player in players:
            if player["type"] == "타자":
                writer.writerow([
                    "선수명",
                    "유형",
                    "팀",
                    "포지션",
                    "타율",
                    "경기",
                    "타석",
                    "타수",
                    "득점",
                    "안타",
                    "홈런",
                    "타점",
                    "상세보기"
                ])

                writer.writerow([
                    player["name"],
                    player["type"],
                    player["team"],
                    player["position"],
                    player["average"],
                    player["games"],
                    player["plate_appearances"],
                    player["at_bats"],
                    player["runs"],
                    player["hits"],
                    player["homerun"],
                    player["rbi"],
                    player["link"]
                ])

            else:
                writer.writerow([
                    "선수명",
                    "유형",
                    "팀",
                    "포지션",
                    "평균자책점",
                    "경기",
                    "승",
                    "패",
                    "세이브",
                    "홀드",
                    "이닝",
                    "피안타",
                    "피홈런",
                    "볼넷",
                    "탈삼진",
                    "WHIP",
                    "상세보기"
                ])

                writer.writerow([
                    player["name"],
                    player["type"],
                    player["team"],
                    player["position"],
                    player["era"],
                    player["games"],
                    player["wins"],
                    player["losses"],
                    player["saves"],
                    player["holds"],
                    player["innings"],
                    player["hits"],
                    player["homerun"],
                    player["walks"],
                    player["strikeouts"],
                    player["whip"],
                    player["link"]
                ])

        writer.writerow([])
        writer.writerow([
            "관련 야구 뉴스"
        ])

        writer.writerow([
            "No",
            "기사 제목",
            "기사 정보",
            "출처",
            "상세보기"
        ])

        for index, article in enumerate(
            news,
            start=1
        ):
            writer.writerow([
                index,
                article["title"],
                article["info"],
                article["source"],
                article["link"]
            ])