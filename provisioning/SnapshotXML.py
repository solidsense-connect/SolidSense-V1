#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent Carré
#
# Created:     02/12/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import xml.etree.ElementTree as ET

from provisioning_utils import *

loclog=logging.getLogger('SolidSense-provisioning')

esf_uri="http://eurotech.com/esf/2.0"
ocd_uri="http://www.osgi.org/xmlns/metatype/v1.2.0"

def esf_tag(tag):
    return '{'+esf_uri+'}'+tag

class SnapshotFile:

    def __init__(self,file):

        ET.register_namespace('esf',esf_uri)
        ET.register_namespace('ocd',ocd_uri)
        try:
            self._tree=ET.parse(file)
        except ET.ParseError as err:
            print (err)
            raise


        self._root=self._tree.getroot()
        self._configurations={}
        cfs=self._root.findall(esf_tag('configuration'))
        for c in cfs:
            sc=SnapshotConfiguration().fromXML(c)
            self._configurations[sc.name()]=sc

    def get_configuration(self,name):
        try:
            return self._configurations[name]
        except KeyError :
            loclog.info('Missing configuration:'+name)
            return None


    def print_elements(self):
        for child in self._root :
            print(child.tag)

    def write(self,filename) :
        try:
            self._tree.write(filename,encoding="UTF-8",xml_declaration=True)
        except IOError as err:
            print(err)

    def write_simple(self,filename):
        try:
            fd=open(filename,'w')
        except IOError as err:
            loclog.error("cannot open:"+filename+" "+err)
            return
        for c in self._configurations.values():
            c.write_simple(fd)
        fd.close()

class SnapshotConfiguration:

    def __init__(self):

        self._properties={}

    def fromXML(self,conf_xml):
        self._xml=conf_xml
        self._pid=conf_xml.attrib['pid']
        e= self._pid.split('.')
        self._name=e[len(e)-1]
        self._properties_xml=self._xml.findall(esf_tag('properties'))[0]
        for p in self._properties_xml.findall(esf_tag('property')):
            sp=SnapshotProperty().fromXML(p)
            self._properties[sp.name()]=sp
        return self


    def name(self):
        return self._name

    def xml_elem(self):
        return self._xml

    def get_property(self,name):
        return self._properties[name]

    def get_properties_names(self):
        props= list()
        for k in self._properties.keys():
            props.append(k)
        props.sort()
        return props

    def set_property(self,name,value):
        try:
            p=self._properties[name]
        except KeyError :
            loclog.info(' Configuration:'+self._name+" property not found:"+name)
            p=None
        if p == None:
            self.add_property(name,value)
            return
        p.setvalue(value)

    def add_property(self,name,value) :
        p=SnapshotProperty()
        p.newProperty(self._properties_xml,name,value)
        self._properties[p.name()]=p


    def write_simple(self,fd):
        fd.write("#### ")
        fd.write(self._name)
        fd.write('\n')
        for pn in self.get_properties_names() :
            p=self._properties[pn]
            p.write_simple(fd)

class SnapshotProperty:

    def __init__(self) :
        pass

    def fromXML(self,prop_xml):
        self._prop_xml=prop_xml
        a=prop_xml.attrib
        self._name=a['name']
        self._type=a['type']
        self._encrypted=a['encrypted']
        self._array=str2bool(a['array'])
        self._value_xml=prop_xml.findall(esf_tag('value'))[0]
        return self

    def newProperty(self,parent,name,value):
        attrib={}
        self._name=name
        attrib['name']=name
        attrib['array']='false'
        attrib['encrypted']='false'
        # now determine the type
        if type(value) == int :
            txml="Integer"
        elif type(value) == bool :
            txml="Boolean"
        else:
            txml="String"
        attrib['type'] = txml
        self._type=txml
        self._array=False
        self._encrypted=False
        self._prop_xml=ET.SubElement(parent,esf_tag('property'),attrib)
        self._value_xml=ET.SubElement(self._prop_xml,esf_tag('value'))
        self._value_xml.text=str(value)
        self._value_xml.tail='\n'
        self._prop_xml.tail='\n'


    def name(self):
        return self._name

    def getvalue(self):
        return self._value_xml.text

    def setvalue(self,value):
        if self._encrypted :
            # remove enryption key
            self._prop_xml.set('encrypted','false')
            self._encrypted = False
        self._value_xml.text=str(value)

    def write_simple(self,fd):
        fd.write(self._name)
        fd.write('=')
        fd.write(str(self.getvalue()))
        fd.write('\n')





def main():
    # xt=SnapshotElement('../template/kura/snapshot0-elements/snapshot_0-position.xml')
    xt=SnapshotFile('../template/kura/snapshot_0-ref1.xml')
    # xt.write_simple('all_elem.conf')
    # conf=xt.get_configuration('MqttDataTransport')
    # ET.dump(conf.xml_elem())
    xt.write("test.xml")

if __name__ == '__main__':
    main()
