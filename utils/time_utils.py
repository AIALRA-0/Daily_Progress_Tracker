from datetime import datetime, time, timedelta
import re

# 匹配严格的 HH:MM-HH:MM 格式
time_pattern = re.compile(r"^\d{2}:\d{2}-\d{2}:\d{2}$")


def is_time_format_valid(time_range: str) -> bool:
    """
    @brief 判断时间段格式是否为严格的 HH:MM-HH:MM。

    @param time_range 时间字符串，如 "09:00-18:00"
    @return 格式符合返回 True，否则 False
    """
    return bool(time_pattern.fullmatch(time_range))


def auto_pad_time(time_range: str) -> str:
    """
    @brief 自动补全时间格式（如 9:5 -> 09:05）。

    @param time_range 宽松时间段，如 "9:5-18:0"
    @return 补全后的标准时间段，如 "09:05-18:00"
    @note 若格式解析失败，则原样返回。
    """
    try:
        parts = time_range.strip().split('-')
        if len(parts) != 2:
            return time_range

        def pad(t):
            h, m = map(int, t.split(':'))
            return f"{h:02d}:{m:02d}"

        start, end = parts
        return f"{pad(start)}-{pad(end)}"
    except Exception:
        return time_range


def validate_time_range(time_range: str) -> bool:
    """
    @brief 验证时间段格式及其合法性。

    @param time_range 输入的时间段字符串，可为非标准格式
    @return 若补全后符合 HH:MM-HH:MM 且起始时间早于结束时间，返回 True
    """
    time_range = auto_pad_time(time_range)
    if not is_time_format_valid(time_range):
        return False

    try:
        start, end = time_range.split('-')
        fmt = "%H:%M"
        start_time = datetime.strptime(start, fmt)
        end_time = datetime.strptime(end, fmt)
        return start_time < end_time
    except Exception:
        return False


def time_overlap(r1: str, r2: str) -> bool:
    """
    @brief 判断两个时间段是否有交集。

    @param r1 第一个时间段，如 "08:00-10:00"
    @param r2 第二个时间段，如 "09:30-11:00"

    @return 若时间段有交叉（允许首尾接触），返回 True；否则 False
    """
    def parse_range(r: str):
        r = auto_pad_time(r)
        start, end = r.split('-')
        fmt = "%H:%M"
        return datetime.strptime(start.strip(), fmt), datetime.strptime(end.strip(), fmt)

    try:
        s1, e1 = parse_range(r1)
        s2, e2 = parse_range(r2)
        return max(s1, s2) < min(e1, e2)
    except Exception:
        return False


def is_full_day_covered(tasks: list[dict]) -> bool:
    """
    @brief 判断任务是否完整覆盖整天（从 00:00 到 24:00）。

    @param tasks 任务列表，每个任务包含 "time" 字段，如 {"time": "08:00-10:00"}
    @return 若无空隙地覆盖 00:00~24:00，返回 True，否则 False
    """
    intervals = []
    for task in tasks:
        start_str, end_str = task["time"].split('-')
        # 将 24:00 转为 23:59 进行近似判断（避免跨天处理）
        if end_str == "24:00":
            end_str = "23:59"
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        intervals.append((start, end))

    # 按起始时间排序
    intervals.sort(key=lambda x: x[0])

    current = time(0, 0)
    for start, end in intervals:
        if start > current:
            return False
        if end > current:
            current = end

    return current >= time(23, 59)

def time_to_minutes(t: str) -> int:
    """
    @brief 将时间字符串转为分钟数。
    @param t 时间字符串，如 "08:30" 或 "24:00"
    @return 从 00:00 开始的分钟数
    """
    h, m = map(int, t.split(":"))
    return (0 if h == 24 else h) * 60 + m + (1440 if h == 24 else 0)


def str_to_datetime(base_date: datetime.date, t: str) -> datetime:
    """
    @brief 将字符串时间转为 datetime 对象。
    @param base_date 日期部分
    @param t 时间字符串，如 "24:00"
    @return 完整 datetime 对象
    """
    if t == "24:00":
        return datetime.combine(base_date + timedelta(days=1), datetime.min.time())
    return datetime.combine(base_date, datetime.strptime(t, "%H:%M").time())

