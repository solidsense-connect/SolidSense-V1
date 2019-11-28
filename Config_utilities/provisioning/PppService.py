#-------------------------------------------------------------------------------
# Name:        PppService
# Purpose:    Provisionning of the PppService
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "../../../Modem_GPS_Service")))
print(cmd_subfolder)
sys.path.insert(0, cmd_subfolder)

from SolidSenseService import *
from QuectelAT_Service import *


class PppService(KuraService):

    def __init__(self,def_dict):
        KuraService.__init__(self,def_dict)


def main():
    pass

if __name__ == '__main__':
    main()
