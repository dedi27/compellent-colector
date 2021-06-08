#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
    Created on 24 de mai de 2021
    @author: Jardel F. F. de Araujo
    
    <DESCRICAO>
    Sintaxe:
        python mailqueue_metrics.py
    
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
    Data de criação: 24/05/2021
    Data de modificação: 04/06/2021
    Versao: 0.1.0
'''

import sys
import os
import logging

import compellent_collector.client as scc
import argparse
import json
from pyutilsunifique import pyutils
from requests.models import stream_decode_response_unicode
from datetime import datetime
from elasticsearch import Elasticsearch


# Definições de log stdout
stdout_log = logging.getLogger()
stdout_log.setLevel(logging.WARN)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter('%(message)s'))
stdout_log.addHandler(log_handler)

def main():
    stdout_log.setLevel(logging.INFO)
    parser = argparse.ArgumentParser(prog='unifique-compellent-collector', description='Programa para coletar métricas da Storage Dell Compellent.')
    args = parser.parse_args()
    dellSC = scc.Client(host='192.168.110.10', username='Admin', password='Dellsvcs1', verify_SSL=False)
    raw_json = json.dumps(dellSC.getScServer(), indent=4)
    stdout_log.info(pyutils.jsonPrint(raw_json, colorful=True))
    raw_json = json.dumps(dellSC.getScCapabilities(), indent=4)
    stdout_log.info(pyutils.jsonPrint(raw_json, colorful=True))  
    raw_json = json.dumps(dellSC.getScConfiguration(), indent=4)
    stdout_log.info(pyutils.jsonPrint(raw_json, colorful=True))

    raw_json = json.dumps(dellSC.getListScChassisRelative(), indent=4)
    stdout_log.info(pyutils.jsonPrint(raw_json, colorful=True))


if __name__ == "main":
    main()
