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
    Data de modificação: 08/06/2021
    Versao: 0.1.0
'''

import sys
import os
import pandas
import requests
import json
import urllib3
import re
from requests.auth import HTTPBasicAuth
from time import sleep, time

urllib3.disable_warnings()

class Client(object):
    """
    Classe para pegar as métricas da Storage Dell Compellent através da REST API
    """
    def __init__(self, host, username, password, protocol='https', verify_SSL=True,  port='3033', timezone='-03:00'):
        """
        Inicializa o objeto da classe Client
        Parâmetros:
            >>> param host: IP/Hostname do Dell Storage Center
            >>> param username: Usuário do Dell Storage Center
            >>> param password: Senha do Dell Storage Center
            >>> param protocol: Protocolo da REST API do Dell Storage Center [HTTP|HTTPS] (Default: HTTPS)
            >>> param verify_SSL: Ativar/Desativar verificação do SSL da REST API do Dell Storage Center (Default: True)
            >>> param port: Dell Storage Center REST API port (Default: 3033)
            >>> param timezone: Fusohorário da data (Default: -03:00) 
        """
        self.timezone = timezone
        self.api_base = 'api/rest'
        self.proto = protocol.lower()
        self.verify_SSL = verify_SSL
        self.host = host if 'DELLSC_HOST' not in os.environ else os.environ['DELLSC_HOST']
        self.usename = username if 'DELLSC_USERNAME' not in os.environ else os.environ['DELLSC_USERNAME']
        self.password = password if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        self.port = port if 'DELLSC_PASSWORD' not in os.environ else os.environ['DELLSC_PASSWORD']
        api_method = 'POST'
        self.headers = {'x-dell-api-version': '5.2', 'Cookie': '', 'Content-Type': 'application/json'}
        self.login()

    def login(self):
        """
        Função para fazer o login e armazenar o Cookie
        """
        if self._isClientLogged():
            return  True
        else:
            api_method = 'POST'
            api_login = '%s://%s:%s/%s/ApiConnection/Login' % (self.proto, self.host, self.port, self.api_base)
            if self.proto == 'https':
                self.res = requests.request(api_method, '%s' % api_login, headers=self.headers, verify=self.verify_SSL, auth=HTTPBasicAuth(self.usename, self.password))
            else:
                self.res = requests.request(api_method, '%s' % api_login, headers=self.headers, auth=HTTPBasicAuth(self.usename, self.password))
            if self.res.status_code == 200:
                self.headers['Cookie'] = '%s=%s' % (self.res.cookies.keys()[0], self.res.cookies.values()[0])
                return True
            else:
                print(self.res.text)
                self.headers['Cookie'] = ''
                return False

    def _isClientLogged(self):
        if self.proto == 'https':
            apiTest = requests.get('%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, '/ApiConnection'), verify=self.verify_SSL)
        else:
            apiTest = requests.get('%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, '/ApiConnection'))
        if apiTest.status_code == 401:
            self.headers['Cookie'] = ''
            return False
        else:
            return True

    def _apiRequest(self, url, method, data=''):
        """
        Função interna para fazer a call das requests validando o retorno e fazendo o login caso necessário
        """
        api_url = '%s://%s:%s/%s%s' % (self.proto, self.host, self.port, self.api_base, url)
        retry = 0
        while not self.login() or retry < 5:
            retry += 1
            sleep(0.3)
        else:
            if self.login():
                if len(data) > 0:
                    res = requests.request(method, '%s' % api_url, headers=self.headers, verify=False, data=data)
                else:
                    res = requests.request(method, '%s' % api_url, headers=self.headers, verify=False)
                if self.res.status_code == 200:
                    return res.json()
                else:
                    return {}
            


    def _getTimeListRelative(self, api, period, acknowledged):
        """
        Função interna retorna um json com a lista de alertas da Storage usando formato de tempo absoluto \n
        Parâmetros: 
          >>> api: url da API Dell Storage Center  
          >>> period: intervalo de tempo relativo () 
          >>> param acknowledged: Filtra os alertas pelo campo acknowledged (True ou False)
        """
        self.period = period
        self.acknowledged = acknowledged
        self.startTime = pandas.Timestamp('now', tz=self.timezone) - pandas.to_timedelta(self.period)
        self.startTime = self.startTime.strftime('%Y-%m-%dT%H:%M:%S%Z')
        self.api_url = api
        api_method = 'POST'
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
        """ % re.sub('UTC', '', self.startTime)
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
""" % (re.sub('UTC', '', self.startTime), acknowledged)
        if len(acknowledged) > 0:
            if re.match('true|True|false|False', acknowledged):
                #self._apiRequest(self.api_url, data=filter_relative_ack)
                return sorted(self._apiRequest(self.api_url, method=api_method, data=filter_relative_ack), key=lambda x: x['createTime'])
        else:
            #self._apiRequest(self.api_url, data=filter_relative)
            return sorted(self._apiRequest(self.api_url, method=api_method, data=filter_relative), key=lambda x: x['createTime'])
        #return sorted(self.res.json(), key=lambda x: x['createTime'])

    def _getTimeListAbsolute(self, api, startTime, endTime, acknowledged):
        """
        Função interna retorna um json com a lista de alertas da Storage usando formato de tempo absoluto \n
        Parâmetros: 
          >>> api: url da API Dell Storage Center  
          >>> startTime: data de início (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T12:00:00) 
          >>> param endTime: data final (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T23:59:00) 
          >>> param acknowledged: Filtra os alertas pelo campo acknowledged (True ou False)
        """
        startTime = startTime + self.timezone
        endTime = endTime + self.timezone
        api_method = 'POST'
        self.api_url = api
        filter_absolute = """
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
            "AttributeName":"createTime",
            "AttributeValue":"%s",
            "FilterType":"LessThan"
        }
        ]
    }
}
        """ % (startTime, endTime)
        filter_absolute_ack = """
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
            "AttributeName":"createTime",
            "AttributeValue":"%s",
            "FilterType":"LessThan"
            },
            {
                "AttributeName":"acknowledged",
                "AttributeValue":"%s",
                "FilterType":"Equals"
            }
        ]
    }
}
""" % (startTime, endTime, acknowledged)
        if len(acknowledged) > 0:
            if re.match('true|True|false|False', acknowledged):
                return sorted(self._apiRequest(self.api_url, method=api_method, data=filter_absolute_ack), key=lambda x: x['createTime'])
        else:
            return sorted(self._apiRequest(self.api_url, method=api_method, data=filter_absolute), key=lambda x: x['createTime'])

    def getListScAlertsRelative(self, period='5m', acknowledged=''):
        """
        Esta função retorna um json com a lista de alertas da Storage usando formato de tempo relativo
        """
        api_url = '/StorageCenter/ScAlert/GetList'        
        return self._getTimeListRelative(api_url, period, acknowledged)

    def getListScAlertsAbsolute(self, startTime, endTime, acknowledged=''):
        """"
        Esta função retorna um json com a lista de alertas da Storage usando formato de tempo absoluto
        Parâmetros: 
          >>> startTime: data de início (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T12:00:00) 
          >>> endTime: data final (formato: AAAA-MM-DDTHH:mm:ss ex.: 2021-01-01T23:59:00) 
          >>> acknowledged: Filtra os alertas pelo campo acknowledged (True ou False)
        """
        api_url = '/StorageCenter/ScAlert/GetList'        
        return self._getTimeListAbsolute(api_url, startTime, endTime, acknowledged)

    def getScCapabilities(self):
        """"
        Esta função retorna um json com a lista de capacidades da Storage
        """
        api_url = '/StorageCenter/ScCapabilities/GetList'
        api_method = 'POST'
        return self._apiRequest(api_url, method=api_method)

    def getScConfiguration(self):
        """"
        Esta função retorna um json com a lista de configurações da Storage
        """
        api_url = '/StorageCenter/ScConfiguration'
        api_method = 'GET'
        return self._apiRequest(api_url, api_method) 

    def getScServer(self):
        """"
        Esta função retorna um json com a lista de Servervidores conectador na Storage
        """
        api_url = '/StorageCenter/ScServer'
        api_method = 'GET'
        return self._apiRequest(api_url, api_method)    

    def getListScChassis(self, period='5m', acknowledged=''):
        """
        Esta função retorna um json com a lista de Chassis da Storage usando formato de tempo relativo
        """
        api_url = '/StorageCenter/ScChassis/GetList'        
        return self._getTimeListRelative(api_url, period, acknowledged)