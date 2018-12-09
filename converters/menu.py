"""Ensure new primary menu is up-to-date"""

from dataclasses import dataclass, asdict

import wpalchemy.classes as wp
from sqlalchemy import or_

from converters.converter import Converter
from converters.helpers import create_post_meta, create_post, Page, kebabify, find_or_create_term

_HOME_PAGE_CONTENT = """
<!-- wp:acf/slider {"id":"block_5bfa9dc5d1f35","data":{"field_5b5a4fff2b3c6":["2669","2211","2189","2775"]},"name":"acf/slider","mode":"preview"} /-->

<!-- wp:acf/preview {"id":"block_5bfa9e9dd1f36","data":{"field_5b14795f2eb5b":"Latest articles","field_5bf49eba5ef9a":"post","field_5b35735273ab3":{"field_5b3573fc73ab6":"all"},"field_5b317fba7ce75":"3","field_5b3575ce73ab7":"6"},"name":"acf/preview","mode":"preview"} /-->

<!-- wp:acf/preview {"id":"block_5bfa9eb4d1f37","data":{"field_5b14795f2eb5b":"Videos","field_5bf49eba5ef9a":"post","field_5b35735273ab3":{"field_5b3573fc73ab6":"format","field_5b1478f22eb5a":"109"},"field_5b317fba7ce75":"2","field_5b3575ce73ab7":"4"},"name":"acf/preview","mode":"preview"} /-->
"""

_EVENTS_PAGE_CONTENT = """
<!-- wp:acf/preview {"id":"block_5bfa9f095e6e8","data":{"field_5b14795f2eb5b":"Upcoming","field_5bf49eba5ef9a":"sd-event","field_5bf49f6d5ef9b":{"field_5bf49f9c5ef9c":"status","field_5bf4a0f85ef9d":"upcoming"},"field_5b317fba7ce75":"2","field_5b3575ce73ab7":"1"},"name":"acf/preview","mode":"preview"} /-->

<!-- wp:acf/preview {"id":"block_5bfa9f195e6e9","data":{"field_5b14795f2eb5b":"Past","field_5bf49eba5ef9a":"sd-event","field_5bf49f6d5ef9b":{"field_5bf49f9c5ef9c":"status","field_5bf4a0f85ef9d":"past"},"field_5b317fba7ce75":"3","field_5b3575ce73ab7":"6"},"name":"acf/preview","mode":"preview"} /-->
"""


@dataclass
class MenuItemMetaArgs:
    type: str = ''
    object_id: int = 0
    object: str = ''
    target: str = ''
    classes: str = 'a:1:{i:0;s:0:"";}'
    xfn: str = ''
    url: str = ''
    menu_item_parent: int = 0

    def update(self, post_id):
        pass


@dataclass
class PageMenuItemMetaArgs(MenuItemMetaArgs):
    type: str = "post_type"
    object: str = "page"


@dataclass
class CustomMenuItemMetaArgs(MenuItemMetaArgs):
    type: str = "custom"
    object: str = "custom"

    def update(self, post_id):
        self.object_id = post_id


@dataclass
class ArchiveMenuItemMetaArgs(MenuItemMetaArgs):
    type: str = "post_type_archive"


@dataclass
class CategoryMenuItemMetaArgs(MenuItemMetaArgs):
    type: str = "taxonomy"
    object: str = "category"


@dataclass
class FormatMenuItemMetaArgs(MenuItemMetaArgs):
    type: str = "taxonomy"
    object: str = "post_format"


class MenuItemMeta:
    def __init__(self, manager, post_id: int, meta_args: MenuItemMetaArgs):
        # Give the args a chance to update based on post_id
        meta_args.update(post_id)
        # Create a post meta for every arg
        data = {
            "_menu_item_{}".format(key): value for
            key, value in
            asdict(meta_args).items()
        }
        create_post_meta(manager.session, post_id, data)


class MenuItem:
    def __init__(self, manager, title: str, order: int, meta_args: MenuItemMetaArgs):
        # Create the menu Item
        self._post = create_post(
            manager,
            post_title=title,
            post_type="nav_menu_item",
            post_content='',
            post_excerpt='',
            menu_order=order)

        # Create the meta data
        MenuItemMeta(manager, self._post.ID, meta_args)

    @property
    def post(self):
        return self._post


class Counter:
    def __init__(self, start_value):
        self._value = start_value

    def next(self):
        value = self._value
        self._value += 1
        return value


class MenuConverter(Converter):
    def convert(self):
        # Delete all menus (we are replacing them completely)
        self.source.session.query(wp.Term).filter_by(
            taxonomy='nav_menu')
        # Delete all nav menu posts (we are replacing them completely)
        self.source.session.query(wp.Post).filter_by(
            post_type='nav_menu_item').delete()

        # Create main menu
        self.main_menu()

        # Create footer menu
        self.footer_menu()

    def main_menu(self):
        # Remove all the nav menu term relationships
        main_menu_term = self._find_or_create_nav(name="Main Menu")
        main_menu_term.posts = []

        # Create new pages for the menu
        home_page, latest_articles, events_page = self.create_menu_pages()

        # Create top-level article menu item
        menu_index = Counter(1)
        items = []
        articles_menu_item = MenuItem(
            manager=self.source,
            title="Articles",
            order=menu_index.next(),
            meta_args=PageMenuItemMetaArgs(object_id=home_page.object.ID))
        items.append(articles_menu_item)

        # Create sub-articles menu items
        items.extend([
            MenuItem(
                manager=self.source,
                title=category_name,
                order=menu_index.next(),
                meta_args=CategoryMenuItemMetaArgs(
                    menu_item_parent=articles_menu_item.post.ID,
                    object_id=self.source.session.query(
                        wp.Term.term_id).filter_by(name=category_name).scalar())) for
            category_name in [
                "Skin Deep Meets",
                "Back To Basics",
                "Art",
                "Activism",
                "Policy",
                "People"
            ]
        ])

        items.append(MenuItem(
            manager=self.source,
            title="Video",
            order=menu_index.next(),
            meta_args=FormatMenuItemMetaArgs(
                menu_item_parent=articles_menu_item.post.ID,
                object_id=self.source.session.query(
                    wp.Term.term_id).filter_by(name="post-format-video").scalar())))

        # Create events menu
        events_menu_item = MenuItem(
            manager=self.source,
            title="Events",
            order=menu_index.next(),
            meta_args=PageMenuItemMetaArgs(object_id=events_page.object.ID))
        items.append(events_menu_item)

        # Create the new menu items
        items.extend([
            MenuItem(
                manager=self.source,
                title="Upcoming",
                order=menu_index.next(),
                meta_args=CustomMenuItemMetaArgs(
                    url="/events/status/upcoming",
                    menu_item_parent=events_menu_item.post.ID)),
            MenuItem(
                manager=self.source,
                title="Past",
                order=menu_index.next(),
                meta_args=CustomMenuItemMetaArgs(
                    url="/events/status/past",
                    menu_item_parent=events_menu_item.post.ID)),
            MenuItem(
                manager=self.source,
                title="Shop",
                order=menu_index.next(),
                meta_args=ArchiveMenuItemMetaArgs(object="sd-product")),
        ])

        # Associate the posts with the main menu term
        main_menu_term.posts.extend([item.post for item in items])

    def footer_menu(self):
        # Create footer menu
        footer_term = self._find_or_create_nav("Footer Menu")

        # Search for posts to add to footer menu
        post_names = [
            'about-us',
            'submissions',
            'email-contacts',
            'donate',
        ]
        posts = self.source.session.query(wp.Post).filter(
            or_(*[wp.Post.post_name == name for name in post_names]))
        assert posts.count() == len(post_names), (
            "Not all posts found for footer menu")

        # Create the new menu items
        items = [
            MenuItem(
                manager=self.source,
                title=post.post_title,
                order=1,
                meta_args=PageMenuItemMetaArgs(object_id=post.ID)) for post in posts]

        # Add posts to menu
        footer_term.posts.extend([item.post for item in items])

    def create_menu_pages(self):
        # Create home page
        self.source.session.query(wp.Post).filter_by(post_title='Articles').delete()
        home_page = Page(
            self.source,
            title="Articles",
            content=_HOME_PAGE_CONTENT)

        # Create articles archive
        self.source.session.query(wp.Post).filter_by(post_title='Latest articles').delete()
        latest_articles = Page(
            self.source,
            title="Latest articles",
            name="latest")

        # Create events page
        events_page = Page(
            self.source,
            title="Events",
            content=_EVENTS_PAGE_CONTENT)

        # Update the home page setting (NOTE: In target settings)
        self.target.session.query(wp.Option).filter_by(
            option_name='page_on_front').update(
                {wp.Option.option_value: home_page.object.ID})

        # Update the articles page setting (NOTE: In target settings)
        self.target.session.query(wp.Option).filter_by(
            option_name="page_for_posts").update(
                {wp.Option.option_value: latest_articles.object.ID})

        return home_page, latest_articles, events_page

    def _find_or_create_nav(self, name):
        return find_or_create_term(
            manager=self.source,
            name=name,
            slug=kebabify(name),
            description='',
            taxonomy="nav_menu")
