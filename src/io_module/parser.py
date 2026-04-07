from lxml import etree

from paths import STATISTICSINFO_OUTPUT_FILE


class Parser:
    def __init__(self):
        self.etree = etree
        self.document = None
        self.episode = None
        self.tree = None

    def parse_statistics_output(self, episode):
        """
        Get mean travel time of simulation episode
        """
        self.document = STATISTICSINFO_OUTPUT_FILE
        self.episode = episode
        self.tree = self.etree.parse(self.document)

        mean_travel_time = self.tree.xpath("//vehicleTripStatistics/@duration")
        return {"episode": self.episode, "mean_travel_time": mean_travel_time}
