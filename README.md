# Skincare PDF Generator

皮膚科の診察時に、現在使用しているスキンケア製品（洗顔料、化粧水など）の情報を医師へスムーズかつ正確に伝えるためのPDF生成Webツールです。

## 概要 (Description)
スキンケア製品の「商品名」「公式URL」「全成分表示」をWebフォームから入力することで、自動的にURLのQRコードを生成し、医師が確認しやすいレイアウト（A4縦・ヘッダー集約型）のPDFファイルを一括出力します。成分が多い商品でも、読みやすく整理された状態で印刷・共有が可能です。

## 主な機能 (Features)
- **Webフォーム入力**: 複数の製品情報をブラウザ上から簡単に入力・追加可能。
- **QRコード自動生成**: 製品のURLからQRコードを動的に生成し、PDFに配置。
- **PDF一括生成**: 複数の製品を1つのPDFファイル（1製品1ページ）としてまとめて出力。
- **最適化されたレイアウト**: 医師がパッと見て重要情報（製品名、QR、成分）を把握できる構成。

## 使用技術 (Tech Stack)
- **Backend**: Python 3, Flask
- **PDF Generation**: ReportLab
- **QR Code**: qrcode, Pillow
- **Frontend**: HTML, CSS, JavaScript (Vanilla)

## 環境構築と使い方 (Setup & Usage)

1. **リポジトリの準備**
   任意のディレクトリにファイルを配置し、ターミナルでそのフォルダに移動します。

2. **仮想環境の作成と有効化**
   Pythonの仮想環境（venv）を作成し、有効化します。
   ```bash
   # Windowsの場合
   python -m venv venv
   .\venv\Scripts\activate

   # Mac/Linuxの場合
   python3 -m venv venv
   source venv/bin/activate

3. **必要なライブラリのインストール**
   requirements.txt を使用して、必要なパッケージを一括インストールします。
   ```bash
   pip install -r requirements.txt

4. **アプリケーションの起動**
   以下のコマンドでローカルサーバーを立ち上げます。
   ```bash
   python app.py

5. **ブラウザでアクセス**
   ブラウザを開き、以下のURLにアクセスしてツールを利用します。
