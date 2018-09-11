import re

import wpalchemy.classes as wp
from sqlalchemy import and_

from converters.converter import Converter
from converters.helpers import get_meta, create_post_meta


class ProductsConverter(Converter):
    def convert(self):
        # Update post type of products
        self.source.session.query(wp.Post).filter_by(
            post_type='it_exchange_prod').update(
                {wp.Post.post_type: 'sd-product'},
                synchronize_session='fetch')

        # Remove all digital downloads (products with a parent)
        self.source.session.query(wp.Post).filter(
            wp.Post.post_type == 'sd-product').filter(
                wp.Post.post_parent != 0).delete()

        # Update product category
        self.source.session.query(wp.Term).filter_by(
            taxonomy='it_exchange_category').update(
                {wp.Term.taxonomy: 'sd-product-cat'})

        # Copy details from ithemes exchange
        for product in self.source.session.query(wp.Post).filter_by(post_type="sd-product"):
            # Copy description
            description = get_meta(product, "_it-exchange-product-description")
            product.post_content = description

            # Copy other meta-data
            price = int(get_meta(
                product, "_it-exchange-base-price")) / 100
            is_subscription = get_meta(
                product,
                "_it-exchange-product-recurring-enabled") == "off"
            frequency = get_meta(
                product,
                "_it-exchange-product-recurring-interval").title()
            image = re.match(
                r'a:1:{i:0;s:(\d+):"(?P<id>\d+)";}',
                get_meta(product, "_it-exchange-product-images"))
            data = {
                "sd-product-price": price,
                "sd-product-subscription": 0 if is_subscription else 1,
                "sd-product-frequency": frequency,
                "_thumbnail_id": image.group('id') if image else '',
            }
            create_post_meta(self.source.session, product.ID, data)
