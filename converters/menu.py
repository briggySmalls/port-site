"""Ensure new primary menu is up-to-date"""

from dataclasses import dataclass, asdict

import wpalchemy.classes as wp
from sqlalchemy import or_

from converters.converter import Converter
from converters.helpers import create_post_meta, create_post, Page, kebabify, find_or_create_term


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

        # Create home page
        self.source.session.query(wp.Post).filter_by(post_title='Articles').delete()
        home_page = Page(
            self.source,
            title="Articles",
            template="views/widget-page.blade.php")

        # Create articles archive
        self.source.session.query(wp.Post).filter_by(post_title='Latest articles').delete()
        latest_articles = Page(
            self.source,
            title="Latest articles",
            name="latest")

        # Update the home page setting (NOTE: In target settings)
        self.target.session.query(wp.Option).filter_by(
            option_name='page_on_front').update(
                {wp.Option.option_value: home_page.object.ID})

        # Update the articles page setting (NOTE: In target settings)
        self.target.session.query(wp.Option).filter_by(
            option_name="page_for_posts").update(
                {wp.Option.option_value: latest_articles.object.ID})

        # Create the new menu items
        items = [
            MenuItem(
                manager=self.source,
                title="Articles",
                order=1,
                meta_args=PageMenuItemMetaArgs(object_id=home_page.object.ID)),
            MenuItem(
                manager=self.source,
                title="Events",
                order=2,
                meta_args=ArchiveMenuItemMetaArgs(object="sd-event")),
            MenuItem(
                manager=self.source,
                title="Shop",
                order=3,
                meta_args=ArchiveMenuItemMetaArgs(object="sd-product")),
        ]

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

    def _find_or_create_nav(self, name):
        return find_or_create_term(
            manager=self.source,
            name=name,
            slug=kebabify(name),
            description='',
            taxonomy="nav_menu")
