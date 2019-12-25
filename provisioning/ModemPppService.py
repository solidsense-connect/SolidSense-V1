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
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0], "../../Modem_GPS_Service")))
sys.path.insert(0, cmd_subfolder)

import json
import logging
import stat

from SolidSenseService import *
from QuectelAT_Service import *

loclog=logging.getLogger('SolidSense-provisioning')


class PppService(NetworkService):

    def __init__(self,kura_config,def_dict):
        NetworkService.__init__(self,kura_config,def_dict)
        modem=kura_config.get_service('modem_gps')
        if modem == None:
            self._state='disabled'
            loclog.error("Ppp Service => No supporting modem service")
            self._valid = False
        else:
            self._valid = modem.valid()
            if not self._valid :
                loclog.error('Ppp Service => No valid modem')



    def configuration(self):
        if not self._valid :
            return
        NetworkService.configuration(self)
        # kura_config.addPpp()


class ModemGps(SolidSenseService):

    def __init__(self,kura_config,def_dict):
        SolidSenseService.__init__(self,kura_config,def_dict)
        if isWindows():
            kura_config.set_variable('MODEM_MODEL',"EC25")
            self._state='active'
            self._valid=True
        else:
            tty1=self.parameterValue('modem_ctrl')
            if not os.path.exists(tty1) :
                loclog.error('Modem service => TTY control file not existing:'+tty1)
                self._valid=False
                return
            mode=os.stat(tty1).st_mode
            if stat.S_ISCHR(mode) == 0 :
                loclog.error('Modem service => Invalid TTY control file:'+tty1)
                self._valid=False
                return
            # Now some basic checks on the modem
            try:
                modem = QuectelModem(tty1)
            except ModemException as err:
                loclog.error('Modem Service => Error during modem access:'+str(err))
                self._valid=False
                return
            #
            #  now get the parameters
            #
            kura_config.set_variable('MODEM_MFG',modem.manufacturer())
            kura_config.set_variable('MODEM_MODEL',modem.model())
            kura_config.set_variable('MODEM_IMEI',modem.IMEI())
            kura_config.set_variable('MODEM_SIM_IN',modem.SIM_Present())
            self._valid= True
            if self._state == 'auto' :
                self._state = 'active'




    def valid(self):
        return self._valid


    def configuration(self):
        if self._state == 'active' :
            self._parameters['start_gps_service']= True
        else:
            self._parameters['start_gps_service']= False
        self._system_serv=self._parameters.get('system')
        try:
            del self._parameters['system']
        except KeyError :
            pass
        outdir=self._kura_config.output_dir('/data/solidsense/modem_gps')
        param=os.path.join(outdir,'parameters.json')
        checkCreateDir(outdir)
        try:
            fd=open(param,'w')
        except IOError as err:
            loclog.error("ModemGps "+param+ " "+str(err))
            return
        json.dump(self._parameters,fd,indent=1)
        fd.close()

    def startService(self):
        if self._state == 'active' :
            servlog.info('Systemd activation for: '+self._name)
            systemCtl('enable',self._system_serv)
            systemCtl('start',self._system_serv)


def main():
    pass

if __name__ == '__main__':
    main()
