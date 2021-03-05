# Trigger Rules
# https://airflow.apache.org/docs/apache-airflow/stable/concepts.html#trigger-rules

#dags/branch_without_trigger.py

import datetime as dt

from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator

dag = DAG(
    dag_id='branch_without_trigger',
    schedule_interval='@once',
    start_date=dt.datetime(2019, 2, 28)
)

run_this_first = DummyOperator(task_id='run_this_first', dag=dag)

# branch_a に進むように指定
branching = BranchPythonOperator(
    task_id='branching', dag=dag,
    python_callable=lambda: 'branch_a'
)

branch_a = DummyOperator(task_id='branch_a', dag=dag)
follow_branch_a = DummyOperator(task_id='follow_branch_a', dag=dag)

branch_false = DummyOperator(task_id='branch_false', dag=dag)

# タスクの trigger_rule を設定することで, 前段のタスクがどのような状態であれば，そのタスクを実行するのかを指定することができる
# デフォルトは all_success であり skip したものがあると条件は満たされない
join = DummyOperator(task_id='join', dag=dag)

# skip も許容する場合は none_failed_or_skipped を用いる
# join = DummyOperator(task_id='join', dag=dag, trigger_rule='none_failed_or_skipped')

run_this_first >> branching
branching >> branch_a >> follow_branch_a >> join
branching >> branch_false >> join