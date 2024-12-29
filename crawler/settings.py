BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'
LOG_LEVEL = 'INFO'
# Scrapy-Playwright settings
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Custom settings
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 32
DOWNLOAD_DELAY = 0.1
COOKIES_ENABLED = False
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.CustomUserAgentMiddleware': 400,
}

# Enable or disable item pipelines
ITEM_PIPELINES = {
    'crawler.pipelines.DuplicateURLFilterPipeline': 100,
    'crawler.pipelines.MultiFormatExportPipeline': 200,
}