"""Ensure home and articles page are present"""
import wpalchemy.classes as wp

from converters.converter import Converter


class Page:
    def __init__(self, manager, title, template=None):
        # Create the page
        self._page = manager.create_post(
            post_type="page",
            post_content='',
            post_excerpt='',
            post_title=title)
        # Set the template (if necessary)
        if template:
            manager.session.add(wp.PostMeta(
                post_id=self._page.ID,
                meta_key="_wp_page_template",
                meta_value=template))

    @property
    def object(self):
        return self._page


class PagesConverter(Converter):
    def convert(self):
        # Create home page
        home_page = Page(
            self.source,
            title="Home",
            template="views/widget-page.blade.php")
        # Update the home page setting
        self.target.session.query(wp.Option).filter_by(
            option_name="page_on_front").update(
                {wp.Option.option_value: home_page.object.ID})

        # Create articles page
        articles_page = Page(self.source, title="Articles")
        # Update the articles page setting
        self.target.session.query(wp.Option).filter_by(
            option_name="page_for_posts").update(
                {wp.Option.option_value: articles_page.object.ID})
