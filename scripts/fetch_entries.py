
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
