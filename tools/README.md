# tools 工具目录

## nani_to_voice_list.py

从 NaniNovel 脚本 (`.nani`) 中提取需要配音的角色对话，输出 CSV 格式的配音清单。

### 用法

在**项目根目录**执行：

```bash
# 基本用法（输出与 nani 同目录）
python tools/nani_to_voice_list.py <nani文件路径>

# 指定输出 CSV 路径
python tools/nani_to_voice_list.py <nani文件路径> [输出CSV路径]
```

### 示例

```bash
python tools/nani_to_voice_list.py Hewkick_complement1_3/Scripts/Hewkick_complement1_3/Main.nani
```

输出：`Hewkick_complement1_3/Scripts/Hewkick_complement1_3/Main_voice_list.csv`

### 输出格式

| 说话人 | 文件名 | 中文 | 日语 |
|--------|--------|------|------|
| Hanna | Main_001 | 你一定能做到的吧，完美犯罪。 | |
| Sherry | Main_002 | 汉娜在质疑我吗？... | |

- 日语列留空，供后续翻译或 AI 配音使用
- 仅提取 15 个需要配音的角色（13 个有魔女化 + 典狱长 + 月代雪）
- 旁白不提取

### 相关规则

详见 [.cursor/rules/07_voice.mdc](../.cursor/rules/07_voice.mdc)
