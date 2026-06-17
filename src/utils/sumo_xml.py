from lxml import etree


def write_meandata_file(output_path, edgedata_file, time_interval):
    with open(output_path, "w+") as f:
        f.write("<additional>\n")
        f.write("\t<edgeData\n")
        f.write(f"\t\tid='density_{time_interval}s'\n")
        f.write(f"\t\tfile='{edgedata_file}'\n")
        f.write(f"\t\tperiod='{time_interval}'\n")
        f.write(f"\t\texcludeEmpty='true'\n")
        f.write(f"\t\twriteAttributes='entered density'/>\n")
        f.write("</additional>\n")


def write_sumo_conf(
    output_path,
    net_file,
    seed,
    route_files=None,
    additional_files=None,
    report_outputs=None,
    device_outputs=None,
):
    root = etree.Element("configuration")
    inp = etree.SubElement(root, "input")
    etree.SubElement(inp, "net_file", value=str(net_file))

    if route_files:
        etree.SubElement(inp, "route-files", value=str(route_files))

    if additional_files:
        etree.SubElement(inp, "additional-files", value=str(additional_files))

    if report_outputs:
        rep = etree.SubElement(root, "report")
        for tag, val in report_outputs.items():
            etree.SubElement(rep, tag, value=str(val))

    rnd = etree.SubElement(root, "random")
    etree.SubElement(rnd, "seed", value=str(seed))

    if device_outputs:
        dev = etree.SubElement(root, "device")
        for tag, val in device_outputs.items():
            etree.SubElement(dev, tag, value=str(val))

    etree.ElementTree(root).write(
        str(output_path), pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )
