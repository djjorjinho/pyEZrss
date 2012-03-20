#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
from xml.dom import minidom
import sys
import os
import httplib 
import urllib2
import re
import getopt
import socket

class Config:
    config = {}
    filename=None
    configdir=None
    
    def __init__(self):
        self.getFilename()
        self.load()
        return None
    
    def getFilename(self):
        home = os.environ['HOME']
        self.configdir = "%s/.pyEZrss" % home
        if not os.path.exists(self.configdir):
            os.makedirs(self.configdir)
        self.filename = "%s/config.json" % self.configdir
        
        return self.filename
    
    def load(self):
        if not os.path.exists(self.filename):
            self.save()
        fh = open(self.filename,'r')
        self.config = json.load(fh)
        
        return self.config
    
    def save(self):
        fh = open(self.filename,'w')
        fh.write(json.dumps(self.config,indent=4))
        fh.close()
    
    def dump(self):
        return json.dumps(self.config,indent=4)
    
    def __getitem__(self,key):
        try:
            return self.config[key]
        except Exception, e:
            return None
    
    def __setitem__(self,key,value):
        self.config[key]=value
        return
    
class RssReader:
    cfg=None
    
    def __init__(self):
        self.cfg = Config()
        # timeout in seconds
        timeout = self.cfg['timeout'] or 5
        #wrlog("timeout: %d" % timeout)
        socket.setdefaulttimeout(timeout)
        #wrlog(self.cfg.dump())
    
    def read(self):
        for record in self.cfg['subscriptions']:
            self.readOne(record)
            self.cfg.save()
        return
        
    def readOne(self,record):
        address = self.cfg['url']
        address += "&show_name=%(show_name)s&quality=%(quality)s&quality_exact=%(quality_exact)s" % record
        address = address.replace(" ","+")
        wrlog("\t"+address)
        try:
            file_request = urllib2.Request(address) 
            file_opener = urllib2.build_opener() 
            file_feed = file_opener.open(file_request).read() 
            file_xml = minidom.parseString(file_feed)        
            item_node = file_xml.getElementsByTagName("item")        
            self.processItems(item_node,record)
        except Exception, e:
            #wrlog("Error reading "+address)
            #wrlog(e)
            pass
        return
    
    def processItems(self,items,record):
        size = items.length
        cnt=0
        lastguid = record['last_guid']
        new_lastguid=None
        for item in items:
            guid=None
            enclosure=None
            
            for child in item.childNodes:
                if child.nodeName == 'guid':
                    guid = child.childNodes[0].nodeValue
                if child.nodeName == 'enclosure':
                    enclosure = child.attributes['url'].value
            
            if cnt==0:
                new_lastguid = guid
                cnt=1
            
            if guid == lastguid: break
            
            self.download(enclosure)
        
        record['last_guid'] = new_lastguid
        
        return
    
    def download(self,url):
        try:
            webFile = urllib2.urlopen(url)
            newfile = url.split('/')[-1]
            localFile = open(os.path.expanduser(self.cfg['target_dir']+'/'+newfile), 'w')
            localFile.write(webFile.read())
            webFile.close()
            localFile.close()
        except Exception, e:
            #wrlog("Error downloading "+url)
            #wrlog(e)
            pass
        return

def main(args):
    rss = RssReader()
    rss.read()
    return

def wrlog(str):
    print >> sys.stderr, str

if __name__ == '__main__':
    main(sys.argv[1:])
