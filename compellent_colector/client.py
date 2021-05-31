#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
    Created on 27 de mai de 2021
    @author: Jardel F. F. de Araujo
    
    <DESCRICAO>
    
    Dependências de bibliotecas:
        time            (nativo python)
        os              (nativo python)
        sys             (nativo python)
        subprocess      (nativo python)
        socket          (nativo python)
        re              (nativo python)
        logging         (nativo python)
        signal          (nativo python)
        psutil          (nativo python)
        datetime        (nativo python)
        elasticsearch   (lib elasticsearch)
        daemon_start    (lib daemon_application)

    Criado por: Jardel F. F. de Araujo
    Data de criação: 27/05/2021
    Data de modificação: 31/05/2021
    Versao: 0.1.0
'''

import sys
import os
import pandas
import requests
import json
import pprint
import urllib3
import re
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()

# Classe para pegar as métricas da Storage Dell Compellent através da REST API
class Client(object):
    def __init__(self, host='192.168.110.10', username='', password='', port='3033'):
        self.api_base = 'api/rest'
        self.proto = 'https'
        self.host = host if 'DELLSC_HOST' not in os.environ else os.environ['DELLSC_HOST']
        self.usename = username if 'DELLSC_USERNAME' not in os.environ else os.environ['DELLSC_USERNAME']
        self.password = password if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        self.port = port if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        self.api_method = 'POST'
        #self.api_login = '%s://%s:%s/%s/ApiConnection/Login' % (self.proto, self.host, self.port, self.api_base)
        #self.api_login = '/ApiConnection/Login'
        self.headers = {'x-dell-api-version': '5.2', 'Cookie': ''}
        self.login()
        #self.res = requests.request(self.api_method, '%s' % self.api_login, headers=self.headers, verify=False, auth=HTTPBasicAuth(self.usename, self.password))
        #if self.res.status_code == 200:
        #    self.headers['Cookie'] = '%s=%s' % (self.res.cookies.keys()[0], self.res.cookies.values()[0])
        #else:
        #    print(self.res.text)
        #    self.headers['Cookie'] = ''

    def login(self):
        self.api_method = 'POST'
        self.api_login = '%s://%s:%s/%s/ApiConnection/Login' % (self.proto, self.host, self.port, self.api_base)
        self.res = requests.request(self.api_method, '%s' % self.api_login, headers=self.headers, verify=False, auth=HTTPBasicAuth(self.usename, self.password))
        if self.res.status_code == 200:
            self.headers['Cookie'] = '%s=%s' % (self.res.cookies.keys()[0], self.res.cookies.values()[0])
        else:
            print(self.res.text)
            self.headers['Cookie'] = ''
            return False

    def _callRequest(self, url, method):
        self.api_method = method
        api_url = '%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, url)
        self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False)
        if len(self.headers['Cookie']) == 0 or self.res.status_code == 401:
            self.login()
            return True

    def getListScAlerts(self, startTime, endTime, acknowledged=''):
        self.api_method = 'POST'
        api_url = '/StorageCenter/ScAlert/GetList'
        
        self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False)
        self._callRequest(self.api_url, self.api_method)
        return pprint.pprint(self.res.json())

    def getListRelative(self, api, period='5m', timezone='-03:00', acknowledged=''):
        self.api = api
        self.period = period
        self.timezone = timezone
        startTime = pandas.Timestamp('now', tz=self.timezone) - pandas.to_timedelta(self.period)
        startTime = startTime.strftime('%Y-%m-%dT%H:%M:%S%Z')
        self.api_method = 'POST'
        self.api_url = '/StorageCenter/ScAlert/GetList'
        self._callRequest(self.api_url, self.api_method)
        return re.sub('UTC', '', startTime)


