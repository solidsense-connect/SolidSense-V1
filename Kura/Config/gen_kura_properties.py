# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent Carré
#
# Created:     15/12/2018
# Copyright:   (c) Laurent 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#

keywords= {}

def gen_default_keywords() :
    keywords["MQTT_SERVER"]="mqtt://vps610213.ovh.net:1883"
    keywords["KAPUA_ACCOUNT"]="SOLIDSENSE-TEST"
    keywords["KAPUA_USER"]="solidrun-internal"
    keywords["KAPUA_PASSWD"]="$SolidSense2019$"
    keywords["APN"] = "operator"
    keywords["APN_USER"]= "operator"
    keywords["APN_AUTH"]= "PAP"
    keywords["APN_PASSWD"]= "operator"
    keywords["NETWORK"]= "DEFAULT"



def set_keyword(keyword,value):
    keywords[keyword]=value

def read_keywords_file(filename):
    try:
        fd=open(filename,"r")
    except IOError as err:
        print err
        return
    print "Reading keyword file:",filename
    for line in fd:
        if line[0]  == '#' : continue
        eqindex=line.find("=")
        keyword=line[:eqindex]
        value=line[eqindex+1:].strip('\n')
        print keyword,"=",value
        keywords[keyword]=value

    fd.close()

def check_replace_keyword(line) :

    stindex=line.find("##KEYWORD##")
    if stindex == -1:
        return line
    outputline=line[:stindex]
    stindex=stindex+11
    lastindex=line.find("</esf:value>",stindex)
    if lastindex == -1 :
        print "syntax error in input file"
        print line
        return line
    keyword=line [stindex:lastindex]
    try:
        value=keywords [keyword]
        print "replacing [",keyword,"] by:",value
    except KeyError :
        print "Unknown keyword:",keyword
        return line
    outputline=outputline+value+line[lastindex:]
    return outputline


def gen_snapshot0(output_dir):
    snapshot_sections= ("header","firewall","net","watchdog","clock",
        "H2Db","mqtt","data","position","cloud","ssl")
    process_section={
        "header": False, "firewall": False, "net": True, "watchdog": False,
        "clock": False, "H2Db": False , "mqtt": True, "data":False,
        "position": False, "cloud": False, "ssl": False }
    ###
    # now generate the snapshot 0
    #
    outputname=output_dir+"/snapshot_0.xml"
    try:
        fo=open(outputname,"w")
    except IOError as err:
        print err
        return
    nbline=0;
    for section in snapshot_sections :
        section_v=section
        if section == "net" :
            if keywords["NETWORK"] == "LTE"  :
                section_v="net-ppp"
        filename="snapshot0-elements/snapshot_0-"+section_v+".xml"
        try:
            ft=open(filename,"r")
        except IOError as err:
            print err
            return
        for line in ft:
            if process_section[section]:
                line_w=check_replace_keyword(line)
            else:
                line_w=line
            fo.write(line_w)
            nbline=nbline+1
        fo.write("\n")
        nbline=nbline+1
        ft.close()
    # write footer
    fo.write("</esf:configurations>\n")
    fo.close()

    print "generated:",outputname,"with:",nbline,"lines"

def main():

    models={ 'ASG0002':"SRGW Indoor-Dual Core-WiFi-LTE CAT4 EU",
        'ASG0001': "SRGW Indoor-Dual Core-WiFi",
        'ASG0003': "SRGW Indoor-Quad Core-WiFi-LTE CAT4 EU",
        'ASG0006' : "SRGW Indoor-Dual Core-WiFi-LTE CAT 4 EU"}

    gen_default_keywords()
    #
    #  first open the config file
    #
    fd=open("/etc/solidsense_device")
    for line in fd :
        #print line
        ls=line.split('=')
        if ls[0] == "PART" :
            partnum=ls[1].strip()
        elif ls[0] == "SERIAL" :
            sernum=ls[1].strip()
        elif ls[0] == "PRODUCT":
            prodid=ls[1].strip()
    fd.close()
    #print "partnum=",partnum," Serial=",sernum," product=",prodid
    #print "P="+partnum
    model=(partnum.split('.'))[0]
    set_keyword("DEVICE-ID",sernum)
    # print "model=",model
    #
    #  Now generate the kura_custom.properies
    #
    ft=open("kura_custom.properties.tmpl")
    try:
        fo=open("/opt/eclipse/kura/user/kura_custom.properties","w")
    except IOError as err:
        print err
        return

    for line in ft:
        fo.write(line)
    ft.close()
    #
    #  now generate custome properties
    #
    # we assume that we have a configuration file on a USB stick
    #
    read_keywords_file("/mnt/usb1/kura_config")

    fo.write("kura.device.name=")
    fo.write(sernum)
    fo.write('\n')
    fo.write("kura.partNumber=")
    fo.write(partnum)
    fo.write('\n')
    fo.write("kura.serialNumber=")
    fo.write(sernum)
    fo.write('\n')
    fo.write("kura.model.id=")
    fo.write(model)
    fo.write('\n')
    try:
        modelName=models[model]
    except KeyError :
        modelName="SolidSense unknown configuration"
    fo.write("kura.model.name=")
    fo.write(modelName)
    fo.write('\n')
    fo.write("################\n")
    fo.write('\n')
    fo.close()
    #
    #   now the network config
    #
    ft=open("kuranet.conf.tmpl")
    fo=open("/opt/eclipse/kura/user/kuranet.conf","w")
    for line in ft :
        fo.write(line)
    ft.close()

    fo.write("net.interface.wlan0.config.master.ssid=")
    fo.write(sernum)
    fo.write('\n')

    fo.close()

    # now generate the snapshot_0
    gen_snapshot0("/opt/eclipse/kura/user/snapshots")



if __name__ == '__main__':
    main()
