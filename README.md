# TennisClipper

テニス録画映像からプレー中のみ切り出すプログラム

## tennis_clip.py

- メインプログラム
- ウインブルドンはプレー中常に同じカメラ画角になるため，プレー中の映像をテンプレート画像としてテンプレート画像と類似する映像フレームのみ切り出して mp4 保存する
- 入出力動画のフォーマットは ffmpeg 対応

### 実行環境

- `pip install -f requirements.txt`
- ffmpeg 実行バイナリ必要（tennis_clip.py と同じフォルダに置く）
  - ffmpeg.exe
  - ffplay.exe
  - ffprobe.exe
  - [公式サイト](https://ffmpeg.org/)よりダウンロード

### EXE化

- `pyinstaller --onefile tennis_clip.py`

### 実行手順

- avidemuxを使い録画tsファイルから1試合分をクリップして保存
  - 映像，音声ともにCopy，出力形式は Mpeg TS Muxerを選択
  - 保存先はd:\usr\dl, ファイル名は半角英数字で指定
- プレイ中の1フレームをテンプレート画像として保存
  - avidemuxでプレイ中の1フレームを選択し，「ファイル」→「画像を保存」→「JPEGで保存」(CTRL-E)でテンプレート画像を保存
  - 保存先はd:\usr\dl, ファイル名はtsファイル名と同じ.jpgにする
- tennis_clip.exeを実行
  - d:\usr\dl にある全てのts, jpgのペアを処理する  
  - 出力は同じフォルダに`ファイル名.mp4`として保存される

### 制限

- 天候変化などに未対応
