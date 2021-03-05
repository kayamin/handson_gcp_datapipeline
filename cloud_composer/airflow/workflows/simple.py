# DAG（ワークフロー）の作成
# https://cloud.google.com/composer/docs/how-to/using/writing-dags?hl=ja

from __future__ import print_function

import datetime

from airflow import models
from airflow.operators import bash_operator
from airflow.operators import python_operator

default_dag_args = {
    # The start_date describes when a DAG is valid / can be run. Set this to a
    # fixed point in time rather than dynamically, since it is evaluated every
    # time a DAG is parsed. See:
    # https://airflow.apache.org/faq.html#what-s-the-deal-with-start-date
    'start_date': datetime.datetime(2018, 1, 1),
}

# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
# models.DAG で生成されるコンテキスト = DAG全体 であり，
# コンテキスト内で定義したタスク（Operator のインスタンス) が DAGを構成するタスクとなる
with models.DAG(
        'composer_sample_simple_greeting', # DAG名を定義
        schedule_interval=datetime.timedelta(days=1), # DAGの実行スケジュールを定義
        default_args=default_dag_args) as dag:

    def greeting():
        import logging
        logging.info('Hello World!')

    # An instance of an operator is called a task. In this case, the
    # hello_python task calls the "greeting" Python function.
    hello_python = python_operator.PythonOperator(
        task_id='hello',
        python_callable=greeting)

    # Likewise, the goodbye_bash task calls a Bash script.
    goodbye_bash = bash_operator.BashOperator(
        task_id='bye',
        bash_command='echo Goodbye.')

    # Define the order in which the tasks complete by using the >> and <<
    # operators. In this example, hello_python executes before goodbye_bash.
    # DAG内で タスク hello_python を実行した後に goodbye_bash が実行される
    hello_python >> goodbye_bash