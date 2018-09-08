import logging

import wpalchemy.classes as wp
from sqlalchemy.sql.expression import func

from converters.converter import Converter


logger = logging.getLogger(__name__)


class AuthorsConverter(Converter):
    def convert(self):
        # First split up any dual-authored values
        self._split_authors()
        # Add authors as terms, with associated posts
        new_terms = []
        current_term = None
        for author in self.source.session.query(wp.PostMeta).filter_by(
                meta_key='author').order_by(wp.PostMeta.meta_value):
            # Ensure we have a term for the current author
            if current_term is None or current_term.name != author.meta_value:
                if current_term is not None:
                    # Add the previously built term
                    new_terms.append(current_term)
                # Create a new term for this new author
                current_term = wp.Term(
                    name=author.meta_value,
                    slug=self.source.kebabify(author.meta_value),
                    term_group=0,
                    taxonomy='sd-author')

            # Add the post for the current term
            current_term.posts.append(author.post)

            # Remove the author
            self.source.session.delete(author)

        # TODO: Set author count
        # seems to be necessary for "choose from most used authors" option

        # Add new terms
        self.source.session.add_all(new_terms)

    def _split_authors(self):
        """Finds all posts with multiple authors and splits them out

        Args:
            manager (DbManager): Manager for the SQL connection
        """
        # Find all author fields with more than one author
        multi_authors = self.source.session.query(wp.PostMeta).filter(
            wp.PostMeta.meta_key == 'author',
            wp.PostMeta.meta_value.contains('&'))  # Has an ampersand in string

        # Process each multi-author
        new_authors = []
        for entry in multi_authors:
            # Extract the authors from the entry
            author_names = entry.meta_value.split(' & ')
            # Update the current author with just the first
            for i, author_name in enumerate(author_names):
                if i == 1:
                    # Update the first author
                    entry.meta_value = author_name
                else:
                    # Create a new author
                    new_author = wp.PostMeta(
                        meta_key=entry.meta_key,  # Copy the key ('author')
                        meta_value=author_name)  # Use the separated name
                    new_author.post_id = entry.post_id  # Link to the same post
                    new_authors.append(new_author)

        # Trim all whitespace
        self.source.session.query(wp.PostMeta).filter_by(
            meta_key='author').update(
                {wp.PostMeta.meta_value: func.ltrim(func.rtrim(wp.PostMeta.meta_value))},
                synchronize_session='fetch')

        # Push the updates
        self.source.session.add_all(new_authors)
