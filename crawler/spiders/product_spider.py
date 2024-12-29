# spiders/hybrid_spider.py
import scrapy
from scrapy_playwright.page import PageMethod
import tldextract
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs, urlencode
from bloom_filter2 import BloomFilter
import xxhash
from typing import Set, List, Optional
import asyncio

class HybridEcommerceSpider(scrapy.Spider):
    name = 'hybrid_spider'
    
    def should_abort_request(request):
        """Filter out unnecessary resource loads"""
        blocked_resources = {'image', 'stylesheet', 'font', 'media', 'other'}
        if request.resource_type in blocked_resources:
            return True

        blocked_patterns = [
            r'google-analytics', r'doubleclick', r'facebook\.com',
            r'analytics', r'tracker', r'advert', r'pixel',
            r'marketing'
        ]
        return any(re.search(pattern, request.url, re.IGNORECASE) 
                  for pattern in blocked_patterns)

    custom_settings = {
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 20000,
        },
        "PLAYWRIGHT_ABORT_REQUEST": should_abort_request
    }

    def __init__(self, domains: str = None, js_domains: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.domains: List[str] = domains.split(',') if domains else []
        self.js_domains: Set[str] = set(js_domains.split(',') if js_domains else [])
        self.domains.extend(list(self.js_domains))
        self.setup_url_patterns()
        
        # Initialize Bloom filter for efficient URL tracking
        self.bloom_filter = BloomFilter(max_elements=1000000, error_rate=0.001)
        self.visited_urls: Set[str] = set()
        self.product_urls: Set[str] = set()

    def setup_url_patterns(self) -> None:
        """Initialize URL pattern lists"""
        self.product_patterns: List[str] = [
            # Common path patterns
            r'/product[s]?/', r'/item[s]?/', r'/p/', r'pdp/',
            r'/shop/', r'product_id=', r'sku=',
            
            # ID-based patterns
            r'/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+-p-\d+',
            r'/product[_-]id[_-]?\d+',
            r'/item[_-]id[_-]?\d+',
            r'/prod\d+',
            r'/pid[_-]?\d+',
            
            # Platform-specific patterns
            r'/catalog/product/view/id/\d+',  # Magento
            r'/products/[\w-]+$',  # Shopify
            r'/shop/[\w-]+/[\w-]+$',  # WooCommerce
        ]
        
        self.ignore_patterns: List[str] = [
            # Navigation pages
            r'/category/', r'/search\?', r'sort=', r'page=',
            r'/department', r'/catalog/', r'/brand/',
            
            # Shopping functions
            r'/cart/', r'/checkout/', r'/basket/',
            r'/shopping-bag/', r'/payment/',
            
            # User pages
            r'/account/', r'/login', r'/register',
            r'/wishlist', r'/favorites',
            
            # Support pages
            r'/contact', r'/support', r'/help', r'/faq',
            
        ]

    def normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates"""
        try:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            important_params = {'product_id', 'sku', 'item', 'pid'}
            filtered_query = {k: v[0] if v else '' for k, v in query.items() 
                            if k in important_params}
            
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if filtered_query:
                normalized += f"?{urlencode(filtered_query)}"
            return normalized.rstrip('/')
        except Exception as e:
            self.logger.error(f"Error normalizing URL {url}: {e}")
            return url

    def url_seen(self, url: str) -> bool:
        """Check if URL has been seen using Bloom filter"""
        try:
            normalized = self.normalize_url(url)
            url_hash = xxhash.xxh64(normalized).hexdigest()
            
            if url_hash in self.bloom_filter:
                return url_hash in self.visited_urls
                
            self.bloom_filter.add(url_hash)
            self.visited_urls.add(url_hash)
            return False
        except Exception as e:
            self.logger.error(f"Error checking URL {url}: {e}")
            return True

    def start_requests(self):
        """Start crawling from specified domains"""
        for domain in self.domains:
            url = f'https://{domain}'
            yield self.create_request(url, domain)

    def create_request(self, url: str, domain: str):
        """Create appropriate request based on domain type"""
        if domain in self.js_domains:
            return scrapy.Request(
                url,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'networkidle'),
                        PageMethod('evaluate', 'window.scrollTo(0, document.body.scrollHeight)'),
                        PageMethod('wait_for_timeout', 2000),
                    ],
                    'playwright_context_kwargs': {
                        'ignore_https_errors': True
                    },
                    'domain': domain,
                    'handle_httpstatus_list': [404, 403, 429]
                },
                callback=self.parse_js,
                errback=self.errback,
            )
        else:
            return scrapy.Request(
                url,
                meta={'domain': domain},
                callback=self.parse_static,
            )

    async def parse_js(self, response):
        """Parse JavaScript-rendered pages"""
        page = response.meta["playwright_page"]
        try:
            self.logger.info(f"Starting to parse JS page: {response.url}")
            await self.handle_infinite_scroll(page)
            content = await page.content()
            async for link in self.extract_links(response, content):
                yield link
        except Exception as e:
            self.logger.error(f"Error parsing JS page {response.url}: {e}")
        finally:
            if page:
                await page.close()

    async def handle_infinite_scroll(self, page):
        """Handle infinite scroll pages"""
        try:
            last_height = await page.evaluate('document.body.scrollHeight')
            scroll_attempts = 0
            max_scrolls = 3
            
            while scroll_attempts < max_scrolls:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)
                
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                
        except Exception as e:
            self.logger.error(f"Error during infinite scroll: {e}")

    def parse_static(self, response):
        """Parse static HTML pages"""
        return self.extract_links(response)

    async def extract_links(self, response, content=None):
        """Extract and process links from the page"""
        seen_links: Set[str] = set()
        try:
            links = self.get_links(response, content)
            
            for link in links:
                absolute_url = response.urljoin(link)
                link_domain = tldextract.extract(absolute_url).registered_domain

                if link_domain not in self.domains:
                    continue

                if absolute_url in seen_links or self.url_seen(absolute_url):
                    continue
                    
                seen_links.add(absolute_url)
                
                if self.should_follow(absolute_url):
                    yield self.create_request(absolute_url, link_domain)
                
                if self.is_product_url(absolute_url):
                    if absolute_url not in self.product_urls:
                        self.product_urls.add(absolute_url)
                        yield {
                            'domain': response.meta['domain'],
                            'url': absolute_url,
                            'discovered_time': datetime.now().isoformat()
                        }
        except Exception as e:
            self.logger.error(f"Error extracting links from {response.url}: {e}")

    def get_links(self, response, content=None):
        """Extract links from response or content"""
        try:
            if content:
                return scrapy.Selector(text=content).css('a::attr(href)').getall()
            return response.css('a::attr(href)').getall()
        except Exception as e:
            self.logger.error(f"Error getting links: {e}")
            return []

    def is_product_url(self, url: str) -> bool:
        """Check if URL is a product page"""
        try:
            return any(re.search(pattern, url, re.IGNORECASE) 
                      for pattern in self.product_patterns) and \
                   not any(re.search(pattern, url, re.IGNORECASE) 
                          for pattern in self.ignore_patterns)
        except Exception as e:
            self.logger.error(f"Error checking product URL {url}: {e}")
            return False

    def should_follow(self, url: str) -> bool:
        """Check if URL should be followed"""
        try:
            domain = tldextract.extract(url).registered_domain
            return domain in self.domains and not self.is_product_url(url)
        except Exception as e:
            self.logger.error(f"Error checking follow URL {url}: {e}")
            return False

    async def errback(self, failure):
        """Handle request failures"""
        self.logger.error(repr(failure))
        page = failure.request.meta.get("playwright_page")
        if page:
            self.logger.info("Closing page due to error")
            asyncio.create_task(page.close())