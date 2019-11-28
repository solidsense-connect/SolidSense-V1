#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import os

from provisioning_utils import *

servlog=logging.getLogger('SolidSense-provisioning')

class SolidSenseService:

    def __init__(self,def_dict):

        self._name=def_dict.get('name','**No name**')
        self._parameters=def_dict.get('parameters',{})
        self._keywords=def_dict.get('keywords',{})

    def name(self):
        return self._name

    def genConfiguration(self):
        pass

    def genSnapshot(self):
        pass

    def startService(self):
        pass

    def push_keywords(self,kura_config):
        '''
        push the local keywords to the global dictionary
        '''
        for item in self._keywords.items():
            kura_config.set_keyword(item[0],item[1])

    def configuration(self,kura_config):
        self.push_keywords(kura_config)


class KuraService(SolidSenseService) :

    def __init__(self,def_dict):
        SolidSenseService.__init__(self,def_dict)

class WiFiService(KuraService):

    def __init__(self,def_dict):
        KuraService.__init__(self,def_dict)



WirepasDataDir='/data/solidsense/wirepas'

class WirepasSink(KuraService):

    Sink_Keywords=("ADDRESS","NETWORK_ID","NETWORK_CHANNEL")
    Sink_Cmd={"NAME":'-s',"ADDRESS":"-n","NETWORK_ID":"-N","NETWORK_CHANNEL":"-c","START":"-S"}
    def __init__(self,def_dict):
        KuraService.__init__(self,def_dict)

    def configuration(self,kura_config):
        kura_config.add_snapshot_0_element('wirepas-sink')
        prefix='WP-'+self._name.upper()+'-'
        for item in self._keywords.items() :
            keyword=prefix+item[0]
            kura_config.set_keyword(keyword,item[1])

    def startService(self,kura_config):
        try:
            syst_service= self._parameters['system']
            plugin= self._parameters['plugin']
        except KeyError :
            servlog.error('SolidSense provisioning -Wirepas Sink:'+self._name+' Missing parameters')
            return
        kura_config.add_plugin(plugin)
        # write the configuration file
        fd=open(os.path.join(WirepasDataDir,'wirepasSinkConfig.service.cfg'),'w')
        fd.write(WirepasSink.Sink_Cmd['NAME']+'='+self._name+'\n')
        for k in WirepasSink.Sink_Keywords :
            fd.write(WirepasSink.Sink_Cmd[k]+'='+self._keywords[k]+'\n')
        fd.write(WirepasSink.Sink_Cmd['START']+'='+str(self._parameters.get('start',False))+'\n')
        fd.close
        systemCtl('start','wirepasSinkConfig')




class WirepasTransport(KuraService):

    Transport_Keywords=("ADDRESS","PORT","USER","PASSWORD")
    Transport_Cmd={"ADDRESS":"host","PORT":"port","USER":"username","PASSWORD":"password"}
    def __init__(self,def_dict):
        KuraService.__init__(self,def_dict)

    def configuration(self,kura_config):
        kura_config.add_snapshot_0_element('wirepas-transport')
        self._tra=self._keywords.get('TA-ENABLE',False)
        self._trb= self._keywords.get('TB-ENABLE',False)
        self._ms=self._keywords.get('MS-ENABLE',False)
        self._systema=self._parameters.get('ta_system',None)
        self._systemb=self._parameters.get('tb_system',None)
        self._systemm= self._parameters.get('ms_system',None)
        if self._tra :
            self.add_keywords('TA',kura_config)
        else:
            self.add_blank('TA',kura_config)
        if self._trb :
            self.add_keywords('TB',kura_config)
        else:
            self.add_blank('TB',kura_config)
        if self._ms :
            kura_config.set_keyword('WP-MS-ENABLE',True)
            kura_config.set_keyword('WP-MS-GLOBAL',self._keywords.get('MS-GLOBAL',False))
        else :
            kura_config.set_keyword('WP-MS-ENABLE',False)
            kura_config.set_keyword('WP-MS-GLOBAL',False)

        self._gwid_rule=self._keywords.get('DEVICE-ID-RULE','device')
        kura_config.set_keyword('WP-DEVICE-ID',self._gwid_rule)
        custom_id= self._keywords.get('CUSTOM-ID','')
        kura_config.set_keyword('WP-CUSTOM-ID',custom_id)
        if self._gwid_rule == 'device' :
            self._gateway_id= custom_id+kura_config.serial_number()

        # now generate the configuration files for thr services
        if self._tra:
            self.gen_transport_conf('TA',self._systema)
        if self._trb :
            self.gen_transport_conf('TB',self._systemb)
        if self._ms :
            self.gen_microservice_conf(self._systemm)


    def add_keywords(self,tr,kura_config) :
        kura_config.set_keyword('WP-'+tr+'-ENABLE',True)
        kura_config.set_keyword('WP-'+tr+'-SECURE',self._keywords.get(tr+'-SECURE',False))
        for k in WirepasTransport.Transport_Keywords :
            val=self._keywords.get(tr+'-'+k,'')
            kura_config.set_keyword('WP-'+tr+'-'+k,val)

    def add_blank(self,tr,kura_config):
        kura_config.set_keyword('WP-'+tr+'-ENABLE',False)
        kura_config.set_keyword('WP-'+tr+'-SECURE',False)
        for k in WirepasTransport.Transport_Keywords :
            kura_config.set_keyword('WP-'+tr+'-'+k,'')

    def gen_transport_conf(self,tr,service):
        file=os.path.join('/data/solidsense/wirepas',service+'.service.conf')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("SolidSense - provisionning "+file+" :"+err)
            return
        fd.write("#Generated by SolidSense provisioning system\n")
        for c in WirepasTransport.Transport_Cmd.items():
            fd.write(c[1])
            fd.write(": ")
            fd.write(str(self._keywords[tr+'-'+c[0]]))
            fd.write('\n')
        sec= not self._keywords[tr+'-SECURE']
        fd.write('unsecure_authentication: '+str(sec)+'\n')
        fd.write('gwid: '+self._gateway_id+'\n')
        fd.write('full_python: False\n\n')
        fd.close()

    def gen_microservice_conf(self,service):
        file=os.path.join('/data/solidsense/wirepas',service+'.service.conf')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("SolidSense - provisionning "+file+" :"+err)
            return
        fd.write("#Generated by SolidSense provisioning system\n")
        if self._keywords.get('MS-GLOBAL',False):
            addr='[::]'
        else:
            addr='127.0.0.1'
        fd.write('host: '+addr+'\n')
        fd.write('\n')
        fd.close()




def main():
    pass

if __name__ == '__main__':
    main()
