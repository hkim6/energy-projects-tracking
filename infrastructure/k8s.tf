resource "kubernetes_namespace" "my_namespace" {
  metadata {
    name = "energy-apps"
  }
}

resource "kubernetes_service_account" "my_ksa" {
  metadata {
    name      = "energy-news-pull-sa"
    namespace = kubernetes_namespace.my_namespace.metadata[0].name
  }
}

resource "kubernetes_deployment" "energy_news_pull" {
  metadata {
    name      = "energy-news-pull"
    namespace = "default"
    labels = {
      app = "energy-news-pull"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "energy-news-pull"
      }
    }

    template {
      metadata {
        labels = {
          app = "energy-news-pull"
        }
      }

      spec {

        container {
          name  = "energy-news-pull"
          image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.docker_repo}/energy-project-tracking:latest"

          port {
            container_port = 8080
          }

          env {
            name  = "PROJECT_ID"
            value = var.project_id
          }

          resources {
            limits = {
              memory = "512Mi"
              cpu    = "200m"
            }

            requests = {
              memory = "128Mi"
              cpu    = "100m"
            }
          }
        }
      }
    }
  }
}