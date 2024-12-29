# Hybrid E-commerce Crawler

This project is a hybrid e-commerce crawler built using Scrapy and Playwright. It is designed to scrape product URLs from various e-commerce websites, handling both static and JavaScript-rendered content.

## Features

- **Hybrid Crawling**: Supports both static and JavaScript-rendered pages using Playwright.
- **Customizable**: Allows specifying domains and JavaScript domains via command-line arguments.
- **Efficient URL Management**: Utilizes a Bloom filter to efficiently track visited URLs and avoid duplicates.
- **Flexible Export**: Exports discovered product URLs in multiple formats (JSON, CSV).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/justinjoy07/hybrid-ecommerce-crawler.git
   cd hybrid-ecommerce-crawler
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Playwright is installed and set up:
   ```bash
   playwright install
   ```

## Usage

Run the crawler with the following command:
   ```bash
   python run.py --domains example1.com,example2.com --js-domains js-example2.com,js-example2.com
   ```
- `--domains`: Comma-separated list of domains to crawl.
- `--js-domains`: Comma-separated list of domains that require JavaScript rendering.

## Configuration

The crawler's behavior can be customized through the `crawler/settings.py` file. Key settings include:

- `CONCURRENT_REQUESTS`: Number of concurrent requests.
- `DOWNLOAD_DELAY`: Delay between requests to the same domain.

## Approach to Finding "Product" URLs

The crawler identifies "product" URLs using specific patterns and filters. Here's a breakdown of the approach:

1. **URL Patterns**: The crawler uses predefined patterns to identify potential product URLs. These patterns are defined in the `setup_url_patterns` method of the `HybridSpider` class.


   - **Product Patterns**: Patterns that likely indicate a product page, such as `/product/`, `/item/`, `/p/`, etc.
   - **Ignore Patterns**: Patterns that should be ignored, such as `/category/`, `/cart/`, `/checkout/`, etc.

2. **Normalization**: URLs are normalized to ensure consistent comparison. This involves parsing the URL and filtering query parameters to retain only those relevant to products.

3. **Duplicate Filtering**: A Bloom filter is used to efficiently track and filter out duplicate URLs, ensuring each URL is processed only once.


4. **Link Extraction**: Links are extracted from the page content, and each link is checked against the product and ignore patterns. If a link matches a product pattern and does not match any ignore patterns, it is considered a product URL.

5. **Request Creation**: For each identified product URL, a request is created and added to the crawl queue. The request is configured to handle both static and JavaScript-rendered pages as needed.

