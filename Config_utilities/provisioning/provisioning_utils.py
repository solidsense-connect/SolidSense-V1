#-------------------------------------------------------------------------------
# Name:        provisioning_utils
# Purpose:
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import platform

def isWindows():
    pl_str=platform.platform()
    # print("System platform:",pl_str)
    return pl_str.startswith('Windows')

def systemCtl(action, service):
    pass

def main():
    pass

if __name__ == '__main__':
    main()
