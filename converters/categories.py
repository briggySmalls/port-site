import logging

import wpalchemy.classes as wp

from converters.converter import Converter
from converters.helpers import get_meta, create_acf_meta


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
            create_acf_meta(
                self.source,
                wp.TermMeta,
                category.term_id,
                enhanced.post_content,
                "sd_article_category_description",
                "field_5b9e965fc63bf")

            try:
                # Copy the image
                image_id = get_meta(enhanced, "_thumbnail_id")
                create_acf_meta(
                    self.source,
                    wp.TermMeta,
                    category.term_id,
                    image_id,
                    "sd_article_category_image",
                    "field_5b54457baf086")
            except RuntimeError:
                # No image found
                pass

            # Make all category names titlecase
            category.name = category.name.title()
