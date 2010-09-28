#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# File name:    radio.py
# Author:       Viator (viator@via-net.org)
# License:      GPL (see http://www.gnu.org/licenses/gpl.txt)
# Created:      2010-09-28
# Description:
# TODO:

import shoutcast
import sys

class radio():
    def __init__(self):
        self.sc = shoutcast.ShoutcastRadioStation()
        self.onlyurls = False

    def getgenres(self):
        lists = self.sc.get_lists()
        return '\n'.join(lists)

    def search(self, keyword):
        lists = self.sc.search(keyword, self.onlyurls)
        return '\n'.join(lists)

    def getlist(self, genre):
        rl = self.sc._get_subrlists(genre, onlyurls = self.onlyurls)
        return '\n'.join(rl)




def usage():
    return '''
radio.py [options]

Options:

    short   long            type    desc:
    ----------------------------------------
    -g      --getgenres             Get genres list
    -s      --search        str     Search keywords
    -l      --list          str     Get list from genre
    -o      --onlyurls              Get only urls
    -h      --help                  Show this help

'''


def parse_options(options):
    import getopt
    if len(options)<=1:
        return usage()
    try:
        opts, args = getopt.getopt(options[1:], "hogs:l:", 
                            ["help", 
                             "onlyurls",
                             "getgenres",
                             "search=",
                             "list="
                             ])
    except getopt.GetoptError, err:
        return 'Error: ' + str(err) + '\n' + usage()
    rad = radio()
    res = ''
    for o, a in opts:
        if o in ("-h", "--help"):
            return usage()
        elif o in ("-o", "--onlyurls"):
            rad.onlyurls = True
        elif o in ("-g", "--getgenres"):
            res = '%s%s\n' % (res, rad.getgenres())
        elif o in ("-s", "--search"):
            res = '%s%s\n' % (res, rad.search(a))
        elif o in ("-l", "--list"):
            res = '%s%s\n' % (res, rad.getlist(a))
        else:
            assert False, "unhandled option"

    return res


def main():
    import sys
    res = parse_options(sys.argv)
    sys.stdout.write(res)

if __name__ == "__main__":
    main()

# vi: ts=4
