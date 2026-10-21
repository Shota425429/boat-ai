"""公式モーターボートファン手帳 (fanYYMM.lzh) からコース別成績を作成。"""
import json
import subprocess
from pathlib import Path

SOURCE = Path('data/fan2604.lzh')
DESTINATION = Path('data/racer_stats.json')


def read_field(record, offset, width):
    return record[offset:offset + width], offset + width


def parse_record(record):
    if len(record) != 416:
        raise ValueError(f'レコード長が416バイトではありません: {len(record)}')
    p = 0

    def take(width):
        nonlocal p
        value, p = read_field(record, p, width)
        return value

    number = take(4).decode('ascii')
    name = take(16).decode('cp932').replace('　', ' ').strip()
    take(15)  # カナ
    branch = take(4).decode('cp932').strip()
    grade = take(2).decode('ascii').strip()
    for width in (1, 6, 1, 2, 3, 2, 2):
        take(width)  # 年号、生年月日、性別、年齢、身長、体重、血液型
    win_rate = int(take(4)) / 100
    second_rate = int(take(4)) / 10
    for width in (3, 3, 3, 2, 2, 3):
        take(width)  # 1着、2着、出走、優出、優勝、平均ST

    summaries = []
    for _ in range(6):
        summaries.append({
            'starts': int(take(3)),
            'two_rate_official': int(take(4)) / 10,
            'avg_start': int(take(3)) / 100,
            'avg_start_rank': int(take(3)) / 100,
        })

    for width in (2, 2, 2, 4, 4, 4, 1):
        take(width)  # 過去級別、能力指数、年、期
    period_start = take(8).decode('ascii')
    period_end = take(8).decode('ascii')
    take(3)  # 養成期

    courses = {}
    for course in range(1, 7):
        finishes = [int(take(3)) for _ in range(6)]
        other = [int(take(2)) for _ in range(8)]
        starts = summaries[course - 1]['starts']
        if sum(finishes) > starts:
            raise ValueError(f'{number} {course}コース: 着順回数が進入回数を超過')
        first, second, third = finishes[:3]
        def percent(n):
            return round(100 * n / starts, 1) if starts else None
        courses[str(course)] = {
            'starts': starts,
            'first_count': first,
            'second_count': second,
            'third_count': third,
            'first_rate': percent(first),
            'two_rate': percent(first + second),
            'three_rate': percent(first + second + third),
            'official_two_rate': summaries[course - 1]['two_rate_official'],
        }

    take(8)  # コースなし事故回数
    take(6)  # 出身地
    if p != 416:
        raise ValueError(f'{number}: 解析位置が不正 ({p})')
    return number, {
        'name': name,
        'branch': branch,
        'grade': grade,
        'win_rate': win_rate,
        'national_two_rate': second_rate,
        'period_start': period_start,
        'period_end': period_end,
        'courses': courses,
    }


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f'{SOURCE} が見つかりません')
    result = subprocess.run(['lha', 'p', str(SOURCE)], check=True, capture_output=True)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError('圧縮ファイルからデータを取得できませんでした')
    racers = {}
    for line in lines:
        
        if len(line) != 416:
            continue
        number, data = parse_record(line)
        if number in racers:
            raise ValueError(f'登録番号が重複しています: {number}')
        racers[number] = data
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(json.dumps({
        'source': SOURCE.name,
        'period_start': next(iter(racers.values()))['period_start'],
        'period_end': next(iter(racers.values()))['period_end'],
        'racer_count': len(racers),
        'racers': racers,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'選手成績の保存完了: {len(racers)}人 → {DESTINATION}')
    print('例 2538:', json.dumps(racers.get('2538'), ensure_ascii=False)[:220])


if __name__ == '__main__':
    main()
