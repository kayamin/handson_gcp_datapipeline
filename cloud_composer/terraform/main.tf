resource "google_service_account" "cloud_composer" {
  account_id   = "cloud_composer"
  display_name = "cloud_composer"
  description  = "A service account for cloud composer"
}

resource "google_project_iam_member" "cloud_composer" {
  for_each = toset([
    "role/composer.worker"
  ])
  role   = each.value
  member = "serviceAccount:${google_service_account.cloud_composer.email}"
}

// https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/composer_environment#node_config
resource "google_composer_environment" "main" {
  name   = "composer"
  region = "asia-northeast1"

  config {
    // airflow を実行するGKEノードの設定
    node_count = 2
    node_config {
      zone         = "asia-northeast1"
      machine_type = "e2-small"
      service_account = google_service_account.cloud_composer.email
    }

    software_config {
      // airflow の設定値を上書きしたいときに設定
      airflow_config_overrides = {
        core-load_example = "True"
      }

      // airflow で利用したい環境変数を設定
      env_variables = {
        FOO = "bar"
      }

      // airflow で利用したい python パッケージを指定
      pypi_packages = {
        numpy = ""
        pandas = ""
      }

      python_version = "3" // デフォルトは2系

      // 利用する airflow のバージョンを指定可能
      // https://cloud.google.com/composer/docs/reference/rest/v1beta1/projects.locations.environments#softwareconfig
      // image_version = ""

    }
  }

}