import io

from google.cloud import secretmanager, storage, bigquery
import google.auth
import pandas as pd


def upload_json_to_bucket(
    project_id: str, bucket_name: str, blob_name: str, object: io.BytesIO
) -> str:
    """Uploads a file to the GCS bucket."""

    # Initialize a storage client
    client = storage.Client(project=project_id)

    # Get the bucket
    bucket = client.bucket(bucket_name)

    # Create a blob object in the bucket
    blob = bucket.blob(blob_name)

    # Upload the file to that blob
    blob.upload_from_string(object)

    print(f"File uploaded to {blob_name}.")

    return blob_name


def get_pgse_secrets(
    project_no: str, pgse_id: str = "pgse_id", pgse_key: str = "pgse_key"
) -> dict:
    """Returns the secrets for the Google Custom Search API."""

    client = secretmanager.SecretManagerServiceClient()
    id_secret_string = f"projects/{project_no}/secrets/{pgse_id}/versions/latest"
    key_secret_string = f"projects/{project_no}/secrets/{pgse_key}/versions/latest"

    return {
        "SEARCH_ENGINE_KEY": client.access_secret_version(
            request={"name": key_secret_string}
        ).payload.data.decode("UTF-8"),
        "SEARCH_ENGINE_ID": client.access_secret_version(
            request={"name": id_secret_string}
        ).payload.data.decode("UTF-8"),
    }


def get_current_project_id():
    credentials, project_id = google.auth.default()
    return project_id


def merge_df_to_bq(df: pd.DataFrame, table_id: str, project_id: str, dataset_id: str):
    """Merges a DataFrame to a BigQuery table."""
    client = bigquery.Client()
    table = f"{project_id}.{dataset_id}.{table_id}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        source_format=bigquery.SourceFormat.PARQUET,
    )
    temp_table = f"{project_id}.{dataset_id}.{table_id}_temp"
    query = f"CREATE OR REPLACE TABLE `{temp_table}` LIKE {table}"

    client.query(query).result()
    job = client.load_table_from_dataframe(df, temp_table, job_config=job_config)
    job.result()  # Wait for the job to complete

    merge_sql = f"""
        MERGE `{table}` T
        USING `{temp_table}` S
        ON T.filename = S.filename
        WHEN MATCHED THEN UPDATE
            SET T.title = S.title,
                T.published = S.published,
                T.last_updated = S.last_updated,
                T.link = S.link,
                T.summary = S.summary,
                T.blob = S.blob,
                T.source = S.source,
                T.time_scraped = S.time_scraped
        WHEN NOT MATCHED THEN
            INSERT (title, published, last_updated, link, summary, blob, filename, source, time_scraped)
            VALUES (S.title, S.published, S.last_updated, S.link, S.summary, S.blob, S.filename, S.source, S.time_scraped);
        """

    client.query(merge_sql).result()

    client.delete_table(f"{temp_table}", not_found_ok=True)
