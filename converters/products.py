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

        # Rename product categories
        self.source.session.query(wp.Term).filter_by(
            slug="print-magazines").update(
                {
                    wp.Term.slug: "magazines",
                    wp.Term.name: "Magazines",
                })
        # TODO: Delete digital-magazines

        # Copy details from ithemes exchange
        for product in self.source.session.query(wp.Post).filter_by(post_type="sd-product"):
            # Copy description
            description = get_meta(product, "_it-exchange-product-description")
            product.post_content = description

            # Extract meta-data
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
            out_of_stock = (
                get_meta(product, "_it-exchange-product-enable-inventory") == "yes" and
                int(get_meta(product, "_it-exchange-product-inventory")) == 0)

            # Save new meta-data
            data = {
                "sd-product-price": price,
                "sd-product-subscription": 0 if is_subscription else 1,
                "sd-product-frequency": frequency,
                "sd_product_in_stock": 0 if out_of_stock else 1,
                "_thumbnail_id": image.group('id') if image else '',
            }
            create_post_meta(self.source.session, product.ID, data)
