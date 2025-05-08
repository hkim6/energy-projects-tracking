# Storage
resource "google_storage_bucket" "my_bucket" {
  name     = var.bucket_name
  location = var.region

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = false
  }

  storage_class = "STANDARD"
}

# Data Warehouse
resource "google_bigquery_dataset" "energy_news" {
  dataset_id                  = "energy_news"
  location                    = "US"
}

resource "google_bigquery_table" "articles" {
  dataset_id = google_bigquery_dataset.energy_news.dataset_id
  table_id   = "articles"
  deletion_protection = false

  time_partitioning {
    type = "DAY"
  }

  labels = {
    env = "default"
  }

  schema = <<EOF
[
  {
    "name": "title",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Article title"
  },
  {
    "name": "published",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "date and time when the article was published"
  },
  {
    "name": "last_updated",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "date and time when the article was last updated"
  },
  {
    "name": "link",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "URL of the article"
  },
  {
    "name": "summary",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Summary of the article"
  },
  {
    "name": "blob",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "GCS Blob of the article"
  },
  {
    "name": "filename",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "GCS Blob filename of the article"
  },
  {
    "name": "source",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Source of the article"
  },
  {
    "name": "time_scraped",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Date and time when the article was scraped"
  }
]
EOF

}
