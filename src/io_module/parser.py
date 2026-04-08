from lxml import etree


class Parser:
    """
    Create one Parser object per document to be parsed
    """

    def __init__(self, document):
        self.document = document
        self.tree = etree.parse(document)

    def extract_one(self, xpath, cast):
        """
        Scalar extraction
        """
        value = self.tree.xpath(f"string({xpath})")
        return cast(value)

    def extract_many(self, xpath, cast):
        """
        List extraction
        """
        values = self.tree.xpath(xpath)
        return [cast(v) for v in values]
