"""Render bilingual lessons with Pillow, eSpeak NG and FFmpeg.

From the repository root, use PYTHONPATH=backend python backend/scripts/render_academy_videos.py.
Pillow and eSpeak NG are required. FFmpeg may be on PATH or provided by imageio-ffmpeg.
"""

import argparse
import shutil
import subprocess
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont

from migrations.academy_video_content import IT_DEMOS, IT_HEADINGS, video_key
from migrations.language_starters import COPY, LESSONS, PHRASES

BACKEND = Path(__file__).resolve().parents[1]
FONT = BACKEND / "app/core/certificate_assets/NotoSansKR-Regular.ttf"
OUTPUT = BACKEND / "app/media/academy"
WIDTH, HEIGHT = 960, 540
PALETTES = {
    "uz": ("#103c38", "#f4c18c"),
    "en": ("#222f50", "#ddd9ff"),
    "ru": ("#472641", "#fbd1c4"),
    "ko": ("#48271e", "#ffdbad"),
    "html": ("#232831", "#ffbb8f"),
    "python": ("#233b29", "#e9db8d"),
}
LANGUAGES = {"uz": "O‘zbekcha", "en": "English", "ru": "Русский", "ko": "한국어"}
VOICES = {"uz": "uz", "en": "en-us", "ru": "ru", "ko": "ko"}
IT_LABELS = {"html": "HTML / CSS", "python": "Python"}
PRACTICE = {
    "uz": "Tinglang, ovoz chiqarib takrorlang, so‘ng darsdagi quizni bajaring.",
    "en": "Listen, repeat aloud, and then try the lesson quiz.",
    "ru": "Прослушайте фразы, повторите вслух и выполните тест к уроку.",
    "ko": "표현을 듣고 소리 내어 따라 한 뒤 수업 퀴즈를 풀어 보세요.",
}


def font(size):
    return ImageFont.truetype(FONT, size)


def wrapped(draw, text, face, width):
    rows = []
    for paragraph in text.splitlines():
        row = ""
        for word in paragraph.split():
            candidate = f"{row} {word}" if row else word
            if row and draw.textlength(candidate, font=face) > width:
                rows.append(row)
                row = word
            else:
                row = candidate
        rows.append(row)
    return rows


def render_slide(file, subject, source, index, count, heading, caption, code):
    dark, accent = PALETTES[subject]
    img = Image.new("RGB", (WIDTH, HEIGHT), dark)
    draw = ImageDraw.Draw(img)
    draw.ellipse((690, -360, 1390, 340), outline=accent, width=2)
    draw.rounded_rectangle((28, 24, 932, 516), 31, outline=accent, width=1)
    draw.text((66, 66), "SCHOLWARD ACADEMY", font=font(19), fill=accent)
    tag = f"{IT_LABELS.get(subject) or LANGUAGES[subject]}  /  {LANGUAGES[source]}"
    draw.text((893, 66), tag, font=font(17), fill=accent, anchor="ra")
    draw.line((66, 108, 892, 108), fill=accent, width=1)
    y = 134
    for line in wrapped(draw, heading, font(46), 810):
        draw.text(
            (64, y), line, font=font(46), fill="#fff6e8", stroke_width=1, stroke_fill="#fff6e8"
        )
        y += 61
    if code:
        rows = code.splitlines()
        draw.rounded_rectangle((64, y + 13, 892, y + 29 + 35 * len(rows)), 16, fill="#101e1a")
        for offset, line in enumerate(rows):
            indentation = len(line) - len(line.lstrip())
            draw.text(
                (85 + 9 * indentation, y + 25 + 35 * offset),
                line.lstrip(),
                font=font(23),
                fill="#f6dcaa",
            )
    else:
        for line in wrapped(draw, caption, font(28), 800):
            draw.text((66, y + 20), line, font=font(28), fill="#f1e8da")
            y += 42
    draw.rounded_rectangle((66, 474, 891, 480), 3, fill="#8a9b91")
    draw.rounded_rectangle((66, 474, 66 + 825 * (index + 1) / count, 480), 3, fill=accent)
    img.save(file)


def speak(voice, text, path):
    clean = text.translate(str.maketrans({"‘": "'", "’": "'", "…": ".", "—": ","}))
    subprocess.run(
        ["espeak-ng", "-v", VOICES[voice], "-s", "138", "-w", str(path), "--", clean],
        check=True,
        capture_output=True,
    )
    with wave.open(str(path)) as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 22050):
            raise ValueError(f"Unexpected audio format for {voice}")
        return audio.readframes(audio.getnframes())


def language_jobs():
    for source, copy in COPY.items():
        for target in COPY:
            if source == target:
                continue
            for index, unit in enumerate(LESSONS):
                heading, intro = unit[source]
                slides = [(heading, intro, "", [(source, heading), (source, intro)])]
                for foreign, native in zip(
                    PHRASES[index][target], PHRASES[index][source], strict=True
                ):
                    slides.append(
                        (
                            foreign,
                            native,
                            "",
                            [(target, foreign), (source, native), (target, foreign)],
                        )
                    )
                slides.append((copy["quiz"], PRACTICE[source], "", [(source, PRACTICE[source])]))
                yield target, source, index + 1, slides


def computing_jobs():
    for subject, units in IT_DEMOS.items():
        for source, titles in IT_HEADINGS[subject].items():
            for index, (code, copy) in enumerate(units):
                overview, exercise = copy[source]
                title = titles[index]
                task = {
                    "uz": "Mustaqil mashq",
                    "en": "Try it yourself",
                    "ru": "Практическое задание",
                    "ko": "직접 해 보기",
                }[source]
                yield (
                    subject,
                    source,
                    index + 1,
                    [
                        (title, overview, "", [(source, title), (source, overview)]),
                        (IT_LABELS[subject], "", code, [(source, overview)]),
                        (task, exercise, "", [(source, exercise)]),
                    ],
                )


def render_video(ffmpeg, job):
    subject, source, position, slides = job
    out = OUTPUT / video_key(subject, source, position)
    if out.exists():
        return
    with TemporaryDirectory(prefix="academy-clip-") as folder:
        root = Path(folder)
        concat = []
        silence = b"\0" * 2 * 22050
        with wave.open(str(root / "narration.wav"), "wb") as audio:
            audio.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
            for index, (heading, caption, code, narration) in enumerate(slides):
                still = root / f"frame-{index}.png"
                render_slide(still, subject, source, index, len(slides), heading, caption, code)
                frames = b"".join(
                    speak(voice, text, root / "voice.wav") + silence for voice, text in narration
                )
                frames += silence * (2 if code else 1)
                audio.writeframes(frames)
                concat.extend([f"file '{still.name}'", f"duration {len(frames) / 44100:.6f}"])
        concat.append(f"file 'frame-{len(slides) - 1}.png'")
        (root / "slides.txt").write_text("\n".join(concat) + "\n")
        pending = out.with_suffix(".partial")
        try:
            subprocess.run(
                [
                    ffmpeg,
                    "-v",
                    "error",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "1",
                    "-i",
                    str(root / "slides.txt"),
                    "-i",
                    str(root / "narration.wav"),
                    "-c:v",
                    "libx264",
                    "-threads",
                    "2",
                    "-tune",
                    "stillimage",
                    "-preset",
                    "fast",
                    "-crf",
                    "25",
                    "-vf",
                    "fps=12",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "48k",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    "-f",
                    "mp4",
                    str(pending),
                ],
                check=True,
            )
            pending.rename(out)
        finally:
            pending.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=4)
    options = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        from imageio_ffmpeg import get_ffmpeg_exe

        ffmpeg = get_ffmpeg_exe()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=options.jobs) as workers:
        list(
            workers.map(
                lambda job: render_video(ffmpeg, job), [*language_jobs(), *computing_jobs()]
            )
        )


if __name__ == "__main__":
    main()
