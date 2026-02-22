#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NaniNovel 脚本 → AI 配音清单 (CSV)

从 .nani 文件中提取需要配音的角色对话，输出为 CSV 格式：
说话人, 文件名, 中文, 日语

规则：
- 仅提取 15 个需要配音的角色（13 个有魔女化 + 典狱长 + 月代雪）
- 魔女化角色在说话人中注明为 "XXX(魔女化)"
- 旁白不配音，不提取
- 文本清洗：移除 <br>、[i]、[/i] 等 NaniNovel 标记

用法（在项目根目录执行）：
    python tools/nani_to_voice_list.py <nani文件路径> [输出CSV路径]

示例：
    python tools/nani_to_voice_list.py Hewkick_complement1_3/Scripts/Hewkick_complement1_3/Main.nani
"""

import csv
import re
import sys
from pathlib import Path

# 15 个需要配音的角色（脚本中的角色 ID）
# 13 个有魔女化 + Warden + Yuki
VOICE_CHARACTERS = {
    "Alisa", "CreatureAlisa",
    "AnAn", "CreatureAnAn",
    "Coco", "CreatureCoco",
    "Ema", "CreatureEma",
    "Hanna", "CreatureHanna",
    "Hiro", "CreatureHiro",
    "Leia", "CreatureLeia",
    "Margo", "CreatureMargo",
    "Meruru", "CreatureMeruru",
    "Miria", "CreatureMiria",
    "Nanoka", "CreatureNanoka",
    "Noah", "CreatureNoah",
    "Sherry", "CreatureSherry",
    "Warden",
    "Yuki",
}

# CreatureX → 基础名，用于生成 "XXX(魔女化)"
CREATURE_TO_BASE = {
    "CreatureAlisa": "Alisa",
    "CreatureAnAn": "AnAn",
    "CreatureCoco": "Coco",
    "CreatureEma": "Ema",
    "CreatureHanna": "Hanna",
    "CreatureHiro": "Hiro",
    "CreatureLeia": "Leia",
    "CreatureMargo": "Margo",
    "CreatureMeruru": "Meruru",
    "CreatureMiria": "Miria",
    "CreatureNanoka": "Nanoka",
    "CreatureNoah": "Noah",
    "CreatureSherry": "Sherry",
}


def clean_text(text: str) -> str:
    """移除 NaniNovel 标记，保留纯文本"""
    # <br> → 空格
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # [i]...[/i] 等标签，只保留内容
    text = re.sub(r"\[/?i\]", "", text, flags=re.IGNORECASE)
    # 其他 [xxx] 标签暂时保留内容（如有需要可扩展）
    text = text.strip()
    return text


def format_speaker(char_id: str) -> str:
    """将角色 ID 转为配音清单中的说话人标注"""
    if char_id in CREATURE_TO_BASE:
        return f"{CREATURE_TO_BASE[char_id]}(魔女化)"
    return char_id


def parse_nani(nani_path: Path) -> list[tuple[str, str]]:
    """
    解析 .nani 文件，提取需要配音的对话。
    返回 [(说话人, 中文台词), ...]
    """
    results = []
    # 角色对话行：CharacterName: 台词
    # 角色名以字母开头，可含字母数字（如 Hanna, CreatureHanna, AnAn）
    pattern = re.compile(r"^([A-Za-z][A-Za-z0-9]*):\s*(.+)$")

    with open(nani_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n\r")
            m = pattern.match(line.strip())
            if not m:
                continue
            char_id, text = m.groups()
            if char_id not in VOICE_CHARACTERS:
                continue
            text = clean_text(text)
            if not text:
                continue
            speaker = format_speaker(char_id)
            results.append((speaker, text))

    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n示例：")
        print('  python nani_to_voice_list.py Hewkick_complement1_3/Scripts/Hewkick_complement1_3/Main.nani')
        sys.exit(1)

    nani_path = Path(sys.argv[1])
    if not nani_path.exists():
        print(f"错误：文件不存在 - {nani_path}")
        sys.exit(1)

    if nani_path.suffix.lower() != ".nani":
        print("警告：文件扩展名不是 .nani")

    # 输出路径：默认与 nani 同目录，同名 .csv
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        script_name = nani_path.stem
        out_path = nani_path.parent / f"{script_name}_voice_list.csv"

    dialogues = parse_nani(nani_path)
    print(f"从 {nani_path.name} 提取了 {len(dialogues)} 条对话")

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["说话人", "文件名", "中文", "日语"])
        base_name = nani_path.stem
        for i, (speaker, text) in enumerate(dialogues, start=1):
            filename = f"{base_name}_{i:03d}"
            writer.writerow([speaker, filename, text, ""])

    print(f"已输出到 {out_path}")


if __name__ == "__main__":
    main()