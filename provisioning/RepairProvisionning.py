#-------------------------------------------------------------------------------
# Name:       SolidSenseService
# Purpose:    Initial configuration of the gateway
#
# Author:      Laurent Carré
#
# Created:     22/11/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     Eclipse Public License 1.0
#-------------------------------------------------------------------------------

import yaml
import json
import sys
import os
import logging
import subprocess
import platform
import datetime

from SolidSenseService import *
from ModemPppService import *
from provisioning_utils import *
from SnapshotXML import *

#servlog=logging.getLogger('SolidSense-provisioning')
servlog=None


class ProvisioningException(Exception):
    pass


class SolidSenseConfig:
    '''
    This class shall generate all files for the kura configuration
    snapshot_0.xml
    kura_custom.properties
    kuranet.conf

    but also drives additional configuration by services

    '''

    def __init__(self,template_dir,config_dir):
        self._variables={}
        self._services={}
        self._plugins={}
        self._pppIf=False
        self._outdoor = False
        self._industrial = False
        self._networkIf=[]
        self._template_dir=template_dir
        self._config_dir=config_dir

        self.rpmb_conf()
        self.mender_conf()
        self.gen_unique_id()
        self.read_model_file()
        self.set_internal_variables()
        self.set_variable('mode','repair')


    def rpmb_conf(self):
        if not os.path.exists("/etc/solidsense_device"):
            self.simul_rpmb()
            return

        fd = open("/etc/solidsense_device")
        for line in fd:
        #print line
            ls = line.split('=')
            if ls[0] == "PART":
                self._partnum = ls[1].strip()
            elif ls[0] == "SERIAL":
                self._sernum = ls[1].strip()
            elif ls[0] == "PRODUCT":
                self._prodid = ls[1].strip()
        fd.close()
        self._model = (self._partnum.split('.'))[0]
        num_model=int(self._model[3:])
        if 100 < num_model < 200:
            servlog.info("Outdoor gateway detected")
            self._outdoor = True
        elif 200 < num_model < 300:
            servlog.info("Industrial gateway detected")
            self._industrial = True

    def isOutdoor(self):
        return self._outdoor

    def mender_conf(self):
        if os.path.exists("/etc/mender/artifact_info"):
            fd=open("/etc/mender/artifact_info","r")
            line=fd.read()
            eqid=line.index('=')
            self._firmware= line[eqid+1:len(line)-1]
            fd.close()
        else:
            self._firmware="Unkwown"

    def simul_rpmb(self):
        self._sernum="ZZ191100001"
        self._partnum="SRG0000.00"
        self._prodid="FAKEONE"
        self._model="SRG0000"
        self._firmware="SolidSense-V0.999"

    def set_internal_variables(self):
        self.set_variable("DEVICE-ID", self._sernum)
        self.set_variable("SERIAL-NUMBER",self._sernum)
        self.set_variable("PART-NUM",self._partnum)
        self.set_variable("MODEL-ID",self._model)
        self.set_variable("FIRMWARE",self._firmware)
        self.set_variable("MODEL-NAME",self.get_model_name(self._model))
        self.set_variable("GW_UNIQUE_ID",self._id)

    def read_model_file(self):
        fname= "SolidSense-HW-configurations.yml"
        fname= os.path.join(self._config_dir,fname)
        # print (fname )
        self._conf_def=None
        try:
            fd=open(fname)
        except IOError as err:
            servlog.error(fname+" "+str(err))
            return
        try:
            conf_def=yaml.load(fd,Loader=yaml.FullLoader)
        except yaml.YAMLError as err:
            servlog.error(fname+" syntax error"+str(err))
            return
        self._conf_def=conf_def

    def get_model_name(self,model):
        if self._conf_def != None :
            return self._conf_def.get(model,"Unkown SolidSense hardware configuration")
        else:
            return "Error in configuration definition file"

    def serial_number(self):
        return self._sernum

    def gen_unique_id(self):
        '''
        Generate a unique ID on 19 bits
        serial in week => 11 bits
        week number => 6 bits
        year (2 bits) => 2019 => 00 2020 => 01 2021 => 10 2022 => 11
        2018 => internal test gateways only
        '''
        year=int(self._sernum[2:4])
        week=int(self._sernum[4:6])
        rank=int(self._sernum[6:])
        self._id=0
        if rank > 2047 :
            servlog.error("Overflow on rank in week")
            rank=2047
            return
        self._id=rank
        # now add the week
        self._id += week << 11
        if 19 <= year <= 22:
            year_code= year - 19
        elif year == 18 :
            year_code=0 # map into 2019 but that is no issue
        else:
            servlog.critical("Invalid year code")
            year_code=3

        self._id += year_code << 17
        # print("serial number:",self._sernum,"ID:","0x%06X"%self._id)

    def set_variable(self,keyword,value):
        self._variables[keyword]=value

    def get_variable(self,key,default=None):
        try:
            value=self._variables[key]
        except KeyError :
            servlog.info("variable not defined:"+key)
            value=default
        return value

    def checkAndReplaceVar(self,value):
        if type(value) != str :
            return value
        if value[0] == "^" :
            # that is a quoted string

            return value[1:]

        var_s= value.find('$')
        if var_s != -1 :
            # that is a variable that needs to be dereferenced
            var_v= self.variableValue(value[var_s+1:])
            return value[:var_s]+var_v

        return value

    def variableValue(self,name):
        value=self.get_variable(name)
        if value == None:
            return None
        else:
            return self.checkAndReplaceVar(value)

    def asVariable(self,name):
        return name in self._variables.keys()

    def add_service(self,s_name,service):
        self._services[s_name]=service

    def get_service(self,name):
        try:
            s=self._services[name]
        except KeyError:
            servlog.error("Service: "+name+" Not found")
            return None
        return s

    def add_plugin(self,plugin_name,plugin_file ):

        self._plugins[plugin_name]=plugin_file

    def addPpp(self):
        self._pppIf=True

    def template(self,category,file) :
        # print("template:",self._template_dir)
        filename=os.path.join(self._template_dir,category,file)
        if not os.path.lexists(filename):
            servlog.error("Template file not existing:"+filename)
            return None
        return filename

    def output_dir(self,target):
        if isWindows() :
           return "../../temp"
        elif self.get_variable('mode','normal') == 'test' :
            return "/tmp"
        else:
            return target

    def gen_snapshot0(self):
        outdir=self.output_dir('/opt/eclipse/kura/user/snapshots')
        filename=os.path.join(outdir,"snapshot_0.xml")
        servlog.info("Generating snapshot 0:"+filename)
        self._snapshot.write(filename)

        # servlog.info("generated:"+ outputname+" with:"+str( nbline)+  " lines")
    def dump_snapshot0(self):
        outdir=self.output_dir('/data/solidsense/config')
        filename=os.path.join(outdir,"snapshot_0.xml")
        self._snapshot.write(filename)

    def gen_properties(self):
        '''
        Generate the kura_custom.properties file
        '''
        tmpl=self.template("kura","kura_custom.properties.tmpl")
        outdir=self.output_dir("/opt/eclipse/kura/user")
        out= os.path.join(outdir,"kura_custom.properties")
        servlog.info("Generating Kura custom properties:"+out)
        self.genconfigfile(self,tmpl,out)

    def gen_netconf(self):
        '''
        Generate the kuranet.conf file
        '''
        outdir=self.output_dir('/opt/eclipse/kura/user')
        out=os.path.join(outdir,'kuranet.conf')
        servlog.info("Generating kuranet file:"+out)
        try:
            fd=open(out,'w')
        except IOError as err:
            servlog.error("File opning error:"+out+" "+str(err))
            return
        write_header(fd)

        for s in self._services.values() :
            if issubclass(s.__class__,NetworkService) or s.__class__ == NetworkService :
                # print("processing:",s.name())
                self._networkIf.append(s.name())
                s.writeKuranet(fd)


        # generate the global networking list
        interfaces=""
        for n in self._networkIf[:len(self._networkIf)-1]:
            interfaces += n
            interfaces += ","
        interfaces += self._networkIf[len(self._networkIf)-1]
        # now write it in the xml
        self._snapshot.get_configuration('NetworkConfigurationService').set_property('net.interfaces',interfaces)
        fd.write("net.interfaces="+interfaces+'\n')
        fd.close()

    def gen_plugin(self):
        '''
        Generate the plugin reference file for Kura: dpa.properties
        '''
        # changes for Kura5 packages direct under kura
        outdir=self.output_dir('/opt/eclipse/kura/data')
        output=os.path.join(outdir, 'dpa.properties')
        plugin_dir='/opt/eclipse/kura/data/packages'
        try:
            fd=open(output,'w')
        except IOError as err:
            servlog.error(" Cannot open plugin file:"+output+" "+str(err))
            return
        write_header(fd)
        for plugin,plugin_file in self._plugins.items() :
            filename=os.path.join(plugin_dir,plugin_file)
            fd.write(plugin)
            fd.write('=file\\:')
            fd.write(filename)
            fd.write('\n')
        fd.close()

    def gen_secondary_global(self):
        '''
        generate the global variables that can depends on other variables
        '''
        prefix_s=self.variableValue('ADDRESS_PREFIX')
        if prefix_s == None :
            prefix=0
        else:
            try:
                prefix=int(prefix_s)
            except ValueError :
                prefix=0
        if prefix < 0 or prefix > 15 :
            servlog.error("ADDRESS_PREFIX must be in range [0-15]")
            prefix=0
        addrb= (self._id << 1) + (prefix << 20)
        # print("ADDRESS0: %08X"%addrb)
        self.set_variable('UNIQUE_ADDRESS0',addrb)
        self.set_variable('UNIQUE_ADDRESS1',addrb+1)
        self.set_variable('AUTO_PASSWORD','_%_'+self._sernum[5:]+'#;.&"%')


    def dump_variables(self):
        servlog.info("****** Declared variables and values *******")
        for item in self._variables.items() :
            servlog.info(item[0]+'='+str(item[1]))

    def dump_properties(self,name):
        filename=name+".properties"
        out_dir=self.output_dir('/data/solidsense/config')
        out=os.path.join(out_dir,filename)
        self._snapshot.write_simple(out)

    def gen_from_template(self,service,category,infile,output_file):
        tf=self.template(category,infile)
        if tf != None :
            self.genconfigfile(service,tf,output_file)

    def genconfigfile(self,service,template,output_file):
        '''
        Generate a configuration file from template
        Replace the keyword/variables in the file by actual values
        variables are identified as $!-----!$ The keyword is the string between the '!' and ending $
        Only one variable per line
        '''
        servlog.info("Generating file:"+output_file)
        try:
            ft=open(template,'r')
        except IOError as err:
            servlog.error("file:"+template+" "+str(err))
            return
        try:
            fo=open(output_file,'w')
        except:
            servlog.error("file:"+output_file+" "+str(err))
            return
        #
        #  generate the header
        #
        write_header(fo)
        #
        #  now loop on template
        #
        line_n=0
        for line in ft:
            line_n += 1
            # pass through comments
            if line[0] == '#' or line[0]=='\n' :
                fo.write(line)
                continue
            kds=line.find('$!')
            if kds == -1 :
                fo.write(line)
                continue
            ks = kds + 2
            ke = line.find('!$',ks)
            if ke == - 1 :
                servlog.error("file:"+template+" line:"+str(line_n)+" Keyword syntax error")
                continue
            if ke - ks < 1 :
                servlog.error("file:"+template+" line:"+str(line_n)+" Keyword syntax error")
                continue
            keyword=line[ks:ke]
            # print (keyword)
            fo.write(line[:kds])
            value=service.variableValue(keyword)
            if type(value) != str :
                value=str(value)
            fo.write(value)
            fo.write(line[ke+2:])
            # fo.write('\n')
            # next line
        ft.close()
        fo.close()


######################################################################
#  End SolidSenseConfig Class
######################################################################




def main():
    # template_dir='C:\\Users\\laure\\Sterwen-Tech\\Git-SolidRun\\SolidSense-V1\\template'
    # config_dir='C:\\Users\\laure\\Sterwen-Tech\\Git-SolidRun\\SolidSense-V1\\config'

    config_dir='/opt/SolidSense/config'
    template_dir='/opt/SolidSense/template'
    custom_dir='/data/solidsense/config'

    global servlog
    master_file="SolidSense-conf-base.yml"
    master_file_default=True
    if len(sys.argv) > 1:
        option=sys.argv[1]
        if len(sys.argv) > 2 :
            master_file=sys.argv[2]
            master_file_default=False
    else:
        option=None
    # template_dir='/mnt/meaban/Sterwen-Tech-SW/SolidSense-V1/template'
    # config_dir= '/mnt/meaban/Sterwen-Tech-SW/SolidSense-V1/config'
    # looging system
    # logfile=os.path.join(custom_dir,'provisioning.log')
    # root_logger = logging.basicConfig(filename=logfile,level=logging.INFO)
    servlog = logging.getLogger('SolidSense-provisioning')
    loghandler = logging.StreamHandler()
    logformat = logging.Formatter("%(asctime)s | [%(levelname)s] %(message)s")
    loghandler.setFormatter(logformat)
    servlog.addHandler(loghandler)
    servlog.setLevel(logging.DEBUG)

    servlog.info('*******Starting gateway provisioning repair process***********')
    loghandler.flush()
    kgc=SolidSenseConfig(template_dir,config_dir)
    #
    #  right now only repairs kura_custom.properties
    #
    kgc.gen_properties()
    servlog.info('*******Finishing gateway provisioning repair process***********')
    loghandler.flush()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        exit(0)
    exit(1)
