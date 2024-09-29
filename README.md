# TennisClipper

テニス録画映像からプレー中のみ切り出すプログラム

## tennis_clip.py

- メインプログラム
- ウインブルドンはプレー中常に同じカメラ画角になるため，プレー中の映像をテンプレート画像としてテンプレート画像と類似する映像フレームのみ切り出して mp4 保存する
- 入出力動画のフォーマットは ffmpeg 対応

### 実行環境

- pip install -f requirements.txt
- ffmpeg 実行バイナリ必要（tennis_clip.py と同じフォルダに置く）
  - ffmpeg.exe
  - ffplay.exe
  - ffprobe.exe
  - [公式サイト](https://ffmpeg.org/)よりダウンロード

### 制限

- 音声未対応
- 天候変化などに未対応
