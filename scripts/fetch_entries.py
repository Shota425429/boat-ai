
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from boatrace_lzh import LzhDownloader, ScheduleParser

JST = timezone(timedelta(hours=9))
today = datetime.now(JST).date()

# 公式番組表をダウンロード・解凍
downloader = LzhDownloader(cache_dir="./cache")
files = downloader.download(today, "schedule")

# ダウンロードしたファイルを確認
print("取得ファイル数:", len(files))

for file in files:
    print("取得ファイル:", file)


if not files:
    raise RuntimeError("本日の番組表を取得できませんでした")

# 番組表を解析
parser = ScheduleParser()
result = parser.parse(files)

if not result.races:
    raise RuntimeError("番組表にレース情報がありません")

# 取得状況をJSONで保存
output = {
    "date": today.isoformat(),
    "updated_at": datetime.now(JST).isoformat(),
    "race_count": len(result.races),
    "racer_count": len(result.racers),
    "entry_count": len(result.entries),
    "status": "ok"
}

Path("data").mkdir(exist_ok=True)
Path("data/schedule_status.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("番組表の取得・解析に成功しました")
print(json.dumps(output, ensure_ascii=False, indent=2))


# 取得データの構造を調査
from dataclasses import asdict, is_dataclass

def inspect_record(record):
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    if hasattr(record, "model_dump"):
        return record.model_dump(mode="json")
    if isinstance(record, dict):
        return record
    if hasattr(record, "__dict__"):
        return vars(record)
    return str(record)

debug_data = {
    "date": today.isoformat(),
    "sample_race": inspect_record(result.races[0]),
    "sample_racer": inspect_record(result.racers[0]),
    "sample_entry": inspect_record(result.entries[0]),
}

Path("data/debug_structure.json").write_text(
    json.dumps(debug_data, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8"
)

print("データ構造の確認用ファイルを保存しました")


# レース別の出走表データを作成
racer_map = {
    racer.racer_number: racer
    for racer in result.racers
}

race_list = []

for race in result.races:
    entries = []

    for entry in result.entries:
        if (
            entry.venue_code == race.venue_code
            and entry.race_date == race.race_date
            and entry.race_number == race.race_number
        ):
            racer = racer_map.get(entry.racer_number)

            entries.append({
                "boat_number": entry.boat_number,
                "racer_number": entry.racer_number,
                "name": racer.name if racer else None,
                "racer_class": racer.racer_class if racer else None,
                "branch": racer.branch if racer else None,
                "motor_number": entry.motor_number,
            })

    entries.sort(key=lambda x: x["boat_number"])

    race_list.append({
        "venue_code": race.venue_code,
        "race_date": str(race.race_date),
        "race_number": race.race_number,
        "distance": race.distance,
        "entries": entries,
    })

output_file = Path("data/races.json")
output_file.write_text(
    json.dumps(
        race_list,
        ensure_ascii=False,
        indent=2,
        default=str
    ),
    encoding="utf-8"
)

print(f"出走表データを保存しました：{len(race_list)}レース")


# ダウンロード機能の調査
import inspect

print("=== LzhDownloader の機能一覧 ===")

for name, member in inspect.getmembers(
    LzhDownloader, predicate=callable
):
    if not name.startswith("_"):
        try:
            signature = inspect.signature(member)
            print(f"{name}{signature}")
        except (TypeError, ValueError):
            print(name)

print("=== download の説明 ===")
print(inspect.getdoc(LzhDownloader.download))


# 番組表ファイルの内容を調査
print("=== 番組表ファイル調査 ===")

for filename, content in files.items():
    print("ファイル名:", filename)
    print("文字数:", len(content))
    print("行数:", len(content.splitlines()))
    print("先頭20行:")

    for line in content.splitlines()[:20]:
        print(repr(line[:150]))

print("=== 解析された会場 ===")
venue_codes = sorted({
    race.venue_code for race in result.races
})
print("会場コード:", venue_codes)
print("会場数:", len(venue_codes))


# 番組表ファイルの末尾を確認
print("=== 番組表ファイル末尾調査 ===")

for filename, content in files.items():
    print("ファイル名:", filename)
    print("末尾30行:")

    
# ファイル全体に含まれる開催場を調査
print("=== 開催場の一覧調査 ===")

for filename, content in files.items():
    print("ファイル名:", filename)

    for line_number, line in enumerate(
        content.splitlines(), start=1
    ):
        if "ボートレース" in line or "競艇場" in line:
            print(
                f"{line_number}行目:",
                repr(line[:120])
            )

    for line in content.splitlines()[-30:]:
        print(repr(line[:150]))


# ScheduleParser の解析機能を調査
print("=== ScheduleParser の機能一覧 ===")

for name, member in inspect.getmembers(
    ScheduleParser, predicate=callable
):
    if not name.startswith("_"):
        try:
            signature = inspect.signature(member)
            print(f"{name}{signature}")
        except (TypeError, ValueError):
            print(name)

print("=== parse の説明 ===")
print(inspect.getdoc(ScheduleParser.parse))


# ScheduleParser.parse の内部コードを調査
print("=== ScheduleParser.parse の内部コード ===")

try:
    print(inspect.getsource(ScheduleParser.parse))
except Exception as e:
    print("内部コードを取得できませんでした:", e)


# _parse_single_file の内部コードを調査
print("=== _parse_single_file の内部コード ===")

try:
    print(inspect.getsource(ScheduleParser._parse_single_file))
except Exception as e:
    print("内部コードを取得できませんでした:", e)
