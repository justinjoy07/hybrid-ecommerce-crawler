import json
import csv
from datetime import datetime
from scrapy.exporters import JsonItemExporter, CsvItemExporter
from itemadapter import ItemAdapter
import pandas as pd
from pathlib import Path

class DuplicateURLFilterPipeline:
    def __init__(self):
        self.urls_seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter['url']
        
        if url in self.urls_seen:
            return None
            
        self.urls_seen.add(url)
        return item

class MultiFormatExportPipeline:
    def __init__(self):
        self.items = []
        self.export_formats = {'json', 'csv'}

    def process_item(self, item, spider):
        if item is None:
            return item
        self.items.append(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        # Export to JSON
        json_path = output_dir / f'products_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(self.items, f, indent=2)

        # Export to CSV
        csv_path = output_dir / f'products_{timestamp}.csv'
        df = pd.DataFrame(self.items)
        df.to_csv(csv_path, index=False)
