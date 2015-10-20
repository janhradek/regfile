
import re
import os
import os.path

# the array contains the instructions for the AutoValues class
# each entry contains: re, group, comment, options
# the most important part is re - the regular expression
# the group and comment values determine the respective output, the following special values are possible
#   "" (empty string) - nothing will be set
#   \1 - get first match from re (other numbers are possible)
# the options can have the following strings (separated by spaces)
#   match - (the default) re.match
#   search - re.search (vs the match)
#   sanitize - replace some non-alnum characters with space from the group and comment (see SANITIZE)
#   import - only process this when importing
#   continue - normaly the AutoValues stop if a match is found, continue will allow other matches as well
# the following is only an unimplemented proposal:
#   g+ - instead of replacing the group value, append a space and the output (append group)
#   +g - preprend to group
#   c+ - instead of replacing the comment value, append a space and the output (append comment)
#   +c - prepend to comment
# order does matter - the items are processed one by one and the first to match is applied, unless continue is specified


SANITIZE = "._/"

from config import CFG, cfgvaltolistlist

class AutoValues(object):
    def __init__(self):
        self.processav()

    def processav(self):
        #self.av = AV
        self.av = cfgvaltolistlist(CFG["regfile"]["autovalues"],strip=False)
        for rr in self.av:
            rr[0] = re.compile(rr[0])

    def getgroupcomment(self, ff, agr, acom, dgr, dcom, imp=False):
        """
        get automatic group and comment of the providef file with respect to provided command line group and comment and default group and comment

        agr, acom, dgr and dcom will maybe all be more relevant later when I decide how to implement additive magic
        """
        gr = ""
        com = ""
        for rr in self.av:
            if "search" in rr[3]:
                res = rr[0].search(ff)
            else: # match is the default
                res = rr[0].match(ff)
            if res == None:
                continue
            if "import" in rr[3] and not imp:
                continue
            # match found
            if rr[1] :#!= "":
                if gr :#!= "" :
                    gr = gr + " "
                gr = gr + res.expand(rr[1])
            if rr[2] :#!= "":
                if com :#!= "" :
                    com = com + " "
                com = com + res.expand(rr[2])

            if "sanitize" in rr[3]:
                for ss in SANITIZE:
                    gr = gr.replace(ss, " ").strip()
                    com = com.replace(ss, " ").strip()

            if not "continue" in rr[3]:
                break
        # the priority is argument, automatic (self) and default
        gr = dgr if not gr else gr
        gr = agr if agr else gr

        com = dcom if not com else com
        com = acom if acom else com

        return (gr, com)

