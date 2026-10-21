"""公式Bファイルから当日開催の全会場の出走表を取得する。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from boatrace_lzh import LzhDownloader, ScheduleParser

JST = timezone(timedelta(hours=9))
VENUE_CODES = {
    "桐生": "01", "戸田": "02", "江戸川": "03", "平和島": "04",
    "多摩川": "05", "浜名湖": "06", "蒲郡": "07", "常滑": "08",
    "津": "09", "三国": "10", "びわこ": "11", "住之江": "12",
    "尼崎": "13", "鳴門": "14", "丸亀": "15", "児島": "16",
    "宮島": "17", "徳山": "18", "下関": "19", "若松": "20",
    "芦屋": "21", "福岡": "22", "唐津": "23", "大村": "24",
}


def venue_from_header(header):
    normalized = header.replace("\u3000", "").replace(" ", "")
    for name, code in VENUE_CODES.items():
        if normalized.startswith("ボートレース" + name):
            return name, code
    raise ValueError(f"会場名を判定できません: {header}")


def split_venues(files):
    """Bファイルの会場見出しで区切り、解析用の独立したテキストにする。"""
    venues = []
    for filename, content in files.items():
        lines = content.splitlines()
        starts = [i for i, line in enumerate(lines)
                  if line.startswith("ボートレース")]
        if not starts:
            raise RuntimeError(f"会場見出しが見つかりません: {filename}")
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(lines)
            block = lines[start:end]
            name, code = venue_from_header(block[0])
            venues.append((name, code, "\n".join(block)))
    return venues


def main():
    today = datetime.now(JST).date()
    files = LzhDownloader(cache_dir="./cache").download(today, "schedule")
    if not files:
        raise RuntimeError("本日の番組表を取得できませんでした")

    venues = split_venues(files)
    print(f"開催場数: {len(venues)}")

    all_races = []
    all_entries = []
    all_racers = []
    seen_codes = set()

    for index, (name, code, content) in enumerate(venues, start=1):
        if code in seen_codes:
            raise RuntimeError(f"同じ会場が重複しています: {name} ({code})")
        seen_codes.add(code)

        parsed = ScheduleParser().parse({f"venue_{index}.TXT": content})
        if len(parsed.races) != 12:
            raise RuntimeError(f"{name} の解析レース数が12ではありません: {len(parsed.races)}")
        if len(parsed.entries) != 72:
            raise RuntimeError(f"{name} の出走データ数が72ではありません: {len(parsed.entries)}")

        # ライブラリの会場名判定が誤るケースを補正する。
        for race in parsed.races:
            race.venue_code = code
        for entry in parsed.entries:
            entry.venue_code = code

        all_races.extend(parsed.races)
        all_entries.extend(parsed.entries)
        all_racers.extend(parsed.racers)
        print(f"{name} ({code}): {len(parsed.races)}R / {len(parsed.entries)}艇")

    # 選手番号から氏名・級別・支部を参照する。
    racer_map = {racer.racer_number: racer for racer in all_racers}
    entries_by_race = {}
    for entry in all_entries:
        key = (entry.venue_code, str(entry.race_date), entry.race_number)
        entries_by_race.setdefault(key, []).append(entry)

    race_list = []
    for race in all_races:
        key = (race.venue_code, str(race.race_date), race.race_number)
        entries = []
        for entry in entries_by_race.get(key, []):
            racer = racer_map.get(entry.racer_number)
            entries.append({
                "boat_number": entry.boat_number,
                "racer_number": entry.racer_number,
                "name": racer.name if racer else None,
                "racer_class": racer.racer_class if racer else None,
                "branch": racer.branch if racer else None,
                "motor_number": entry.motor_number,
            })
        entries.sort(key=lambda item: item["boat_number"])
        if len(entries) != 6:
            raise RuntimeError(f"出走数が6艇ではありません: {key} / {len(entries)}艇")
        race_list.append({
            "venue_code": race.venue_code,
            "race_date": str(race.race_date),
            "race_number": race.race_number,
            "distance": race.distance,
            "entries": entries,
        })

    race_list.sort(key=lambda item: (item["venue_code"], item["race_number"]))
    status = {
        "date": today.isoformat(),
        "updated_at": datetime.now(JST).isoformat(),
        "venue_count": len(venues),
        "race_count": len(race_list),
        "racer_count": len(all_racers),
        "entry_count": len(all_entries),
        "status": "ok",
    }

    Path("data").mkdir(exist_ok=True)
    Path("data/races.json").write_text(
        json.dumps(race_list, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    Path("data/schedule_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("=== 全国解析の合計 ===")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    print("出走表データを保存しました:", len(race_list), "レース")


if __name__ == "__main__":
    main()
