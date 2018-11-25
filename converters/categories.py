import logging

import wpalchemy.classes as wp
from sqlalchemy import or_

from converters.converter import Converter
from converters.helpers import kebabify


logger = logging.getLogger(__name__)


NEW_CATEGORIES = {
    "Policy": [2361, 2311, 1990],
    "Activism": [2402, 2376, 1928],
    "Art": [2724, 2430, ],
    "People": [2301, 2275, 2189, 1979],
}
CATEGORY_TAXONOMY = "category"


class CategoriesConverter(Converter):
    def convert(self):
        # Get all categories and associated enhanced category
        query = self.source.session.query(wp.Term).filter_by(
            taxonomy=CATEGORY_TAXONOMY)

        # Copy the relevant information over
        for category in query:
            # No sub-categories
            category.parent = 0
            # Make all category names titlecase
            category.name = category.name.title()

        # Add new categories
        for category, post_ids in NEW_CATEGORIES.items():
            # Create the new category
            cat_obj = wp.Term(
                taxonomy=CATEGORY_TAXONOMY,
                name=category,
                slug=kebabify(category))
            self.source.session.add(cat_obj)
            # Add category to posts
            posts = self.source.session.query(wp.Post).filter(
                or_(*[wp.Post.ID == id for id in post_ids])).all()
            cat_obj.posts.extend(posts)
