#!/usr/bin/env python
# -*- coding: utf-8-*-  

import sys
import getopt
import requests
import json
from bs4 import BeautifulSoup


token = ''

def convert(source):

    html = ''


    #print 'source'

    user = ''

    user = source[source.find('com/') + 4 : ]
    if user.find('/') != -1:
        user = user[0 : user.find('/')]

    #print user

    user_url = "https://api.github.com/users/" + user


    data = requestWithAuth(user_url)

    jobj = json.loads(data.text)


    repos_url = jobj['repos_url']

    following_url = "https://api.github.com/users/" + user + "/following"

    print ' | ----repos----- | https://github.com/' + user + '?tab=repositories | '
    getRepos(repos_url)
    print ' | ----starred----- | https://github.com/' + user + '?tab=stars | '
    getStarred(user)
    print ' | ----following----- | https://github.com/' + user + '?tab=following | '
    getFollowing(following_url)


    return html

def getRepos(repos_url):
    repos_data = requestWithAuth(repos_url)
    repos_jobj = json.loads(repos_data.text)

    repo_dict = {}


    for repo in repos_jobj:
        #print repo['name']
        desc = ''
        if repo.has_key('description') and repo['description'] != None:
            desc = 'description:' 
            desc += 'star(' + str(repo['stargazers_count']) + ') '
            desc += 'forks(' + str(repo['forks']) + ') '
            #desc += 'watchers(' + str(repo['watchers']) + ') '
            desc += repo['description'].replace('\n', '<br>')
        line =  ' | ' + repo['full_name'] + ' | ' + repo['html_url'] + ' | ' + desc


        key = repo.get("stargazers_count", 0)

        repo_dict[getKey(repo_dict, key)] = line

    for k, line in [(k,repo_dict[k]) for k in sorted(repo_dict.keys(), reverse=True)]:
        print line

def getKey(dictData, key):
    if dictData.has_key(key):
        count = 0
        while dictData.has_key(key):
            count += 1
            key = key - count 

        return key
    else:
        return key



def getStarred(user, returnAll=True, pageSize=50):
    starred_dict = {}

    if returnAll:
        for page in range(1, pageSize):
            starred_url = "https://github.com/" + user + "?page=" + str(page) + "&tab=stars"

            r = requests.get(starred_url)
            soup = BeautifulSoup(r.text)
            div = soup.find('div', class_='col-12')
            if div == None:
                break
            for div in soup.find_all('div', class_='col-12'):
                if div.h3 != None:
                    soup2 = BeautifulSoup(div.prettify())

                    divDesc = soup2.find('div', class_='py-1')
                    links = soup2.find_all('a', class_='muted-link')
                    desc = 'description:'
                    star = 0
                    for a in links:
                        if a['href'].endswith('stargazers'):
                            star = int(a.text.strip().replace(',', ''))
                            desc += 'star(' + a.text.strip() + ') '
                            break

                    desc += divDesc.text.replace('\n', '').strip()


                    line = ' | ' + div.h3.text.strip() + ' | http://github.com' + div.h3.a['href']+ ' | ' + desc 

                    starred_dict[getKey(starred_dict, star)] = line

    else:
        starred_url = "https://api.github.com/users/" + user + "/starred"

        starred_data = requestWithAuth(starred_url)
        starred_jobj = json.loads(starred_data.text)

        for starred in starred_jobj:

            desc = ''
            if starred.has_key('description') and starred['description'] != None:
                desc = 'description:'
                desc += 'star(' + str(starred['stargazers_count']) + ') '
                desc += 'forks(' + str(starred['forks']) + ') '
                #desc += 'watchers(' + str(starred['watchers']) + ') '
                desc += starred['description'].replace('\n', '<br>')

            line = ' | ' + starred['full_name'] + ' | ' + starred['html_url'] + ' | ' + desc

            key = starred.get("stargazers_count", 0)

            starred_dict[getKey(starred_dict, key)] = line


    for k, line in [(k,starred_dict[k]) for k in sorted(starred_dict.keys(), reverse=True)]:
        print line.encode('utf-8')

def getFollowing(following_url):

    following_data = requestWithAuth(following_url)
    following_jobj = json.loads(following_data.text)

    for following in following_jobj:
        #print starred
        print ' | ' + following['login'] + ' | ' + following['html_url'] + ' | icon:' + following['avatar_url']

def requestWithAuth(url):
    if token != "":
        return requests.get(url, auth=(token, ''))    
    else:
        return requests.get(url)


def main(argv):
    source = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'u:', ["url"])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)


    for o, a in opts:

        if o in ('-u', '--url'):
            source = a

    if source == "":
        print "you must input the input file or dir"
        return

    convert(source)

if __name__ == '__main__':
    main(sys.argv)
    