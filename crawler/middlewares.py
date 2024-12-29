from scrapy import signals
from typing import Optional, List
import random
import tldextract
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy_playwright.handler import ScrapyPlaywrightDownloadHandler
from scrapy.http import Request
from scrapy.utils.defer import deferred_from_coro


class CustomUserAgentMiddleware(UserAgentMiddleware):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101'
    ]

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.user_agents)

