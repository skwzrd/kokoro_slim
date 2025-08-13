from flask import Flask, request, send_file, render_template_string, url_for, abort
import os
from time import time
from tts import KokoroTTS, make_path, get_pipeline
from enums import Language, Voice, Device, Ext


app = Flask(__name__)


HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>kokoro</title>
    <style>
        html {
            background-color: black;
            color: white;
            font-family: arial;
        }
        a, a:visited {
            color: white;
        }
    </style>
</head>
<body>
  <form method='post' action='/'>

    <textarea name='text' rows='6' cols='60' placeholder='Enter text here...' required>{{ text }}</textarea>
    <br>

    <label for='ext'>Format:</label>
    <select name='ext' id='ext'>
      {% for e in exts %}
        <option value='{{ e.value }}' {% if e.value == ext %}selected{% endif %}>{{ e.name }}</option>
      {% endfor %}
    </select>
    <br>

    <label for='lang_code'>Language:</label>
    <select name='lang_code' id='lang_code'>
      {% for l in lang_codes %}
        <option value='{{ l.value }}' {% if l.value == lang_code %}selected{% endif %}>{{ l.name }}</option>
      {% endfor %}
    </select>
    <br>

    <label for='voice'>Voice:</label>
    <select name='voice' id='voice'>
      {% for v in voices %}
        <option value='{{ v.name }}' {% if v.name == voice %}selected{% endif %}>{{ v.name }}</option>
      {% endfor %}
    </select>
    <br>

    <label for='speed'>Speed:</label>
    <input type='number' step='0.1' min='0.1' max='3.0' name='speed' id='speed' value='{{ speed }}'>
    <br>

    <label for='sample_rate'>Sample Rate:</label>
    <input type='number' name='sample_rate' id='sample_rate' value='{{ sample_rate }}'>
    <br>

    <button type='submit'>Create</button>
  </form>

  {% if audio_url %}
    <h2>Audio</h2>
    <audio controls>
        <source src='{{ audio_url }}' type='audio/{{ ext }}'>
        Your browser does not support the audio element.
    </audio>

    <p>
        <a href='{{ audio_url }}' download>Download Audio</a>
    </p>
  {% endif %}
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    audio_url = None

    exts = list(Ext)
    ext = tts.ext

    voices = list(Voice)
    voice_name = tts.voice.name

    lang_codes = list(Language)
    lang_code = tts.pipeline.lang_code

    speed = tts.speed
    sample_rate = tts.sample_rate

    if request.method == 'POST' and (text := request.form.get('text', '').strip()):

        ext = request.form.get('ext', ext)
        tts.ext = ext

        lang_code = request.form.get('lang_code', lang_code)
        if lang_code != tts.pipeline.lang_code:
            tts.pipeline = get_pipeline(lang_code=Language(lang_code), device=Device(tts.pipeline.model.device.type), repo_id=tts.pipeline.repo_id)

        voice_name = request.form.get('voice', voice_name)
        tts.voice = Voice[voice_name]
        
        speed = float(request.form.get('speed', speed))
        tts.speed = speed

        sample_rate = int(request.form.get('sample_rate', sample_rate))
        tts.sample_rate = sample_rate

        filename = tts.filename_callback()

        p = tts.text_to_audio(text=text, filename=filename)
        filename = os.path.basename(p)

        audio_url = url_for('download_file', filename=filename)

    return render_template_string(
        HTML,
        text=text,
        audio_url=audio_url,
        ext=ext,
        exts=exts,
        lang_codes=lang_codes,
        lang_code=lang_code,
        voices=voices,
        voice=voice_name,
        speed=speed,
        sample_rate=sample_rate,
    )


@app.route('/download/<path:filename>')
def download_file(filename: str):
    if not filename:
        abort(404)

    path = make_path(tts.output_path, filename)
    print(path)
    if not os.path.isfile(path):
        abort(404)

    return send_file(path, as_attachment=True)


pipeline = get_pipeline(
    lang_code=Language.AMERICAN_ENGLISH,
    device=Device.GPU,
    repo_id='hexgrad/Kokoro-82M',
)


tts = KokoroTTS(
    pipeline,
    ext=Ext.WAV,
    voice=Voice.AM_ADAM,
    speed=1.0,
    sample_rate=24_000,
    filename_callback=lambda: int(time() * 1000),
    output_path=make_path('..', 'output'),
)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
