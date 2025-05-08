# Give node pool accesses required for app
module "my-app-workload-identity" {
  source              = "terraform-google-modules/kubernetes-engine/google//modules/workload-identity"
  name                = "energy-news-pull"
  namespace           = "energy-apps"
  project_id          = var.project_id
  roles               = ["roles/secretmanager.secretAccessor", "roles/storage.objectAdmin", "roles/bigquery.dataEditor", "roles/artifactregistry.reader"]
}