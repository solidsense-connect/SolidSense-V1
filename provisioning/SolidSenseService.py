#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     Eclipse Public License 1.0
#-------------------------------------------------------------------------------

import logging
import os
import time
import json

from provisioning_utils import *

servlog=logging.getLogger('SolidSense-provisioning')

state_DISABLED='disabled'
state_ACTIVE='active'
state_AUTO='auto'
state_INTERACTIVE='interactive'

services_States={state_DISABLED: False, state_INTERACTIVE: False, state_AUTO: True, state_ACTIVE: True}

class SolidSenseService:

    def __init__(self,kura_config,def_dict):

        self._name=def_dict.get('name','**No name**')
        self._kura_config=kura_config

        self.validate_state(def_dict)
        self._parameters=def_dict.get('parameters',{})
        self._variables=def_dict.get('variables')
        if self._variables == None :
            self._variables={}
        self._properties=def_dict.get('properties')
        if self._properties == None :
            self._properties={}

        self._variables['service_name']=self._name

    def validate_state(self,def_dict):
            self._state=def_dict.get('state',state_DISABLED)
            try:
                val=services_States[self._state]
            except KeyError :
                servlog.error("Service "+self._name+ " Invalid state")
                self._state=state_DISABLED

    def name(self):
        return self._name

    def combine(self,def_dict) :
        '''
        combine the existing definition with the new one
        new variables and properties are added
        existing values are updated
        '''
        try:
            self._state=def_dict['state']
        except KeyError:
            pass
        def merge_dict(dict1,dict2):
            if dict2 == None:
                return
            for key,value in dict2.items():
                dict1[key]=value

        merge_dict(self._parameters,def_dict.get('parameters',None))
        merge_dict(self._variables,def_dict.get('variables',None))
        merge_dict(self._properties,def_dict.get('properties',None))


    def dump_variables(self):
        servlog.info("Variables for service: "+self._name)
        for name,value in self._variables.items():
           servlog.info(name+"="+str(value))

    def startService(self):
        pass

    def configuration(self):
        pass

    def variableValue(self,name):
        try:
            value=self._variables[name]
        except KeyError :
            value=self._kura_config.get_variable(name)
            if value == None :
                return None
        return self.checkAndReplaceVar(value)

    def asVariable(self,name):
        if name in self._variables.keys():
            return True
        return self._kura_config.asVariable(name)

    def asParameter(self,name):
        if name in self._parameters.keys():
            return True
        else:
            return False

    def checkAndReplaceVar(self,value):
        if type(value) != str :
            return value
        if len(value) == 0:
            return value
        if value[0] == "^" :
            # that is a quoted string

            return value[1:]

        var_s= value.find('$')
        if var_s != -1 :
            # that is a variable that needs to be dereferenced
            i=var_s+1
            for c in value[var_s+1:] :
                if c.isalnum() or c in '.-_' :
                    i += 1
                else:
                    break
            vt=value[var_s+1:i]
            end=value[i:]


            var_v= self.variableValue(vt)
            # print("Variable=",vt,"end=",end,"val=",var_v)

            try:
                if type(var_v)  ==str :
                    res=value[:var_s]+var_v+end
                elif len(value[:var_s]) == 0:
                    res=var_v
                else:
                    res=value[:var_s]+str(var_v)

            except TypeError :
                servlog.error("Error processing value:"+value)
                # print("var_s=",var_s,"var_v=",var_v)
                return None

            return res
        else:
            return value


    def parameterValue(self,name):
        try:
            value=self._parameters[name]
        except KeyError:
             servlog.info("Service:"+self._name+" missing parameter:"+name)
             return None
        return self.checkAndReplaceVar(value)




class KuraService(SolidSenseService) :

    def __init__(self,kura_config,def_dict):
        SolidSenseService.__init__(self,kura_config,def_dict)
        try:
            self._snapshot_confname=self._parameters['configuration']
        except KeyError :
            servlog.error("Missing snapshot name in:"+self._name)
            return

        self._prefix=self.parameterValue('prefix')


    def propertyName(self,property_short):

        if self._prefix == None :
            return property_short
        else:
            return self._prefix+'.'+property_short

    def configuration(self):
        self._snapconf=self._kura_config.getSnapshot_conf(self._snapshot_confname)
        # print ("Adjusting XML for:",self.name())
        for p in self._properties.items():
            name=self.propertyName(p[0])
            value=self.checkAndReplaceVar(p[1])
            servlog.debug (' Configure property:'+self._name+"."+name+"="+str(value))
            self._snapconf.set_property(name,value)



class NetworkService(KuraService):

    def __init__(self,kura_config,def_dict):
        KuraService.__init__(self,kura_config,def_dict)

    def configuration(self):
        KuraService.configuration(self)

    def writeKuranet(self,fd):
        for name,value in self._properties.items():
            line="%s=%s\n" % (self.propertyName(name),str(self.checkAndReplaceVar(value)))
            fd.write(line)

class WiFiService(NetworkService):

    def __init__(self,kura_config,def_dict):
        NetworkService.__init__(self,kura_config,def_dict)

    def configuration(self):
        NetworkService.configuration(self)
        # Compute the global parameters
        if not self.asVariable('SSID'):
            self._variables['SSID']=self._kura_config.serial_number()

        # generate the hostapd configuration
        outdir=self._kura_config.output_dir('/etc')
        outfile=os.path.join(outdir,'hostapd-'+self._name+'.conf')
        self._kura_config.gen_from_template(self,'','hostapd.conf.tmpl',outfile)

        '''
class EthernetService(NetworkService):

    def __init__(self,kura_config,def_dict):
        NetworkService.__init__(self,kura_config,def_dict)

    def configuration(self):
        NetworkService.configuration(self)
        # generate the kuranet conf
        #infile='kuranet.'+self._name+'.client.tmpl'
        #outfile='/tmp/kuranet.'+self._name+'.conf'
        #kura_config.gen_from_template('kura',infile,outfile)
    '''




WirepasDataDir='/data/solidsense/wirepas'

class WirepasSink(KuraService):

    Sink_Keywords=("ADDRESS","NETWORK_ID","NETWORK_CHANNEL")
    Sink_Cmd={"NAME":'-s',"ADDRESS":"-n","NETWORK_ID":"-N","NETWORK_CHANNEL":"-c","START":"-S"}
    def __init__(self,kura_config,def_dict):
        KuraService.__init__(self,kura_config,def_dict)
        # self.dump_variables()

    def configuration(self):
        if self._state == state_DISABLED :
            checkAndRemoveFile(WirepasDataDir,"wirepasSinkConfig.service.cfg")
            return
        KuraService.configuration(self)
        checkCreateDir(WirepasDataDir)

        # mandatory setup
        try:
            self._syst_service= self._parameters['system']
            plugin= self._parameters['plugin']
            plugin_name= self._parameters['plugin_name']
        except KeyError :
            servlog.error('Wirepas Sink:'+self._name+' Missing parameters')
            return
        self._kura_config.add_plugin(plugin_name,plugin)

        # now check that we have a valid Wirepas sink
        if readSinkStatus(self._syst_service) :
            servlog.info("Systemd service running:"+self._syst_service)
        else:
            port=self.parameterValue('port')
            if port == None :
                servlog.critical('Cannot check Wirepas sink => Configuring anyway but may lead to disfunctional system ')
            else:
                dev_port=os.path.join('/dev',port)
                if not checkWirepasSink(dev_port,self._name):
                    self._state= state_DISABLED
                    return
                servlog.info("Wirepas firmware found on "+self._name)


        # self.configSink()
        # sinks must be configured after starting the service

    def configSink(self):

        # write the configuration file
        outdir=self._kura_config.output_dir(WirepasDataDir)
        fd=open(os.path.join(outdir,'wirepasSinkConfig.service.cfg'),'w')
        # write_header(fd)
        fd.write(WirepasSink.Sink_Cmd['NAME']+'='+self._name+'\n')
        for k in WirepasSink.Sink_Keywords :
            fd.write(WirepasSink.Sink_Cmd[k]+'='+str(self.variableValue(k))+'\n')
        fd.write(WirepasSink.Sink_Cmd['START']+'='+bool2str(self._parameters.get('start',False))+'\n')
        fd.close

    def startService(self):
        servlog.debug('starting sink service:'+self._name+" "+self._state)
        # issue 549 wrong test on service activity
        if self._state == state_ACTIVE:
            if not readSinkStatus(self._syst_service) :
                # we shall start the service as it is not active issue #549
                servlog.info('Systemd activation for: '+self._name)
                systemCtl('enable',self._syst_service)
                systemCtl('start',self._syst_service)
                # wait to allow the system to start
                time.sleep(1.0)
            self.configSink()
            systemCtl('start','wirepasSinkConfig')




class WirepasTransport(KuraService):

    # Transport_Keywords=("ADDRESS","PORT","USER","PASSWORD")
    Transport_Cmd={"ADDRESS":"host","PORT":"port","USER":"mqtt_username","PASSWORD":"mqtt_password"}
    def __init__(self,kura_config,def_dict):
        KuraService.__init__(self,kura_config,def_dict)

    def configuration(self):
        self._service=self.parameterValue('system')
        if self._state == state_DISABLED :
            checkAndRemoveFile(WirepasDataDir,self._service+'.service.cfg')
            return
        KuraService.configuration(self)
        checkCreateDir(WirepasDataDir)

        plugin= self.parameterValue('plugin')
        plugin_name= self.parameterValue('plugin_name')

        self._kura_config.add_plugin(plugin_name,plugin)
        if self._state == state_INTERACTIVE :
            return
        # compute the gateway-id
        gatewayID=self.parameterValue('gatewayID')
        customID= self.parameterValue('customID')
        if customID != None :
            # highest priority
            self._gwid=customID
            self._snapconf.set_property('customID',customID)
            self._snapconf.set_property('gatewayID','custom')
        elif self.asVariable('gateway-id'):
            self._gwid=self.variableValue('gateway-id')
            self._snapconf.set_property('customID',self._gwid)
            self._snapconf.set_property('gatewayID','custom')
        else:
            self._snapconf.set_property('customID','None')
            self._snapconf.set_property('gatewayID','device')
            self._gwid=self.variableValue('SERIAL-NUMBER')


        # print('gateway ID=',self._gwid)

        # now generate the configuration files for the services

        self.gen_transport_conf()


    def gen_transport_conf(self):
        outdir=self._kura_config.output_dir(WirepasDataDir)
        file=os.path.join(outdir,self._service+'.service.cfg')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("Wirepas transport - "+file+" :"+err)
            return
        write_header(fd)
        for c in WirepasTransport.Transport_Cmd.items():
            fd.write(c[1])
            fd.write(": ")
            fd.write(str(self.variableValue(c[0])))
            fd.write('\n')
        sec= self.variableValue('SECURE')
        if sec == None : sec = False
        sec = not sec
        fd.write('unsecure_authentication: '+bool2str(sec)+'\n')
        fd.write('gateway_id: '+self._gwid+'\n')
        fd.write('full_python: false\n\n')
        fd.close()

class WirepasMicroService(KuraService):

    def __init__(self,kura_config,def_dict):
        KuraService.__init__(self,kura_config,def_dict)

    def configuration(self):
        if self._state == state_DISABLED :
            checkAndRemoveFile(WirepasDataDir,self._service+'.service.cfg')
            return
        KuraService.configuration(self)
        checkCreateDir(WirepasDataDir)
        self._service=self.parameterValue('system')
        if self._state == state_INTERACTIVE :
            return
        self.gen_microservice_conf()


    def gen_microservice_conf(self):
        file=os.path.join(WirepasDataDir,self._service+'.service.cfg')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("Wirepas micro service "+file+" :"+err)
            return
        write_header(fd)
        if self.variableValue('GLOBAL'):
            addr='[::]'
        else:
            addr='127.0.0.1'
        fd.write('host: '+addr+'\n')
        fd.write('\n')
        fd.close()


BluetoothDataDir='/data/solidsense/ble_gateway'
MQTTDataDir='/data/solidsense/mqtt'

class MQTTService (KuraService):
    Transport_Cmd={"address":"mqtt_hostname","port":"mqtt_port","user":"mqtt_username","passwd":"mqtt_password",
                    "secured": None}
    Default_Parameters= {'trace':'info'}
    def __init__(self,kura_config,def_dict):
        KuraService.__init__(self,kura_config,def_dict)

    def configuration(self):
        self._service=self.parameterValue('system')
        if self._state == state_DISABLED :
            checkAndRemoveFile(MQTTDataDir,self._service+'.service.cfg')
            return
        KuraService.configuration(self)
        checkCreateDir(MQTTDataDir)

        plugin= self.parameterValue('plugin')
        plugin_name= self.parameterValue('plugin_name')

        self._kura_config.add_plugin(plugin_name,plugin)
        if self._state == state_INTERACTIVE :
            return
        # compute the gateway-id
        gatewayID=self.parameterValue('gatewayID')
        customID= self.parameterValue('customID')
        if customID != None :
            # highest priority
            self._gwid=customID
            self._snapconf.set_property('customID',customID)
            self._snapconf.set_property('gatewayID','custom')
        elif self.asVariable('gateway-id'):
            self._gwid=self.variableValue('gateway-id')
            self._snapconf.set_property('customID',self._gwid)
            self._snapconf.set_property('gatewayID','custom')
        else:
            self._snapconf.set_property('customID','None')
            self._snapconf.set_property('gatewayID','device')
            self._gwid=self.variableValue('SERIAL-NUMBER')

        self.gen_transport_conf()
        # now generate the parameters.json
        param={}
        for key,value in  MQTTService.Default_Parameters.items():
            if self.asParameter(key):
                param[key]=self.parameterValue(key)
            else:
                param[key]=value
        outdir=self._kura_config.output_dir(MQTTDataDir)
        file=os.path.join(outdir,'parameters.json')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("MQTT "+str(err))
            return
        json.dump(param,fd,indent=1)
        fd.write('\n')
        fd.close()

    def startService(self):
        # now activate the service
        servlog.debug('starting MQTT service:'+self._name+" "+self._state)
        if self._state != state_DISABLED:
           systemCtl('enable',self._service)
        if self._state == state_ACTIVE :
            systemCtl('start',self._service)

    def gen_transport_conf(self):
        outdir=self._kura_config.output_dir(MQTTDataDir)
        file=os.path.join(outdir,self._service+'.service.cfg')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("MQTT transport - "+file+" :"+err)
            return
        write_header(fd)
        sec= self.variableValue('SECURE')
        if sec == None : sec = False
        sec = not sec

        fd.write('gateway_id: '+self._gwid+'\n')
        fd.write('mqtt_force_unsecure: '+bool2str(sec)+'\n')

        for prop,val in self._properties.items():
            try:
                param=MQTTService.Transport_Cmd[prop]
            except KeyError :
                param=prop
            if param == None : continue

            fd.write(param)
            fd.write(": ")
            fd.write(str(self.variableValue(prop)))
            fd.write('\n')


        fd.close()


class BluetoothService(SolidSenseService):

    def __init__(self,kura_config,def_dict):
        SolidSenseService.__init__(self,kura_config,def_dict)


    def startService(self):
        # now activate the services for hci1 and hci2
        servlog.debug('starting Bluetooth service:'+self._name+" "+self._state)
        if self._state == state_ACTIVE:
            interface=self.parameterValue('port')
            if interface == None: return
            if interface == 'ttymxc1':
                systemCtl('enable','ble1')
                systemCtl('start','ble1')
            elif interface == 'ttymxc2':
                systemCtl('enable','ble2')
                systemCtl('start','ble2')
            elif interface == 'internal' :
                pass
            else:
                servlog.error("Bluetooth service - unknown port:"+interface)


class BLEClientService(SolidSenseService):
    Default_Parameters= {'max_connect':10,'notif_MTU':63,'debug_bluez':False,'trace':'info','interface':'hci0'}
    def __init__(self,kura_config,def_dict):
        SolidSenseService.__init__(self,kura_config,def_dict)

    def configuration(self):
        # self._service=self.parameterValue('system')

        checkCreateDir(BluetoothDataDir)

        # now generate the parameters.json
        param={}
        for key,value in  BLEClientService.Default_Parameters.items():
            if self.asParameter(key):
                param[key]=self.parameterValue(key)
            else:
                param[key]=value
        outdir=self._kura_config.output_dir(BluetoothDataDir)
        file=os.path.join(outdir,'parameters.json')
        try:
            fd=open(file,'w')
        except IOError as err:
            servlog.error("Bluetooth Client "+str(err))
            return
        json.dump(param,fd,indent=1)
        fd.write('\n')
        fd.close()

def main():
    pass

if __name__ == '__main__':
    main()
