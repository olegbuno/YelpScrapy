import argparse
import re
from urllib.parse import unquote_plus
from urllib.parse import urlencode

import scrapy
from scrapy.crawler import CrawlerProcess


class YelpSpider(scrapy.Spider):
    name = 'yelp_spider'
    allowed_domains = ['yelp.com']
    base_url = 'https://www.yelp.com'

    def __init__(self, *args, **kwargs):
        super(YelpSpider, self).__init__(*args, **kwargs)
        self.category = kwargs.get('category')
        self.location = kwargs.get('location')
        self.limit_pages = 1

    def start_requests(self):
        params = {'find_desc': self.category, 'find_loc': self.location}
        url = f'{self.base_url}/search?{urlencode(params)}'

        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response, **kwargs):
        businesses = response.xpath('//div[contains(@class, "toggle__09f24__fZMQ4")]')

        for business in businesses:
            name = business.xpath('.//a[contains(@class, "css-19v1rkv")]/text()').get()
            rating = business.xpath('.//span[contains(@class, "css-gutk1c")]/text()').get()

            reviews_str = business.xpath('.//span[contains(@class, "css-chan6m")]/text()').get()
            reviews_match = re.search(r'(\d+)', reviews_str)
            num_reviews = reviews_match.group(1) if reviews_match else 0

            yelp_url = business.css('a.css-1jrzyc::attr(href)').get()
            yelp_url = response.urljoin(yelp_url)

            yield scrapy.Request(yelp_url, callback=self.parse_business_page,
                                 meta={
                                     'name': name,
                                     'rating': rating,
                                     'num_reviews': num_reviews,
                                     'yelp_url': yelp_url
                                 })

        # Check if we need to continue to the next page
        next_page = response.css('a.next-link::attr(href)').get()
        if next_page and self.limit_pages > 1:
            self.limit_pages -= 1
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_business_page(self, response):
        name = response.meta.get('name')
        rating = response.meta.get('rating')
        num_reviews = response.meta.get('num_reviews')
        yelp_url = response.meta.get('yelp_url')

        website_href = response.xpath(
            './/p[contains(@class, "css-1p9ibgf")]//a[contains(@class, "css-1idmmu3")]/@href').get()
        decoded_url = unquote_plus(website_href) if website_href else ""  # Decode the URL

        website = ""
        if decoded_url:
            domain_match = re.search(r'https?://([^/?&]+)', decoded_url)  # Extract the domain
            website = domain_match.group(1).split("&")[0] if domain_match else ""

        item = {
            'name': name,
            'rating': rating,
            'num_reviews': num_reviews,
            'yelp_url': yelp_url,
            'website': website
        }

        review_block = response.xpath('.//div[@id="reviews"]//li[contains(@class, "css-1q2nwpv")]')
        item['reviews'] = []
        for review in review_block[:5]:
            reviewer_name = review.xpath('.//a[contains(@class, "css-19v1rkv")]/text()').get()
            reviewer_location = review.xpath('.//span[contains(@class, "css-qgunke")]/text()').get()
            review_date = review.xpath('.//span[contains(@class, "css-chan6m")]/text()').get()

            review_item = {
                'reviewer_name': reviewer_name,
                'reviewer_location': reviewer_location,
                'review_date': review_date
            }
            item['reviews'].append(review_item)

        yield item


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Yelp Spider')
    parser.add_argument('--category', help='Category for Yelp search', required=True)
    parser.add_argument('--location', help='Location for Yelp search', required=True)
    args = parser.parse_args()

    category = args.category
    location = args.location
    output_file = 'yelp_data.json'

    process = CrawlerProcess(settings={
        'FEEDS': {
            output_file: {'format': 'json', 'overwrite': True},
        },
    })
    process.crawl(YelpSpider, category=category, location=location)
    process.start()
