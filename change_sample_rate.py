"""
音频批量转换工具
将目录下所有 wav / ogg / mp3 转换为：双声道 · 44100 Hz · 16-bit PCM WAV
支持重复运行（幂等）：已满足目标格式的文件会被跳过
"""

import os
import struct
import numpy as np
import soundfile as sf
import soxr

# ───────── 配置 ─────────────────────────────────────────────────────────────
INPUT_DIR   = r"Hewkick_complement1_5\Voice"
TARGET_SR   = 44100   # 目标采样率
TARGET_CH   = 2       # 目标声道（2 = 立体声）

# GPT-SoVITS 等工具常见 bug：WAV 头声称 WRONG_HDR_SR，但 PCM 数据实际是 ACTUAL_SR
WRONG_HDR_SR = 48000
ACTUAL_SR    = 24000
# ────────────────────────────────────────────────────────────────────────────


def _wav_header_sr(path: str) -> int:
    """只读 WAV 头部的采样率字段，不解码音频数据。"""
    with open(path, "rb") as f:
        f.seek(24)
        return struct.unpack_from("<I", f.read(4))[0]


def _to_stereo(y: np.ndarray) -> np.ndarray:
    """将任意声道数的音频统一转为 (N, 2) 立体声。"""
    if y.ndim == 1:
        return np.stack([y, y], axis=1)          # 单声道 → 复制双声道
    if y.shape[1] == 1:
        return np.concatenate([y, y], axis=1)    # (N,1) → (N,2)
    if y.shape[1] > 2:
        return y[:, :2]                          # 多声道 → 取前两轨
    return y                                     # 已是 (N,2)，原样返回


def _read(path: str):
    """
    读取音频，返回 (y: float32 ndarray, sr: int)。
    - WAV/OGG/FLAC/AIFF：用 soundfile 读取，自动修正错误的 WAV 头
    - MP3：用 librosa 读取（需要 audioread / ffmpeg）
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in (".wav", ".ogg", ".flac", ".aiff", ".aif"):
        y, sr = sf.read(path, dtype="float32", always_2d=True)
        # 修正 WAV 头写错的情况
        if ext == ".wav":
            hdr_sr = _wav_header_sr(path)
            if hdr_sr == WRONG_HDR_SR:
                print(f"    ⚠ WAV 头标称 {WRONG_HDR_SR} Hz，按实际 {ACTUAL_SR} Hz 处理")
                sr = ACTUAL_SR
        return y, sr

    if ext == ".mp3":
        import librosa
        y, sr = librosa.load(path, sr=None, mono=False)
        if y.ndim == 1:
            y = y[:, np.newaxis]   # (N,) → (N,1)
        else:
            y = y.T                # librosa: (ch,N) → (N,ch)
        return y.astype(np.float32), sr

    raise ValueError(f"不支持的格式: {ext}")


def convert(path: str) -> str:
    """
    转换单个文件为目标格式。
    输出文件与输入同目录，扩展名统一改为 .wav。
    返回状态字符串。
    """
    fname = os.path.basename(path)
    out_name = os.path.splitext(fname)[0] + ".wav"
    out_path = os.path.join(os.path.dirname(path), out_name)

    y, sr = _read(path)

    # ── 检查是否已满足目标格式（仅对 WAV 输入有效）─────────────────
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav" and sr == TARGET_SR and y.shape[1] == TARGET_CH:
        return "跳过（已是目标格式）"

    # ── 重采样 ────────────────────────────────────────────────────
    if sr != TARGET_SR:
        y = soxr.resample(y, sr, TARGET_SR, quality="HQ")

    # ── 转立体声 ──────────────────────────────────────────────────
    y = _to_stereo(y)

    # ── 写出 16-bit PCM WAV ───────────────────────────────────────
    sf.write(out_path, y, TARGET_SR, subtype="PCM_16")
    return f"{sr} Hz, {y.shape[1]}ch  →  {TARGET_SR} Hz, {TARGET_CH}ch"


if __name__ == "__main__":
    SUPPORTED = {".wav", ".mp3", ".ogg", ".flac", ".aiff", ".aif"}
    THIS_SCRIPT = os.path.basename(__file__)

    targets = [
        f for f in sorted(os.listdir(INPUT_DIR))
        if os.path.splitext(f)[1].lower() in SUPPORTED
        and f != THIS_SCRIPT
    ]

    if not targets:
        print("没有找到可处理的音频文件。")
    else:
        ok = skip = err = 0
        for fname in targets:
            path = os.path.join(INPUT_DIR, fname)
            print(f"{fname} ... ", end="", flush=True)
            try:
                status = convert(path)
                if status.startswith("跳过"):
                    print(f"[跳过] {status}")
                    skip += 1
                else:
                    print(f"[完成] {status}")
                    ok += 1
            except Exception as e:
                print(f"[错误] {e}")
                err += 1

        print(f"\n完成 {ok} 个 | 跳过 {skip} 个 | 错误 {err} 个")
