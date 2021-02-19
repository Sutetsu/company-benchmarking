import os
import tempfile
import json

import pytest

from proxy import Proxy3 as prox

alg = [["aa100", "+", "aa101 aa102 aa103"], ["aa101", "*", "va110 va112"], ["aa102", "/", "va200 2"], ["aa103", "-", "va300 10"], ["bb100", "Min", "vb100 vb101 vb102"], ["cc100", "+", "cc101 cc102"], ["cc101", "+", "cc201 cc202"], ["cc102", "+", "vc201 vc202"], ["cc201", "+", "3 4"], ["cc202", "-", "4 3"], ["va200", "+", "0 0"], ["dd100", "Abs", -3]]
kpi = ["aa100", "cc100", "va200", "bb100"]

@pytest.fixture
def client():
    db_fd, prox.api.config['DATABASE'] = tempfile.mkstemp()
    prox.api.config['TESTING'] = True

    with prox.api.test_client() as client:
        with prox.api.app_context():
            prox.db_setup()
            prox.process_algorithm(alg, kpi)
        yield client

    os.close(db_fd)
    os.unlink(prox.api.config['DATABASE'])


#Check the default descriptor
def test_descriptor(client):
    rv = client.get('/')
    assert b'Proxy for a benchmarking platform' in rv.data

#Tests the initial exchange between client and proxy
def test_initial(client):
    msg = json.dumps({'key': 6})
    headers = {'Authorization' : '(some auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    
    rv = client.post('/initial', data=msg, headers=headers)
    #Getting an id back
    assert b'{"id": ' in rv.data
    
#Tests sending the algorithm
def test_algorithm(client):
    algorithm = [["aa100", "+", "aa101 aa102 aa103"], ["aa101", "*", "va110 va112"], ["aa102", "/", "va200 2"], ["aa103", "-", "va300 10"], ["bb100", "Min", "vb100 vb101 vb102"], ["cc100", "+", "cc101 cc102"], ["cc101", "+", "cc201 cc202"], ["cc102", "+", "vc201 vc202"], ["cc201", "+", "3 4"], ["cc202", "-", "4 3"], ["va200", "+", "0 0"], ["dd100", "Abs", -3]]
    kpi_list = ['aa100', 'cc100', 'va200', 'bb100']
    headers = {'Authorization' : '(some auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    msg = json.dumps({'key': 15, 'alg': algorithm, 'kpi': kpi_list})
    
    rv = client.post('/algorithm', data=msg, headers=headers)
    assert b'ack' in rv.data
    
    
#Tests sending new values for an existing client
def test_new_values(client):
    vals = {"va110": 1, "va112": 2, "va200": 3, "va300": 4, "vb100": 5, "vb101": 6, "vb102": 7, "vc201": 8, "vc202": 9}
    cid = 1
    headers = {'Authorization' : '(some auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    msg = json.dumps({'id': str(cid), 'values': vals})
    
    rv = client.post('/values', data=msg, headers=headers)
    print('_-------------------------------------------------_')
    print('RVDATA:', rv.data)
    assert b'{"todo": [["aa102", "/", 3, 2], ["bb100", "Min", 5, 6, 7], ["dd100", "Abs", -3]]}' in rv.data
    
#Tests sending new kpi for an existing client
def test_new_kpi(client):
    kpi = {"aa100": -2.5, "bb100": 5, "cc100": 25, "va200": 3}
    cid = 1
    headers = {'Authorization' : '(some auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    msg = json.dumps({'id': str(cid), 'kpi': kpi})
    
    rv = client.post('/kpi', data=msg, headers=headers)
    print('_-------------------------------------------------_')
    print('RVDATA:', rv.data)
    assert b'ack' in rv.data
 