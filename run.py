from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import argparse

def main():
    parser = argparse.ArgumentParser(description='Hybrid E-commerce Crawler')
    parser.add_argument('--domains', help='Comma-separated list of domains')
    parser.add_argument('--js-domains', help='Comma-separated list of domains requiring JavaScript')
    
    args = parser.parse_args()
    
    settings = get_project_settings()
    
    process = CrawlerProcess(settings)
    process.crawl('hybrid_spider', 
                 domains=args.domains,
                 js_domains=args.js_domains)
    process.start()

if __name__ == '__main__':
    main()