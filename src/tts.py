import os
import soundfile as sf
from kokoro import KPipeline
import subprocess
from enums import Language, Voice, Device, Ext
from time import time
from typing import Callable


def make_path(*filepaths):
    return os.path.realpath(os.path.join(os.path.dirname(__file__), *filepaths))


class KokoroTTS:
    def __init__(
        self,
        lang_code=Language.AMERICAN_ENGLISH,
        device: Device=Device.CPU,
        repo_id="hexgrad/Kokoro-82M",
        ext: Ext = Ext.WAV,
        voice: Voice = Voice.AM_ADAM,
        speed: float = 1.0,
        sample_rate: int = 24_000,
        output_path: str = make_path('..', 'output'),
        filename_callback: Callable = None,
    ):
        """
        - sample_rate > 20_000 is recommended
        - mp3 is about ~5x smaller than wav (requires FFMPEG)
        - higher speed is faster speech
        - if callback_filename is specified, ignore filename
        """
        self.pipeline = KPipeline(lang_code=lang_code.value, device=device.value, repo_id=repo_id)
        self.ext = ext
        self.voice = voice
        self.speed = speed
        self.sample_rate = sample_rate
        self.output_path = output_path
        self.filename_callback = filename_callback


    def text_to_audio(self, text: str, filename: Callable | str=None):
        text = text.strip()

        generator = self.pipeline(text, voice=self.voice.value, speed=self.speed, split_pattern=None)
        _, _, audio = next(generator)

        if self.filename_callback:
            filename = self.filename_callback()
        elif not filename:
            raise ValueError('Must specify a filename')

        wav_path = make_path(self.output_path, f"{filename}.wav")
        sf.write(wav_path, audio, self.sample_rate)

        if self.ext == Ext.MP3:
            return self.transcode(wav_path, self.ext)

        return wav_path


    def transcode(self, input_path: str, target_ext: Ext):
        target_path = os.path.splitext(input_path)[0] + f".{target_ext.value}"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                input_path,
                "-codec:a",
                "libmp3lame" if target_ext == Ext.MP3 else "copy",
                "-qscale:a",
                "2" if target_ext == Ext.MP3 else None,
                target_path,
            ],
            check=True,
        )
        os.remove(input_path)
        return target_path


if __name__ == "__main__":
    text = """I am so happy I drive a Cadillac. Gosh."""

    tts = KokoroTTS(
        lang_code=Language.AMERICAN_ENGLISH,
        device=Device.CPU,
        repo_id="hexgrad/Kokoro-82M",
        ext=Ext.WAV,
        voice=Voice.AM_ADAM,
        speed=1.0,
        sample_rate=24_000,
        filename_callback=lambda: int(time() * 1_000),
        output_path=make_path('..', 'output'),
    )

    p = tts.text_to_audio(text)
    print(f'Saved file: {p}')
