import logging

import wpalchemy.classes as wp
from sqlalchemy import func
from sqlalchemy.sql import collate

from converters.converter import Converter
from converters.helpers import kebabify


logger = logging.getLogger(__name__)


class AuthorsConverter(Converter):
    def convert(self):
        # First split up any dual-authored values
        self._split_authors()

        # Create an author for each unique author name
        # Note: We 'collate' to not group accented chars with non-accented
        unique_authors = self.source.session.query(
            wp.PostMeta.meta_value,
            func.count(wp.PostMeta.meta_id)).group_by(
                collate(wp.PostMeta.meta_value, "utf8_bin")).filter_by(
                    meta_key='author').order_by(
                        collate(wp.PostMeta.meta_value, "utf8_bin"))
        new_authors = []
        for name, count in unique_authors:
            # Create a new term for this new author
            new_authors.append(wp.Term(
                name=name,
                slug=kebabify(name),
                term_group=0,
                count=count,
                taxonomy='sd-author'))

        # Summarise authors found
        logger.debug(
            "Found authors:\n- %s",
            "\n- ".join([a.name for a in new_authors]))

        # Connect new authors to posts
        current_term = None
        assert new_authors
        term_iterator = iter(new_authors)
        for author in self.source.session.query(wp.PostMeta).filter_by(
                meta_key='author').order_by(collate(wp.PostMeta.meta_value, "utf8_bin")):
            # Fetch the new term for current author
            if current_term is None or current_term.name != author.meta_value:
                # Assuming order_by worked, we should just need the next term
                current_term = next(term_iterator)
            # Check we have the matching term
            logger.debug(
                "Term %s vs postmeta %s (id %d)",
                current_term.name,
                author.meta_value,
                author.meta_id)
            assert current_term.name == author.meta_value
            # Add the post for the current term
            current_term.posts.append(author.post)
            # Remove the author
            self.source.session.delete(author)

        # Add new terms
        self.source.session.add_all(new_authors)

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
