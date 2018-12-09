import logging

import wpalchemy.classes as wp
from sqlalchemy import or_

from converters.converter import Converter
from converters.helpers import kebabify


logger = logging.getLogger(__name__)


NEW_CATEGORIES = {
    "Policy": [2361, 2311, 1990, 2606],
    "Activism": [1928, 2376, 2402, 2512, 2578, 2614, 2627, 2680],
    "Art": [2430, 2489, 2674, 2724, 2872, 2896],
    "People": [1979, 2189, 2275, 2301, 2321, 2393, 2420, 2653, 2736, 2752, 2763, 2910, 2925],
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
