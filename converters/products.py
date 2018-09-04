import wpalchemy.classes as wp

from converters.converter import Converter


class ProductsConverter(Converter):
    def convert(self):
        # Update post type of products
        self.session.query(wp.Post).filter_by(
            post_type='it_exchange_prod').update(
                {wp.Post.post_type: 'sd-product'},
                synchronize_session='fetch')

        # Update product category
        self.session.query(wp.Term).filter_by(
            taxonomy='it_exchange_category').update(
                {wp.Term.taxonomy: 'sd-product-cat'})
