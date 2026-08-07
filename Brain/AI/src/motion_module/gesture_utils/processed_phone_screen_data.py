import re
import subprocess


def extract_phone_screen_info() -> tuple[
    tuple[float, float, float], tuple[float, float, float]
]:
    """
    Parses the output of `adb shell dumpsys input` to compare raw and logical touch input dimensions.

    Returns: a tuple of (raw_x, logical_x, ratio_x) and (raw_y, logical_y, ratio_y).
    Returns: a tuple of (raw_x, logical_x, ratio_x) and (raw_y, logical_y, ratio_y).
    """
    data = subprocess.check_output(["adb", "shell", "dumpsys", "input"]).decode()

    logical_x = re.search(r"X:.*?max=([\d.]+)", data)
    logical_y = re.search(r"Y:.*?max=([\d.]+)", data)

    raw_x = re.search(r"Touch Input Mapper.*?X:.*?max=(\d+)", data, re.DOTALL)
    raw_y = re.search(r"Touch Input Mapper.*?Y:.*?max=(\d+)", data, re.DOTALL)

    assert logical_x and logical_y and raw_x and raw_y, (
        "Error: Could not find all X/Y pairs in the input."
    )

    lx, ly = (
        round(float(logical_x.group(1)) + 0.01),
        round(float(logical_y.group(1)) + 0.01),
    )
    rx, ry = int(raw_x.group(1)), int(raw_y.group(1))

    return (rx, lx, round(rx / lx, 2)), (ry, ly, round(ry / ly, 2))


if __name__ == "__main__":
    print(f"{'Axis':<10} | {'Raw':<10} | {'Pixel':<15} | {'Ratio'}")
    print("-" * 55)
    for axis, (raw, logical, ratio) in zip(["X", "Y"], extract_phone_screen_info()):
        print(f"{axis:<10} | {raw:<10} | {logical:<15} | {ratio}x")
