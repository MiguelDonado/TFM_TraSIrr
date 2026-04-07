from lxml import etree


class Parser:
    """
    Create one Parser object per document to be parsed
    """

    def __init__(self, document):
        self.document = document
        self.tree = etree.parse(document)

    def mean_travel_time(self):
        return float(self.tree.xpath("string(//vehicleTripStatistics/@duration)"))

    def parse_episode(self, episode):
        return {"episode": episode, "mean_travel_time": self.mean_travel_time()}
