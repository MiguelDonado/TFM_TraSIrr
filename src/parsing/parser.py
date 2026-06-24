"""
Generic XPath-based parser for SUMO XML output files.

Wraps lxml to provide three extraction modes used by sumo_outputs.py:
  extract_one      — single scalar value via XPath string() function
  extract_many     — list of attribute values across multiple elements
  extract_fcd_flat — specialised reader for fcd-export.xml, which has
                     a nested timestep > vehicle structure that requires
                     its own flattening logic

XPath expressions are defined in config/config.yaml and passed in by
the caller, keeping query definitions separate from parsing mechanics.
"""

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

    def extract_fcd_flat(self, episode):
        rows = []

        timesteps = self.tree.xpath("//timestep")

        for ts in timesteps:
            t = float(ts.get("time"))

            for vehicle_elem in ts.xpath("vehicle"):
                rows.append(
                    {
                        "episode": episode,
                        "timestep": t,
                        "vehicle_id": vehicle_elem.get("id"),
                        "x": float(vehicle_elem.get("x")),
                        "y": float(vehicle_elem.get("y")),
                    }
                )
        return rows
