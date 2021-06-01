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
    Data de modificação: 01/06/2021
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
from time import sleep

urllib3.disable_warnings()

# Classe para pegar as métricas da Storage Dell Compellent através da REST API
class Client(object):
    # Inicializa o objeto da classe Client
    def __init__(self, host='192.168.110.10', username='', password='', port='3033'):
        self.api_base = 'api/rest'
        self.proto = 'https'
        self.host = host if 'DELLSC_HOST' not in os.environ else os.environ['DELLSC_HOST']
        self.usename = username if 'DELLSC_USERNAME' not in os.environ else os.environ['DELLSC_USERNAME']
        self.password = password if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        self.port = port if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        self.api_method = 'POST'
        self.headers = {'x-dell-api-version': '5.2', 'Cookie': '', 'Content-Type': 'application/json'}
        self.api_login = '%s://%s:%s/%s/ApiConnection/Login' % (self.proto, self.host, self.port, self.api_base)
        self.login()

    # Método para fazer o login e armazenar o Cookie
    def login(self):
        if self._isClientLogged():
            return  True
        else:
            self.api_method = 'POST'
            self.res = requests.request(self.api_method, '%s' % self.api_login, headers=self.headers, verify=False, auth=HTTPBasicAuth(self.usename, self.password))
            if self.res.status_code == 200:
                self.headers['Cookie'] = '%s=%s' % (self.res.cookies.keys()[0], self.res.cookies.values()[0])
                return True
            else:
                print(self.res.text)
                self.headers['Cookie'] = ''
                return False

    def _isClientLogged(self):
        apiTest = requests.get('%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, '/ApiConnection'), verify=False)
        if apiTest.status_code == 401:
            self.headers['Cookie'] = ''
            return False
        else:
            return True

    # Método interno para fazer a call das requests validando o retorno e fazendo o login caso necessário
    def _apiRequest(self, url, data=''):
        api_url = '%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, url)
        retry = 0
        while not self.login() or retry < 5:
            retry += 1
            sleep(0.3)
        if len(data) > 0:
            self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False, data=self.data)
        else:
            self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False)
        return True

    def _getListRelative(self, api, period, timezone='-03:00', acknowledged=''):
        """
        Função interna retorna um json com a lista de alertas da Storage usando formato de tempo absoluto \n
        Parâmetros: 
          >>> api: url da API Dell Storage Center  
          >>> period: intervalo de tempo relativo () 
          >>> param timezone: Fusohorário da data (ex.: -03:00) 
          >>> param acknowledged: Filtra os alertas pelo campo acknowledged (True ou False)
        """
        startTime = pandas.Timestamp('now', tz=timezone) - pandas.to_timedelta(period)
        startTime = startTime.strftime('%Y-%m-%dT%H:%M:%S%Z')
        self.api_url = api
        self.api_method = 'POST'
        filter_relative = """
{
    "Filter": {
        "FilterType":"AND",
        "Filters":[
        {
            "AttributeName":"createTime",
            "AttributeValue":"%s",
            "FilterType":"GreaterThan"
        }
        ]
    }
}
        """ % re.sub('UTC', '', startTime)
        filter_relative_ack = """
{
    "Filter": {
        "FilterType":"AND",
        "Filters":[
            {
                "AttributeName":"createTime",
                "AttributeValue":"%s",
                "FilterType":"GreaterThan"
            },
            {
                "AttributeName":"acknowledged",
                "AttributeValue":"%s",
                "FilterType":"Equals"
            }
        ]
    }
}
""" % (re.sub('UTC', '', startTime), acknowledged)
        if len(acknowledged) > 0:
            if re.match('true|True|false|False', acknowledged):
                self._apiRequest(self.api_url, self.api_method, data=filter_relative_ack)
        else:
            self._apiRequest(self.api_url, self.api_method, data=filter_relative)
        return sorted(self.res.json(), key=lambda x: x['createTime'])

    # Método para retornar um JSON com uma lista da request solicitada usando tempo absoluto
    def _getListAbsolute(self, api, startTime, endTime, timezone='-03:00', acknowledged=''):
        """
        Função interna retorna um json com a lista de alertas da Storage usando formato de tempo relativo \n
        Parâmetros: 
          >>> api: url da API Dell Storage Center  
          >>> startTime: data de início (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T12:00:00) 
          >>> param endTime: data final (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T23:59:00) 
          >>> param timezone: Fusohorário da data (ex.: -03:00) 
          >>> param acknowledged: Filtra os alertas pelo campo acknowledged (True ou False)
        """
        self.startTime = startTime + timezone
        self.endTime = endTime + timezone
        self.api_method = 'POST'
        self.api_url = api



        self._apiRequest(self.api_url, self.api_method, acknowledged)
        return self.res.json()

    def getListScAlertsRelative(self, period='5m', acknowledged=''):
        """
        Esta função retorna um json com a lista de alertas da Storage usando formato de tempo relativo
        """
        api_url = '/StorageCenter/ScAlert/GetList'        
        #self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False)
        self._getListRelative(api_url, period, acknowledged)
        return pprint.pprint(self.res.json())

    # Método para retornar os alertas da Storage usando tempo absoluto
    def getListScAlertsAbsolute(self, startTime, endTime, acknowledged=''):
        """
        Esta função retorna um json com a lista de alertas da Storage usando formato de tempo absoluto
        """
        api_url = '/StorageCenter/ScAlert/GetList'        
        self.res = requests.request(self.api_method, '%s' % api_url, headers=self.headers, verify=False)
        self._apiRequest(self.api_url, self.api_method)
        self._get
        return pprint.pprint(self.res.json())