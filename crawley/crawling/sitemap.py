import logging
from itertools import islice

from usp.objects.sitemap import AbstractSitemap
from usp.tree import sitemap_tree_for_homepage

from crawley.crawling.util import get_homepage

# Silences gunzip warnings
logging.getLogger("usp.helpers").disabled = True


class SitemapCache(dict):
    """Defines a sitemap cache. Prevents domain sitemaps from being revisited."""

    def __init__(self, use_known_paths: bool = False):
        """
        Creates a sitemap cache.
        :param use_known_paths: Whether to discover sitemaps through common known paths.
        """
        super().__init__()
        self.use_known_paths = use_known_paths

    def _create_sitemap_tree(self, homepage: str):
        """
        Creates a sitemap tree and stores it in the cache.
        :param homepage: The homepage identifier for the cache.
        """
        self[homepage] = sitemap_tree_for_homepage(
            homepage, use_known_paths=self.use_known_paths
        )

    def _get_sitemap_tree(self, url: str) -> str:
        """
        Gets the desired sitemap tree from the cache. Creates the sitemap tree if
        not already in the cache.
        :param url: Any url belonging to a certain domain.
        :return: The homepage of the given url.
        """
        homepage = get_homepage(url)
        if homepage not in self:
            self._create_sitemap_tree(homepage)
        return homepage

    def get(self, __key) -> AbstractSitemap:
        """
        Gets the sitemap tree of a domain.
        :param __key: Any url belonging to a certain domain.
        :return: The sitemap of the domain of the given url.
        """
        return super().get(self._get_sitemap_tree(__key))

    def __getitem__(self, item) -> AbstractSitemap:
        """
        Gets the sitemap tree of a domain.
        :param item: Any url belonging to a certain domain.
        :return: The sitemap of the domain of the given url.
        """
        return super().__getitem__(self._get_sitemap_tree(item))

    @staticmethod
    def get_urls(tree: AbstractSitemap, max_urls: int = None):
        """
        Gets urls from a sitemap tree.
        :param tree: The tree to get the urls from.
        :param max_urls: The maximum amount of urls to retrieve.
        :return: Urls from the sitemap tree.
        """
        urls, pages = set(), tree.all_pages()
        if max_urls:
            pages = islice(pages, max_urls)
        for page in pages:
            urls.add(page.url)
        return urls
