# CloudComposer
- Apache Airflow を提供するマネージドサービス


# Tips

## Terraform の認証周り
- 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` に terraform で利用する service account のクレデンシャルを含む jsonファイルのパスを設定する
- terraform コマンド実行時に自動で上記jsonを参照して, GCP の api を呼び出してくれる

## gsutil

- バージョニングが有効になっている場合
    - バージョニングされた過去のファイルは `{ファイル名}#{適当な数字}` という形式のファイル名になっている  
    - `gsutil ls -a` で過去のバージョン含めて全て表示される
    - `gsutll rm -r` で過去のバージョン含めて全て削除できる