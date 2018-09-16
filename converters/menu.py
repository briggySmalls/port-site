"""Ensure new primary menu is up-to-date"""

from dataclasses import dataclass, asdict

import wpalchemy.classes as wp

from converters.converter import Converter
from converters.helpers import create_post_meta, create_post, Page, kebabify


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
        home_page = Page(
            self.source,
            title="Articles",
            template="views/widget-page.blade.php")
        # Update the home page setting (NOTE: In target settings)
        self.target.session.query(wp.Option).filter_by(
            option_name="page_on_front").update(
                {wp.Option.option_value: home_page.object.ID})

        # Get about page
        about_page = self.source.session.query(wp.Post).filter_by(
            post_type='page',
            post_name='about-us',
            post_status='publish').one()

        # Create the new menu items
        items = [
            MenuItem(
                manager=self.source,
                title="About",
                order=1,
                meta_args=PageMenuItemMetaArgs(object_id=about_page.ID)),
            MenuItem(
                manager=self.source,
                title="Articles",
                order=2,
                meta_args=PageMenuItemMetaArgs(object_id=home_page.object.ID)),
            MenuItem(
                manager=self.source,
                title="Events",
                order=3,
                meta_args=CustomMenuItemMetaArgs(url="/events")),
            MenuItem(
                manager=self.source,
                title="Shop",
                order=4,
                meta_args=CustomMenuItemMetaArgs(url="/products")),
        ]

        # Associate the posts with the main menu term
        for item in items:
            item.post.terms.append(main_menu_term)

    def footer_menu(self):
        # Create footer
        footer_term = self._find_or_create_nav("Footer Menu")
        # Add posts
        posts = [
            38,  # Donate

        ]
        for id in posts:
            post = self.source.session.query(wp.Post).filter_by(ID=id).one()
            post.terms.append(footer_term)


    def _find_or_create_nav(self, name):
        return self._find_or_create_term(
            name=name,
            slug=kebabify(name),
            description='',
            taxonomy="nav_menu")

    def _find_or_create_term(self, name, slug, description, taxonomy):
        # First try find it
        term = self.source.session.query(wp.Term).filter_by(
            slug=slug).first()
        if term:
            return term

        # Term doesn't exist, so make it
        return wp.Term(
            name=name,
            slug=slug,
            description=description,
            taxonomy=taxonomy)
