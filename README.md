# Crawley
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

Crawley is an asynchronous **web crawling** and **web request** Python library.
## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Code Coverage](#code-coverage)
- [Contact Me](#contact-me)

## Features
- Supports retrieving/crawling dynamic webpages with **[Playwright](https://playwright.dev/python/) browser automation**.
- Supports *optional* **polite web crawling** by following robots.txt instructions.
- Supports **crawling sitemaps** to retrieve urls. Caches sitemaps to prevent redundant requests.
- Doesn't consume much memory when making multiple requests by using an asynchronous generator. Responses are returned as soon as they occur.
- Performant browser automation by reusing idle browser windows.
- Closing of resources is easy because the request clients and crawlers are async context managers.
- Supports crawling timeout. 
- Supports **logging** of requests.
- Significant test coverage.

## Installation
1. Clone the repository.
````commandline
git clone https://github.com/adamoregan/crawley.git
````
2. Download the dependencies.
````commandline
cd crawley
pip install -r requirements.txt
````

## Usage
````python
import asyncio
from crawley.crawling import Crawler

async def main():
    async with Crawler() as crawler:
      urls = await crawler.crawl(["https://www.python.org/"], 100)
      for url in urls:
          print(url)

asyncio.run(main())
````
``.crawl`` will return 100 discovered urls, staring from "https://www.python.org". The crawler can be used as an async
context manager to automatically close the web client used to make requests. The crawler gets static webpages by 
default, this can be changed by passing the DynamicRequestClient to it.
````python
import asyncio
from playwright.async_api import async_playwright

from crawley.crawling import Crawler
from crawley.web_requests import DynamicRequestClient

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        client = DynamicRequestClient(browser)
        async with Crawler(client) as crawler:
          urls = await crawler.crawl(["https://www.python.org/"], 100)
          for url in urls:
              print(url)
asyncio.run(main())
````
`.crawl` now automates a Chrome browser to render dynamic webpages. This allows it to find more urls.

## Code Coverage
````commandline
cd crawley
coverage run -m unittest 
coverage report -m
````
Runs all the unit tests in the library and generates a report. Run `coverage report html` to output the report to a 
HTML file.

## Contact Me
- Adam O'Regan 
  - Github: [adamoregan](https://github.com/adamoregan)  
  - Email: [adamoregan457@gmail.com](mailto:adamoregan457@gmail.com)
  - LinkedIn: [adamoregan457](https://www.linkedin.com/in/adamoregan457)
