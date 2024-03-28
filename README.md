# Speech plus Subtitles Player app written in Python with Flet GUI framework

With this GUI app, you can easily edit subtitles by playing speech audio file and SRT text in sync.

<img width="1084" alt="screenshot_en" src="https://github.com/tokyohandsome/Speech-plus-Subtitles-Player/assets/34906599/755220b2-d7d7-4f95-bafa-b5a5ceb1b500">

Use OpenAI's Whisper or similar speech-to-text software to generate SRT file which will be loaded when you load an audio file.  
Click on subtitles text to edit it.  
Save button overwrites current file.  
SRT and TXT buttons export as respective file where TXT has no timestamps.

Note: This app was developed and only tested on macOS Sonoma 14.3 running on Mac Studio (M2 Max).

Requirements:
- Python >= 3.8
- Flet >= 0.21.0 (`pip install flet`)
- Numpy (`pip install numpy`)

How to run the app:
```
python main.py
```

Known issues/limitations:
- Move or resize of window is laggy when the number of subtitles (=buttons) is big.
- Built app by `flet build macos --include-packages flet_audio` crashes as Numpy cannot be included with the current Flet version. Comment `import numpy` to build but auto scroll/slider won't work.
- Sometimes Open/Export dialogs freezes and you have to quit the app. Save frequently.
- Supported MP3 sample rate by macOS is 44.1KHz.
- Add audio file extension to the `pick_speech_file` method if it's grayed out.
- SRT file must have only one line of text. If you use Whisper to generate SRT, it should be fine.

Font: [源界明朝](https://flopdesign.com/blog/font/5146/)

© 2024 [Peddals.com](https://blog.peddals.com/)
