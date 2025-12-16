"""
DumbCrawler Scrapy Middlewares

This module contains custom Scrapy middlewares for the DumbCrawler project.
"""


class PlaywrightStealthMiddleware:
    """Middleware to inject stealth scripts into Playwright pages."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    async def process_request(self, request, spider):
        """Inject stealth JavaScript before page loads."""
        if request.meta.get("playwright"):
            # JavaScript to hide automation indicators
            stealth_js = """
                // Overwrite the `navigator.webdriver` property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Overwrite the `plugins` property to use a fake PluginArray
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Overwrite the `languages` property
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Pass the Chrome Test
                window.chrome = {
                    runtime: {}
                };

                // Pass the Permissions Test
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Remove automation indicators
                delete navigator.__proto__.webdriver;
            """

            # Add init script to page
            if "playwright_page_init_callback" not in request.meta:
                async def init_page(page, request):
                    await page.add_init_script(stealth_js)

                request.meta["playwright_page_init_callback"] = init_page

        return None
