import subprocess
import sys

from paths import CONF_FILE, NET_FILE, OUTPUT_FILE, ROUTE_FILE


def gen_conf():
    """
    Create SUMO Config file
    """
    with open(CONF_FILE, "w+") as conf:
        conf.write('<?xml version="1.0"?>\n')
        conf.write("<configuration>\n")
        conf.write("\t<input>\n")
        conf.write(f'\t\t<net-file value="{NET_FILE}"/>\n')
        conf.write(f'\t\t<route-files value="{ROUTE_FILE}"/>\n')
        conf.write("\t</input>\n\n")
        conf.write(f"\t<report>\n")
        conf.write(f'\t\t<tripinfo-output value="{OUTPUT_FILE}"/>\n')
        conf.write(f"\t</report>\n")
        conf.write("</configuration>\n")
    return CONF_FILE


# Generate config file
gen_conf()

sumo_cmd = ["sumo-gui", "-c", CONF_FILE, "--delay", "500", "--output-prefix", "TIME"]

subprocess.run(sumo_cmd)
