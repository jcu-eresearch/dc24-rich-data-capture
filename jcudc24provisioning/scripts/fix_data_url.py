"""
This script replaces the view data url prefix of all records in the given folder with the provided prefix.
"""

import glob
import sys
import os


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <records dir> <url prefix>\n'
          '(example: "%s c:/data http://research.jcu.edu.au/enmasse/")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 3:
        usage(argv)
    data_dir = argv[1]
    url_prefix = argv[2].strip()
    if url_prefix[-1] in ("\\", "/", os.sep):
        url_prefix = url_prefix[:-1]

    fix_records_in_dir("c:\\awt_records", url_prefix)

def fix_records_in_dir(dir, url_prefix):
    for fname in glob.glob(dir + os.sep + "*"):
        if os.path.isdir(fname):
            fix_records_in_dir(fname, url_prefix)
        elif fname.endswith(".xml"):
            text = ""
            with open(fname, "r") as f:
                text = f.read()

                data_url_start = text.index("<data_storage_location>") + len("<data_storage_location>")
                data_url_end = text.index("</data_storage_location>")

                id = text[data_url_start : data_url_end].split("/")[-1]
                new_url = "%s/%s" % (url_prefix, id)
#                print new_url + " : " + text[data_url_start : data_url_end] + " : " + fname

                text = text[:data_url_start] + new_url + text[data_url_end:]

                citation_url_start = text.index("<citation_url>") + len("<citation_url>")
                citation_url_end = text.index("</citation_url>")
                text = text[:citation_url_start] + new_url + text[citation_url_end:]
##                print text

#                new_desc = """Rainforest invertebrates have been monitored at permanent monitoring sites across the Australian Wet Tropics rainforest between 2006-2009. Such surveys were conducted on monthly to bi-monthly basis across the Spec, Atherton, Windsor, Carbine and Bellenden Ker Uplands during these years.
#
#                              The Wet Tropics rainforest of North Queensland has the highest biodiversity of any region in Australia. While world heritage listing of the area has prevented ongoing impacts from land clearing, our research suggests that the fauna of the region is highly vulnerable to global climate change. Almost half of the unique rainforest fauna could be lost with an increase in temperature of 3-4 degrees Celsius. This is significant as the IPCC fourth assessment report and regional climate models suggest that we will see between 1.0-4.2 degrees Celsius of warming by the year 2070: potentially causing a catastrophic impact on the world heritage values of the region.
#
#                              Long-term monitoring of the region seeks to understand patterns of biodiversity and to detect shifts in phenology of the invertebrates of the Wet Tropics rainforest.Insects were sampled using a combination of Malaise traps, pitfall traps, and flight intercept traps (FIT) at permanent monitoring sites across the Australian Wet Tropics."""
#
#
#
#                desc_start = text.index("<full_desc>") + len("<full_desc>")
#                desc_end = text.index("</full_desc>")
#                text = text[:desc_start] + new_desc + text[desc_end:]
#                print text

            with open(fname, "w") as f:
                f.write(text)




if __name__ == "__main__":
    main()
