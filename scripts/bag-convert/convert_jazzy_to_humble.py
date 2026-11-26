#!/usr/bin/env python3
"""将 Jazzy 录制的 mcap bag 转换为 Humble 兼容格式"""

import re
import sys
from pathlib import Path


def convert_bag(bag_path: Path) -> None:
    metadata = bag_path / "metadata.yaml"
    if not metadata.exists():
        print(f"错误: 找不到 {metadata}")
        sys.exit(1)

    backup = metadata.with_suffix(".yaml.bak")
    backup.write_text(metadata.read_text())

    content = metadata.read_text()

    # Humble 的 rosbag2 支持 metadata version <= 5，实测 version 5 可正常读取。
    # 原脚本改成 6，但 Humble 实测仍可能解析失败，这里统一降到 5。
    content = re.sub(r"^(\s+)version: \d+$", r"\1version: 5", content, flags=re.MULTILINE)

    # 逐行处理 offered_qos_profiles 和 type_description_hash
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "offered_qos_profiles:" in line:
            indent = len(line) - len(line.lstrip())
            result.append(" " * indent + 'offered_qos_profiles: ""')
            i += 1
            while i < len(lines):
                next_indent = len(lines[i]) - len(lines[i].lstrip())
                if next_indent > indent and lines[i].strip():
                    i += 1
                else:
                    break
        elif "type_description_hash:" in line:
            i += 1
        else:
            result.append(line)
            i += 1
    content = "\n".join(result)

    content = re.sub(r"history: unknown", "history: 0", content)

    metadata.write_text(content)
    print(f"已转换: {bag_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <bag_path> [bag_path2 ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        convert_bag(Path(arg))
