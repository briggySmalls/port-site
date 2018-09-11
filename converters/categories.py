import logging

import wpalchemy.classes as wp

from converters.converter import Converter
from converters.helpers import get_meta


logger = logging.getLogger(__name__)


class CategoriesConverter(Converter):
    def convert(self):
        # Get all categories and associated enhanced category
        query = self.source.session.query(wp.Term, wp.Post).filter(
                wp.Post.post_type == 'enhancedcategory').filter(
                    wp.Term.slug == wp.Post.post_name)

        # Copy the relevant information over
        for category, enhanced in query:
            assert category.name == enhanced.post_title

            # Copy the description
            category.description = enhanced.post_content
            try:
                # Copy the image
                image_id = get_meta(enhanced, "_thumbnail_id")
                self.add_category_image(category.id, image_id)
            except RuntimeError:
                # No image found
                pass

    def add_category_image(self, category_id, image_id):
        # Add image metadata
        self.source.session.add(wp.TermMeta(
            term_id=category_id,
            meta_key="sd_article_category_image",
            meta_value=image_id))
        # Add the ACF metadata
        self.source.session.add(wp.TermMeta(
            term_id=category_id,
            meta_key="_sd_article_category_image",
            meta_value="field_5b54457baf086"))
