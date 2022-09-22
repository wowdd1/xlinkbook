#!/usr/bin/env python

import os
import json
import sys
import datetime  
from record import Record
from record import LibraryRecord
from config import Config


class ExtensionManager:
    
    extensions = {}
    extensions_check_cache = {}
 
    def loadExtensions(self):
        if len(self.extensions) > 0:
            return
        base_path = os.getcwd() + '/extensions'
        #print '--->' + base_path
        dirList = os.listdir(base_path)
        #print dirList
        for f in dirList:
            #print f
            if os.path.isdir(base_path + '/'+ f):
                for f2 in os.listdir(base_path + '/'+ f):
                    if f2 == 'manifest':
                        self.extensions[f] = base_path + '/'+ f + '/' + f2
                        break

    def loadExtensionEx(self, module, className):
        
        return self.newExtension(module, className)

    def loadExtension(self, name):
        if len(self.extensions) == 0:
            self.loadExtensions()
        print 'load ' + name + ' module'
        for k, manifest in self.extensions.items():
            jobj = json.loads(open(manifest, 'rU').read())
            if jobj['name']  == name:
                return self.newExtension('extensions.' + name + '.' + jobj['module'], jobj['class'])

    def newExtension(self, module, cls):
       print 'newExtension:' + module + ' ' + cls
       __import__(module)
       m = sys.modules[module]
      # print m
       for str in dir(m):
           if str == cls:
               att = getattr(m, str)
               return att()

       return None

    def findRecordInLib(self, utils, rID, fileName):
	while True:
            r = utils.getRecord(rID, path=fileName, use_cache=False)
	    if r.get_id().strip() != '':
		return r
	    else:
		if rID.find('-') != -1:
		    rID = rID[0 : rID.rfind('-')]
		else:
		    return None


    def doWork(self, form_dict, utils):
        form = form_dict.copy()
        self.loadExtensions()
        check = form['check']
        rID = form['rID'].encode('utf-8')
        fileName = form['fileName'].encode('utf-8')
        #print form
        if fileName.endswith('library') or fileName.find('exclusive') != -1:
            r = self.findRecordInLib(utils, rID, fileName)
            if r != None and r.get_id().strip() != '':
                lr = LibraryRecord(r.line)
                if lr.get_path() != None and lr.get_path().strip() != '':
                    print lr.get_path()
                    form['originFileName'] = os.getcwd() + '/' + lr.get_path().strip()

                if form.has_key('resourceType') == False and r.line.find('category:') != -1:
                    resourceType = utils.reflection_call('record', 'WrapRecord', 'get_tag_content', r.line, {'tag' : 'category'})
                    if resourceType != None:
                        form['resourceType'] = resourceType


        if check == 'true':
            if form['name'] == "*":
                if fileName.find('db/library/') != -1:
                    form['delete'] = True
                    
                if self.extensions_check_cache.has_key(rID) and (form.has_key('nocache') and form['nocache'] == "false"):
                    print 'return cache for ' + rID
                    return self.checkCache(self.extensions_check_cache[rID].split(' '), form)
                else:
                    self.extensions_check_cache[rID] = self.checkAll(form)
                    return self.extensions_check_cache[rID]
            else:
                extension = self.loadExtension(form['name'])
                if extension != None:
                    if extension.check(form):
                        return form['name']
                    else:
                        if form['url'] != '':
                            return 'reference'
                        return 'false'
                else:
                    print 'error'
                    return ''
        else:
            name = form['name']
            if form.has_key('navigate'):
                name = 'track'
                if form['navigate'].strip() == '':
                    form['name'] = 'star'
                else: 
                    form['name'] = form['navigate'].strip()
            
            extension = self.loadExtension(name)

            starttime = 0
            endtime = 0
            starttime = datetime.datetime.now().microsecond
            result = extension.excute(form) #'cs-stanford2016', form['rID'], form['rTitle'], form['divID'])
            endtime = datetime.datetime.now().microsecond
            print name + " excute cost --> " + str((endtime - starttime) / 1000.0) + "ms"
            return result
    def checkCache(self, names, form):
        result = ''
        for name in names:
            extension = self.loadExtension(name)
            if extension != None:
                if extension.needCache():
                    result += name + ' '
                elif extension.check(form):
                    result += name + ' '
        return result

    def checkAll(self, form):
        result = ''
        for k, v in self.extensions.items():
            starttime = 0
            endtime = 0
            starttime = datetime.datetime.now().microsecond
            if self.loadExtension(k).check(form):
                result += k + " "
            endtime = datetime.datetime.now().microsecond
            print k + " check cost --> " + str((endtime - starttime) / 1000.0) + "ms"
        print result
        return result.strip()

    def genIconLinkHtml(self, linkUrl, iconUrl, radius=0, width=12, height=10):
        clickJS = ''
        if linkUrl.find("*") != -1:
            for url in linkUrl.split("*"):
                clickJS += "window.open('" + url + "');"
        else:
            clickJS = "window.open('" + linkUrl + "');"
        html = '<a href="javascript:void(0);" onclick="' + clickJS + '">' + self.genIconHtml(iconUrl, radius, width, height) + '</a>'
        return html

    def genIconHtml(self, src, radius, width, height):
        if src != '':
            if radius:
                return ' <img src="' + src + '" width="' + str(width) + '" height="' + str(height) + '" style="border-radius:10px 10px 10px 10px; opacity:0.7;">'
            else:
                return ' <img src="' + src + '" width="' + str(width) + '" height="' + str(height) + '">'
        return ''
       
    def getExtensionHtml(self, website, link, group=False):
        html = ''
        if website == "github" or link.find("github.com") != -1:
            repo = link[link.find("com/") + 4 :]
            user = ''
            if repo.endswith("/"):
                repo = repo[0 : len(repo) -1]
            if repo.find("/") != -1:
                user = repo[0 : repo.find("/")]
            else:
                user = repo

            if group:
                js = "getExtensionHtml('', '" + link + "');"
                html =  '<a href="javascript:void(0);" onclick="' + js + '">' + self.genIconHtml(Config.website_icons['extension'], 0, 12, 10) + '</a>'
            else:
                #html += self.genPreviewLink(newAID, itemText, self.getRepoImage(repo))
                html += self.genIconLinkHtml("https://metrics.lecoq.io/insights/" + user + "*" + "https://octoprofile.vercel.app/user?id=" + user + "*" + "https://ossinsight.io/analyze/" + repo, Config.website_icons['analyze'])
                html += self.genIconLinkHtml("https://useful-forks.github.io/?repo=" + repo + "*" + "https://techgaun.github.io/active-forks/#" + repo, Config.website_icons['fork'])
                html += self.genIconLinkHtml("https://github.com/" + repo +  "/commits" + "*" + "https://releaseeye.info/" + repo, Config.website_icons['release'])
                html += self.genIconLinkHtml("https://github1s.com/" + repo + "*" + "https://replit.com/github/" + repo + "*" + "https://mango-dune-07a8b7110.1.azurestaticapps.net/?repo=" + repo, Config.website_icons['ide'])
                html += self.genIconLinkHtml("https://gitplanet.com/" + repo + "*" + "https://similarrepos.com/" + repo + "*" + "https://www.yasiv.com/github/#/costars?q=" + repo, Config.website_icons['repos'])
        return html

