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
    Data de modificação: 26/05/2021
    Versao: 0.1.0
'''

import sys
import os
from datetime import datetime
from elasticsearch7 import Elasticsearch

