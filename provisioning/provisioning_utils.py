#-------------------------------------------------------------------------------
# Name:        provisioning_utils
# Purpose:
#
# Author:      Laurent
#
# Created:     27/11/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     Eclipse Public License 1.0
#-------------------------------------------------------------------------------

import platform
import os
import subprocess
import sys
import datetime
import logging

servlog=logging.getLogger('SolidSense-provisioning')

def isWindows():
    pl_str=platform.platform()
    # print("System platform:",pl_str)
    return pl_str.startswith('Windows')

def systemCtl(action, service):
    args=['systemctl']
    args.append(action)
    args.append(service)
    servlog.info('Executing:'+str(args))
    try:
        c=subprocess.run(args,stderr=sys.stderr)
    except Exception as e:
        servlog.error("Systemctl error:"+str(e))
        return -1
    servlog.info('result:'+str(c))
    return c.returncode



def checkCreateDir(dir) :
    if isWindows() :
        return
    if os.path.lexists(dir):
        # ok the file exist
        if not os.path.isdir(dir) :
            # normal file need to remove it
            os.remove(dir)
            os.mkdir(dir)
    else:
        os.mkdir(dir)
    # adjust mode in all cases
    os.chmod(dir,0o777)

def checkAndRemoveFile(dir,file):
    if os.path.lexists(dir):
        path=os.path.join(dir,file)
        if os.path.lexists(path):
            os.remove(path)


def write_header(fd):
    t=datetime.datetime.now()
    header=t.strftime("# Generated by SolidSense provisioning system on %d-%b-%Y %H:%M:%S\n")
    fd.write(header)

def str2bool(s):
    if s == 'true':
        return True
    elif s == 'false' :
        return False
    else:
        raise(ValueError)

def bool2str(b):
    if b :
        return 'true'
    else :
        return 'false'

def findUsbModem(mfg):
    '''
    Look on the USB system and detect the modem from the manufacturer
    '''
    r=subprocess.run('lsusb',capture_output=True)
    lines=r.stdout.decode('utf-8').split('\n')
    found_modem=False
    for line in lines :
        if len(line) > 0 :
            print(line)
            if line.find(mfg)  > 0 :
                t=line.split(' ')
                bus=int(t[1])
                dev=int(t[3].rstrip(':'))
                ids=t[5].split(':')
                found_modem=True
                break
    if found_modem :
        out={}
        # check the device path
        r=subprocess.run("ls /sys/bus/usb/drivers/option/ | head -n1 | cut -f1 -d':'",capture_output=True,shell=True)
        dev_path=r.stdout.decode('utf-8').rstrip('\n')
        servlog.info("Found "+mfg+" modem on USB bus "+str(bus)+" device "+str(dev)+' Device path:'+dev_path)
        out['bus']=bus
        out['dev'] = dev
        out['mfgid']=ids[0]
        out['modelid'] = ids[1]
        out['dev_path'] = dev_path
        return out
    else:
        servlog.error('No '+mfg+' modem found')
        return None

def checkWirepasSink(tty,sink):

    r=subprocess.run(['wp-get-fw-version',tty],capture_output=True)
    if r.returncode != 0 :
        servlog.info('No Wirepas firmware running on:'+ sink)
        servlog.info(r.stderr.decode('utf-8').rstrip('\n'))
        return False
    else:
        lines=r.stdout.decode('utf-8').split('\n')
        servlog.info(lines[3])
        return True


def main():
    pass

if __name__ == '__main__':
    main()
