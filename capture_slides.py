import argparse
import ctypes
import json
import re
import time
from pathlib import Path
from typing import Dict, Tuple

import pyautogui
import tkinter as tk


BASE_DIR = Path(__file__).resolve().parent
CAPTURES_DIR = BASE_DIR / "captures"
REGION_FILE = BASE_DIR / "capture_region.json"
INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*]')


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return number


def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or greater")
    return number


def prompt_text(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("不能为空，请重新输入。")


def prompt_positive_int(label: str) -> int:
    while True:
        raw = input(label).strip()
        try:
            return positive_int(raw)
        except (ValueError, argparse.ArgumentTypeError):
            print("请输入大于 0 的整数。")


def prompt_non_negative_float(label: str) -> float:
    while True:
        raw = input(label).strip()
        try:
            return non_negative_float(raw)
        except (ValueError, argparse.ArgumentTypeError):
            print("请输入大于或等于 0 的数字。")


def prompt_yes_no(label: str) -> bool:
    while True:
        value = input(label).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("请输入 y 或 n。")


def sanitize_folder_name(name: str) -> str:
    cleaned = INVALID_WINDOWS_CHARS.sub("_", name).strip().rstrip(".")
    return cleaned or "未命名章节"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CMOS 课程课件自动截图工具")
    parser.add_argument("--chapter", help="章节编号，例如 2")
    parser.add_argument("--title", help='章节名称，例如 "Basic MOS Device Physics"')
    parser.add_argument("--pages", type=positive_int, help="PPT 总页数，例如 50")
    parser.add_argument("--interval", type=non_negative_float, help="翻页等待时间（秒），例如 0.2")
    parser.add_argument(
        "--select-region",
        action="store_true",
        help="重新手动框选 PPT 区域并覆盖已保存区域",
    )
    return parser.parse_args()


def load_region() -> Dict[str, int]:
    with REGION_FILE.open("r", encoding="utf-8") as file:
        region = json.load(file)

    required_keys = {"x1", "y1", "x2", "y2"}
    if not required_keys.issubset(region):
        raise ValueError("区域配置文件缺少必要坐标。")

    x1, y1, x2, y2 = (int(region[key]) for key in ("x1", "y1", "x2", "y2"))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("区域配置文件中的坐标无效。")

    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def save_region(region: Dict[str, int]) -> None:
    with REGION_FILE.open("w", encoding="utf-8") as file:
        json.dump(region, file, ensure_ascii=False, indent=2)


def minimize_console_window() -> None:
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)
    except AttributeError:
        pass


def restore_console_window() -> None:
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except AttributeError:
        pass


def select_region() -> Dict[str, int]:
    print("进入框选模式：请先点击 PPT 区域左上角，再点击右下角。")

    points = []
    root = tk.Tk()
    root.title("选择 PPT 区域")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.25)
    root.configure(bg="black")
    root.config(cursor="crosshair")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    rectangle_id = None

    def on_click(event: tk.Event) -> None:
        nonlocal rectangle_id
        points.append((event.x_root, event.y_root))
        if len(points) == 1:
            x, y = points[0]
            rectangle_id = canvas.create_rectangle(
                x,
                y,
                x,
                y,
                outline="red",
                width=3,
            )
        elif len(points) == 2:
            root.after(100, root.destroy)

    def on_move(event: tk.Event) -> None:
        if len(points) == 1 and rectangle_id is not None:
            x1, y1 = points[0]
            canvas.coords(rectangle_id, x1, y1, event.x_root, event.y_root)

    root.bind("<Button-1>", on_click)
    root.bind("<Motion>", on_move)
    root.mainloop()

    if len(points) != 2:
        raise RuntimeError("未完成区域选择。")

    (raw_x1, raw_y1), (raw_x2, raw_y2) = points
    x1, x2 = sorted((raw_x1, raw_x2))
    y1, y2 = sorted((raw_y1, raw_y2))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("框选区域无效，请重新运行后再选。")

    region = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    save_region(region)
    print(f"已记录区域：x1={x1}, y1={y1}, x2={x2}, y2={y2}")
    return region


def get_region(should_select_region: bool) -> Dict[str, int]:
    if should_select_region or not REGION_FILE.exists():
        if not REGION_FILE.exists() and not should_select_region:
            print("未找到已保存区域，将进入框选模式。")
        return select_region()

    try:
        region = load_region()
        print(
            "使用已保存区域："
            f"x1={region['x1']}, y1={region['y1']}, "
            f"x2={region['x2']}, y2={region['y2']}"
        )
        return region
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"已保存区域不可用：{error}")
        print("程序会先最小化 PowerShell，然后重新进入框选模式。")
        minimize_console_window()
        time.sleep(1)
        return select_region()


def region_to_box(region: Dict[str, int]) -> Tuple[int, int, int, int]:
    width = region["x2"] - region["x1"]
    height = region["y2"] - region["y1"]
    return region["x1"], region["y1"], width, height


def countdown_before_capture(seconds: int = 5) -> None:
    print("请在 5 秒内切换到课件窗口，程序将自动开始截图。")
    for remaining in range(seconds, 0, -1):
        print(remaining, flush=True)
        time.sleep(1)


def capture_slides(
    output_dir: Path,
    pages: int,
    interval: float,
    region: Dict[str, int],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_box = region_to_box(region)

    for page in range(1, pages + 1):
        filename = f"{page:03d}.png"
        filepath = output_dir / filename
        screenshot = pyautogui.screenshot(region=screenshot_box)
        screenshot.save(filepath)
        print(f"[{page}/{pages}] saved {filename}")

        if page == pages:
            break

        time.sleep(interval)
        pyautogui.press("right")
        time.sleep(interval)


def main() -> int:
    args = parse_args()

    chapter = args.chapter or prompt_text("请输入章节编号：")
    title = args.title or prompt_text("请输入章节名称：")
    pages = args.pages if args.pages is not None else prompt_positive_int("请输入PPT总页数：")
    interval = (
        args.interval
        if args.interval is not None
        else prompt_non_negative_float("请输入翻页等待时间（秒）：")
    )
    should_select_region = (
        True if args.select_region else prompt_yes_no("是否框选区域？(y/n)：")
    )

    safe_chapter = sanitize_folder_name(str(chapter))
    safe_title = sanitize_folder_name(title)
    output_dir = CAPTURES_DIR / f"第{safe_chapter}章{safe_title}"

    if should_select_region or not REGION_FILE.exists():
        print("准备进入框选模式。请先确保课件已经打开并停留在第一页。")
        print("程序会先最小化 PowerShell，然后请点击 PPT 区域左上角和右下角。")
        input("准备好后按回车")
        minimize_console_window()
        time.sleep(1)

    region = get_region(should_select_region)

    restore_console_window()
    print(f"截图将保存到：{output_dir}")
    countdown_before_capture()
    minimize_console_window()
    print("开始截图。")
    capture_slides(output_dir, pages, interval, region)
    print("全部截图完成。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已中止。")
        raise SystemExit(130)
