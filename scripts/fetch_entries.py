
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

from boatrace_lzh import LzhDownloader, ScheduleParser

JST = timezone(timedelta(hours=9))
today = datetime.now(JST).date()

# 公式番組表をダウンロード・解凍
downloader = LzhDownloader(cache_dir="./cache")
files = downloader.download(today, "schedule")

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
