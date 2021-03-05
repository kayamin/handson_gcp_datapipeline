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
  

## GCP ではリソース識別のために label を付与する
- AWS での tag のようなもの
- GCP では tag は FirewallRules の適用対象識別のためにリソースに付与するものなので注意

[AWSと比較しつつGCPに入門したときのメモ](https://qiita.com/noko_qii/items/5e616aa2cc6e46919e34)


## Cloud Composer

[Cloud Composerでデータ基盤のワークフローを作る](https://medium.com/eureka-engineering/data-mgmt-cloud-composer-29ba3fcbffe0)

[クイックスタート](https://cloud.google.com/composer/docs/quickstart#web-ui)

airflow cli をラップした gcloud composer コマンドがある
```shell
# CloudComposerで起動したairflowへDAGファイルをアップロード (対応するGCSバケットにファイルがアップロードされる
gcloud composer environments storage dags import --environment composer --location asia-northeast1 --source quickstart.py
```

- DAG
  - 非巡回有効グラフ，Airflow では Task の処理の流れを DAGとして表現し，実行する
  - python スクリプト内で models.DAG で生成されるコンテキストで定義する
- Task
  - DAGを構成する処理，インスタンス化されたOperator を指す
  - pythonスクリプト内で Task 同士を `>>` `<<` 演算子を用いて並べることでDAG内でのタスクの順番が定義される
  - Operator
    - Task を構成する処理を定義するクラス
    - Airflow公式のOperator に加えてコミュニティが作成した各種Operatorが存在  `SlackAPIOperator` 等
    - BashOperator
      - ワーカーの bashスクリプトで指定されたコマンドを実行する 
      - gcloud, bq, gsutil, kubectl コマンドはプリインストールされている
    - PythonOperator
      - ワーカーで任意のpythonコードを実行する
      - google-cloud-bigquery,dataflow,storage, pandas, pandas-gbq 等のパッケージはプリインストールされている
      - CloudComposer 定義時に任意のPythonパッケージを追加可能
    - GoogleCloud Operator
      - 各種GCPプロダクトを利用するタスクを定義できるOperator, プロダクト毎に存在（ `bigquery_operator`, `dataflow_operator` etc )
      - GCP プロダクトでの処理をラップしてくれるので shellスクリプト，pythonスクリプトを組んで全て自前で実装するよりもこちらを使ったほうが楽
  - Sensor
    - Operator の中でも，何かしらのリソースの状態を polling し，変化があった場合に実行される Operator を指す
  

## Airflow (ver 2.0 についての説明になっており，モジュール名が 1系とは異なるので注意）

[Tutorial](https://console.cloud.google.com/storage/browser/asia-northeast1-composer-a714ec32-bucket/dags?project=leaarninggcp-ash&pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22))&prefix=&forceOnObjectsSortingFiltering=false)

[Concepts](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html)

- DAG内のタスクは別のプロセスとして実行され，異なるworkerで実行されることもある．
- タスク間で情報を共有したい場合は `XComs` を用いる

> if two operators need to share information, like a filename or small amount of data, you should consider combining them into a single operator. If it absolutely can’t be avoided, Airflow does have a feature for operator cross-communication called XCom that is described in the section XComs

- XCom
  - Task 間で情報をやり取りするための仕組み
  - pickle化できるオブジェクトなら何でもやり取り可能
    - pickle化するのでオブジェクトのサイズには注意
  - オブジェクトの serialize, deserialize 方法等はカスタマイズも可能

特定のタスクで XCom に値を push し，他のタスクでXComから値を pull する (task_id を指定)
```python
# inside a PythonOperator called 'pushing_task'
# タスク内で xcom_push() を呼び出すか task で 値を return すると XComに値を push できる
def push_function():
    return value

# inside another PythonOperator
def pull_function(task_instance):
    value = task_instance.xcom_pull(task_ids='pushing_task')
```

> XComs can be “pushed” (sent) or “pulled” (received). When a task pushes an XCom, it makes it generally available to other tasks. Tasks can push XComs at any time by calling the xcom_push() method. In addition, if a task returns a value (either from its Operator’s execute() method, or from a PythonOperator’s python_callable function), then an XCom containing that value is automatically pushed.


- Variables
  - Airflow 環境内でグローバルに利用できる key,valueペア
  - 異なるDAG, タスク間で値を共有可能
    - XComと違ってこっちは設定等を共有するのに使う感じか
    - XComの方は task_id と共に値を保管するので，順番がある処理で値を受け渡しするのに都合良い
  
  
```python
from airflow.models import Variable
foo = Variable.get("foo")
bar = Variable.get("bar", deserialize_json=True)
baz = Variable.get("baz", default_var=None)
```

- [Branching](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#branching)
  - DAG内で分岐（後続するパスの中で特定のものだけを実行する等)したい場合に用いるOperator
  - BranchPythonOperator
    - `task_id` を返す python callable を引き受け，返された `task_id`を有する直接つながっている後続のタスクを実行する 
    - 直接つながっているタスクであれば，間のタスクをスキップして実行させることも可能
    - 利用例: XCom に前段のタスクの実行結果を格納し， BranchPythonOperator で Xcomから前段のタスクの実行結果を取得した上で，次に実行する task_id を返す

- SubDAGs
  - 複数のTaskを含むTaskのこと, 複数の繰返し処理タスクを定義する際に便利, タスクを分割することで並列実行できる?(けどしないほうが良い？)
  - `SubDagOperator` を用いて定義する
  - it is possible to specify an executor for the SubDAG. It is common to use the SequentialExecutor if you want to run the SubDAG in-process and effectively limit its parallelism to one. Using LocalExecutor can be problematic as it may over-subscribe your worker, running multiple tasks in a single slot
  
- Task Group (version 2.0 からの新機能)
  - Web UI上でTaskのまとまりを作る機能
  - Taksが多数存在するときに, TaskGroup でまとめておくと，WebUIで見た際にグルーピングされるのでわかりやすくなる
  
```python
with TaskGroup("group1") as group1:
    task1 = DummyOperator(task_id="task1")
    task2 = DummyOperator(task_id="task2")

task3 = DummyOperator(task_id="task3")

group1 >> task3
```

- [Trigger Rules](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#trigger-rules)
  - タスクの実行条件をカスタマイズ可能，デフォルトは `all_success` = DAG上で先行するタスク全てが成功した場合にタスクを実行する
  - 様々な条件指定が存在(ドキュメントを参照) 

- LatestOnlyOperator
  - 最新の時間タイミングでDAGが実行された場合のみ後続のTaskを実行する Operator
    - DAGを定義した際に，どのタイミングで実行するかが問題となる．
    - 過去のタイミングに対してDAGが実行された場合はこのOperator で停止する
    - 具体的にこれが必要となるケースが思いつかないが，，DAG定義時に過去の時間帯に対して実行してしまう？？
    - > use the LatestOnlyOperator to skip tasks that are not being run during the most recent scheduled run for a DAG.
  - [Difference between latest only operator and catchup in Airflow](https://stackoverflow.com/questions/61252482/difference-between-latest-only-operator-and-catchup-in-airflow)
    -  DAG の default_arg で catchup=True にすると
      - start_date から現在までの間の全ての schedule interval に対して DAG run を生成する
      - 要は過去の実行期間に対して全て実行すると
    - LatestOnlyOperator があると
      - 上記の過去のインターバルに対しての DAG run の場合は LatestOnlyOperator 以降の箇所が実行されなくなる
      - backfill 等の際には実行したくない Task を LatestOnlyOperator の後ろに設定しておくと再実行を防止できる
  
- [Exceptions](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#exceptions)
  - Task での例外処理は大きく３パターン
    - 単純な例外（PythonOperator での raise )
      - タスクは fail する，retry が設定されていたら設定されている限界数までretry する
    - AirflowSkipException
      - この例外が raise された場合は，このタスクはスキップされる
    - AriflowFialException
      - この例外が raise された場合は，設定されている retry 回数に関わらず即座に fail にする
  

- [Packaged DAGs](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#packaged-dags)
  - 複数のDAG (pythonファイル)や，利用する関数等を zip ファイルにまとめてアップロード可能
  - Airflow は zip ファイルのトップディレクトリのみをスキャンし，DAG を検出する
    - サブディレクトリの DAGは認識されない
    - サブディレクトリには必要な関数やパッケージ等を入れておく
  - 例えば venv で必要なパッケージのみを特定のディレクトリにインストールして DAGと一緒に zip化してアップロードする等
