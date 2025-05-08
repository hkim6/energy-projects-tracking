import json
import os
import sys
from datetime import datetime
import pandas as pd
import time
import logging
import requests
import traceback
# from transformers import pipeline

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from ftfy import fix_text

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from gcp_utils import (
    get_current_project_id,
    get_pgse_secrets,
    upload_json_to_bucket,
    merge_df_to_bq,
)


def scrape_article_body(url):
    options = Options()
    options.add_argument(
        "--headless"
    )  # Optional: remove if you want to see the browser
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        # Wait until the div with the specific class loads
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.entry-content.post-layout-layout_2")
            )
        )

        # Extract the div content
        content_div = driver.find_element(
            By.CSS_SELECTOR, "div.entry-content.post-layout-layout_2"
        )
        return content_div.text

    finally:
        driver.quit()


def parse_articles(response: dict) -> dict:
    """Parses the articles from the Google Custom Search API response."""

    article_items = {}
    article_items["title"] = response.get("title")
    article_items["published"] = (
        response.get("pagemap", {}).get("metatags", {})[0].get("article:published_time")
    )
    article_items["published"] = (
        response.get("pagemap", {}).get("metatags", {})[0].get("article:modified_time")
    )
    article_items["link"] = response.get("link")
    article_items["body"] = fix_text(scrape_article_body(response.get("link")))

    # Reset buffer position to the beginning (optional if you want to read from it)

    return article_items


def generate_article_filename(article_items: dict) -> str:
    """Generates a filename for the article based on its title and published date."""
    # Extract the date from the published field
    date = article_items["published"][0:10]
    dt = datetime.fromisoformat(article_items.get("published"))

    # Convert to Unix time (seconds since epoch)
    unix_time = int(dt.timestamp())
    file_name = f"articles/{date}/{'_'.join(article_items['title'].lower().split(' ')[0:3])}_{unix_time}.json"

    return file_name


# If you want to summarize aricle using PyTorch/Transformers
# def summarize_article(article_text: str) -> str:
#     summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
#     summary = summarizer(article_text, max_length=130, min_length=60, do_sample=False)

#     return summary[0]["summary_text"]


def generate_row(article_items: dict, blob_name: str) -> dict:
    """Generates a row for the BigQuery table."""
    row = {
        "title": article_items.get("title"),
        "published": article_items.get("published"),
        "last_updated": article_items.get("last_updated", "N/A"),
        "link": article_items.get("link"),
        "summary": None,  # summarize_article(article_items.get("body")),
        "blob": blob_name,
        "filename": blob_name.split("/")[-1],
        "source": "Google Custom Search API",
    }
    return row


def main(
    query: str = "site:power-eng.com renewables",
    url: str = "https://www.googleapis.com/customsearch/v1",
    num_articles: int = 20,
    time_range_months: int = 1,
    start_result_index: int = 0,
):
    """Main function to run the script."""
    project_id = os.getenv("PROJECT_ID")
    project_no = os.getenv("PROJECT_NO")
    # if not project_id:
    #     project_id = get_current_project_id()
    secrets = get_pgse_secrets(project_no)
    if num_articles > 10:
        batches = [10] * (num_articles // 10)  # add as many 10s as possible
        if num_articles % 10 != 0:
            batches.append(num_articles % 10)
    else:
        batches = [num_articles]

    # Initialize the Google Custom Search API

    for num_articles in batches:
        print(f"Fetching {num_articles} articles...")
        params = {
            "key": secrets["SEARCH_ENGINE_KEY"],
            "cx": secrets["SEARCH_ENGINE_ID"],
            "q": query,
            "num": num_articles,  # Max 10 per page,
            "sort": "date",  # Sort by date
            "dateRestrict": f"m[{time_range_months}]",  # Restrict to the last year,
            "start": start_result_index,  # Start from the specified index
        }
        bq_df = pd.DataFrame()
        res = requests.get(url, params=params)
        results = res.json()

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in results.get("items", []):
            print(f"Processing article: {item['title']}")
            try:
                art_dict = parse_articles(item)
                filename = generate_article_filename(art_dict)
                buffer = json.dumps(art_dict)

                blob_name = upload_json_to_bucket(
                    project_id, "power-project-data", filename, buffer
                )
                row = generate_row(art_dict, blob_name)
                bq_df = pd.concat([bq_df, pd.DataFrame([row])], ignore_index=True)
            except Exception as e:
                logging.error(f"Error processing article: {item['title']}")
                print(traceback.format_exc(2))
            time.sleep(3)

        if len(bq_df) > 0:
            logging.info(f"Writing {len(bq_df)} Records to BigQuery.")
            bq_df["time_scraped"] = current_timestamp

            # Write to BigQuery
            merge_df_to_bq(bq_df, "articles", project_id, "energy_news")

        start_result_index += num_articles


if __name__ == "__main__":
    if len(sys.argv) > 1:
        num_articles = int(sys.argv[1])
    else:
        num_articles = 10
    if len(sys.argv) > 2:
        time_range_months = int(sys.argv[2])
    else:
        time_range_months = 1
    if len(sys.argv) > 3:
        start_result_index = int(sys.argv[3])
    else:
        start_result_index = 0

    main(
        num_articles=num_articles,
        time_range_months=time_range_months,
        start_result_index=start_result_index,
    )
