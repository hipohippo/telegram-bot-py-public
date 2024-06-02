# env: deeplearning
from pathlib import Path

import opencc
import whisper

converter = opencc.OpenCC("t2s.json")
model_checkpoint = Path("/home/hipo/apps/openai-whisper/tiny.pt")
model = whisper.load_model(str(model_checkpoint.resolve()))

# input_video_file = r"c:\users\weiwe\Downloads\[960x540] Financial Results Highlights.mp4"
# input_audio_file = r"c:\users\weiwe\Downloads\[960x540] Financial Results Highlights.mp3"
# ffmpeg_out = subprocess.run(f'ffmpeg -i "{input_video_file}" "{input_audio_file}"',shell=True,capture_output=True)
fn = r"/home/hipo/Downloads/ep03.m4a"
result = model.transcribe(fn)
with open(rf"{fn}.txt", mode="w", encoding="utf-8") as f:
    f.write("，".join([converter.convert(segment["text"]) for segment in result["segments"]]))
