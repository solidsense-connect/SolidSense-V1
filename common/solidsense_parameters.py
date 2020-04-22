#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent
#
# Created:     28/07/2019
# Copyright:   (c) Laurent 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import json
import os






class SolidSenseParameters():

    active=None

    @staticmethod
    def active_set():
        return SolidSenseParameters.active

    @staticmethod
    def getParam(name):
        return SolidSenseParameters.active.get(name)

    def __init__(self,service,default,local_log):

    # local_log=logging.getLogger('Modem_GPS_Service')

        self._default=default
        fn=self.file_name(service)
        try:
            fp=open(fn,'r')
        except (IOError, FileNotFoundError) as err:
            local_log.info("Read parameters in:"+fn+" Err:"+str(err))
            #  initilaise with default values
            self._parameters=default
            try:
                fp=open(fn,'w')
            except IOError as err:
                local_log.error("Write parameters in:"+fn+" Err:"+str(err))
                raise
            json.dump(self._parameters,fp,indent=1)
            fp.close()
            return
        try:
            self._parameters=json.load(fp)
        except Exception as err:
            local_log.error("Error decoding parameter file (running on default):"+str(err))
            self._parameters=default
        # print(modem_gps_parameters)
        fp.close()
        SolidSenseParameters.active=self



    def get(self,name,default=None):
        try:
            return self._parameters[name]
        except KeyError :
            pass
        try:
            return self._default[name]
        except KeyError :
            return default


    def getLogLevel(self):
        debug_level_def={ 'debug':logging.DEBUG, 'info': logging.INFO , 'warning':logging.WARNING, 'error':logging.ERROR, 'critical':logging.CRITICAL}
        try:
            level_str= self._parameters['trace']
        except KeyError :
            return logging.DEBUG
        level_str=level_str.lower()
        try:
            level=debug_level_def[level_str]
        except KeyError :
            return logging.DEBUG
        # print("debug:",level_str,level)
        return level

    def file_name(self,service):
        return os.path.join("/data/solidsense/",service,"parameters.json")


def main():

    pass

if __name__ == '__main__':
    main()
