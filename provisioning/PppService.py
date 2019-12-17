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
# cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "../../Modem_GPS_Service")))
# sys.path.insert(0, cmd_subfolder)

from SolidSenseService import *
# from QuectelAT_Service import *


class PppService(NetworkService):

    def __init__(self,kura_config,def_dict):
        NetworkService.__init__(self,kura_config,def_dict)
        if isWindows():
            self._variables['MODEM_MODEL'] ="EC25"

    def configuration(self):
        NetworkService.configuration(self)
        # kura_config.addPpp()


def main():
    pass

if __name__ == '__main__':
    main()
