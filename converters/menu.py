"""Ensure new primary menu is up-to-date"""

from dataclasses import dataclass, asdict

import wpalchemy.classes as wp

from converters.converter import Converter


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
        for key, value in asdict(meta_args).items():
            # Create the post meta object
            manager.session.add(wp.PostMeta(
                post_id=post_id,
                meta_key="_menu_item_{}".format(key),
                meta_value=value))


class MenuItem:
    def __init__(self, manager, title: str, order: int, meta_args: MenuItemMetaArgs):
        # Create the menu Item
        post = manager.create_post(
            post_title=title,
            post_type="nav_menu_item",
            post_content='',
            post_excerpt='',
            menu_order=order)

        # Create the meta data
        MenuItemMeta(manager, post.ID, meta_args)


class MenuConverter(Converter):
    def convert(self):
        # Delete all nav menu posts (we are replacing them completely)
        self.source.session.query(wp.Post).filter_by(
            post_type='nav_menu_item').delete()

        # Get about page
        about_page = self.source.session.query(wp.Post).filter_by(
            post_type='page',
            post_name='about-us',
            post_status='publish').one()

        # Create the new menu items
        MenuItem(
            manager=self.source,
            title="About",
            order=1,
            meta_args=PageMenuItemMetaArgs(object_id=about_page.ID))
        MenuItem(
            manager=self.source,
            title="Articles",
            order=2,
            meta_args=CustomMenuItemMetaArgs(url="/articles"))
        MenuItem(
            manager=self.source,
            title="Events",
            order=3,
            meta_args=CustomMenuItemMetaArgs(url="/events"))
        MenuItem(
            manager=self.source,
            title="Shop",
            order=4,
            meta_args=CustomMenuItemMetaArgs(url="/shop"))
