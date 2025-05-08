terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.8.0"
    }
  }
}


# Container Orchestration

resource "google_artifact_registry_repository" "docker_repo" {
  provider = google-beta
  project = var.project_id
  repository_id = "docker-repo"
  location = var.region
  format   = "DOCKER"
  description = "My Docker repository"
}

resource "google_container_cluster" "default_cluster" {
  name     = "primary-cluster"
  location = var.zone
  project = var.project_id

  initial_node_count = 1
  remove_default_node_pool = true

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
}

resource "google_container_node_pool" "default_node_pool" {
  name       = "primary-node-pool"
  cluster    = google_container_cluster.default_cluster.name
  location   = var.zone
  node_count = 1


  node_config {
    service_account = "energy-news-pull@${var.project_id}.iam.gserviceaccount.com"
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    metadata = {
      disable-legacy-endpoints = "true"
    }
    labels = {
      env = var.project_id
    }
  }
}