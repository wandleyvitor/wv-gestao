from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timezone, timedelta
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db import make_engine
from app.main import create_app
from app.models import Movement, Sale

@pytest.fixture
def client(tmp_path,monkeypatch):
    url='sqlite:///'+str(tmp_path/'test.db')
    monkeypatch.setenv('WV_DATABASE_URL',url)
    command.upgrade(Config('alembic.ini'),'head')
    engine=make_engine(url)
    with TestClient(create_app(engine)) as c:
        yield c
    engine.dispose()

def product(c,code='A',price=101,stock=10):
    r=c.post('/api/products',json=dict(code=code,name='Produto '+code,category='Teste',price_cents=price,minimum_stock=2))
    assert r.status_code==201,r.text
    p=r.json()
    if stock:
        assert c.post('/api/movements',json=dict(product_id=p['id'],quantity=stock,kind='inicial',reason='Estoque de teste')).status_code==201
    return p

def sell(c,items,**extra):
    return c.post('/api/sales',json=dict(items=[dict(product_id=p['id'],quantity=q) for p,q in items],**extra))

def stock(c,p):
    return next(x['stock'] for x in c.get('/api/products').json() if x['id']==p['id'])

def test_multi_items_exact_money_and_history(client):
    a=product(client,price=101);b=product(client,'B',price=299)
    r=sell(client,[(a,3),(b,2)])
    assert r.status_code==201
    sale=r.json()
    assert sale['total_cents']==901
    assert [i['subtotal_cents'] for i in sale['items']]==[303,598]
    assert stock(client,a)==7 and stock(client,b)==8
    edit={k:a[k] for k in ['code','name','category','minimum_stock','active']}
    edit.update(price_cents=999,category='Outra')
    assert client.put('/api/products/'+str(a['id']),json=edit).status_code==200
    old=client.get('/api/sales?start=2020-01-01&end=2030-01-01').json()[0]
    assert old['items'][0]['unit_price_cents']==101 and old['items'][0]['category']=='Teste'

def test_insufficient_has_no_partial_write(client):
    a=product(client);b=product(client,'B',stock=1)
    before=len(client.get('/api/movements').json())
    assert sell(client,[(a,2),(b,2)]).status_code==409
    assert stock(client,a)==10 and stock(client,b)==1
    assert len(client.get('/api/movements').json())==before
    with Session(client.app.state.engine) as s: assert s.scalar(select(func.count()).select_from(Sale))==0

def test_simultaneous_sales(client):
    p=product(client,stock=1);barrier=Barrier(2)
    def attempt(_):
        barrier.wait()
        with TestClient(client.app) as c: return sell(c,[(p,1)]).status_code
    with ThreadPoolExecutor(2) as pool: codes=list(pool.map(attempt,range(2)))
    assert sorted(codes)==[201,409]
    assert stock(client,p)==0

def test_cancel_once_and_indicators(client):
    p=product(client,price=333)
    a=sell(client,[(p,2)]).json();b=sell(client,[(p,1)]).json()
    for _ in range(2):assert client.post(f"/api/sales/{a['id']}/cancel").status_code==200
    assert stock(client,p)==9
    returns=[m for m in client.get('/api/movements').json() if m['kind']=='cancelamento']
    assert len(returns)==1
    d=client.get('/api/dashboard?start=2020-01-01&end=2030-01-01').json()
    assert d['sales_count']==1 and d['revenue_cents']==333 and d['average_ticket_cents']==333
    assert d['top_products'][0]['quantity']==1
    assert d['categories']==[{'category':'Teste','revenue_cents':333}]

@pytest.mark.parametrize('quantity',[0,-1,1.5,True,'2'])
def test_invalid_quantities(client,quantity):
    p=product(client)
    assert sell(client,[(p,quantity)]).status_code==422
    assert stock(client,p)==10

def test_inactive_unique_and_negatives(client):
    p=product(client)
    payload={k:p[k] for k in ['code','name','category','price_cents','minimum_stock','active']}
    assert client.post('/api/products',json=payload).status_code==409
    assert client.post('/api/products',json={**payload,'code':'B','price_cents':-1}).status_code==422
    assert client.post('/api/products',json={**payload,'code':'B','minimum_stock':-1}).status_code==422
    assert client.put('/api/products/'+str(p['id']),json={**payload,'active':False}).status_code==200
    assert sell(client,[(p,1)]).status_code==409

def test_dates_and_backdated_stock(client):
    p=product(client)
    assert sell(client,[(p,1)],occurred_at='2020-01-01T10:00:00-03:00').status_code==409
    assert sell(client,[(p,1)],occurred_at='2026-01-01T10:00:00').status_code==422
    assert client.get('/api/dashboard?start=2026-02-01&end=2026-01-01').status_code==422

def test_csv_formula_protection(client):
    p=product(client,code='=1+1')
    url='/api/exports/products?start=2020-01-01&end=2030-01-01'
    r=client.get(url)
    assert r.status_code==200 and r.content.startswith(b'\xef\xbb\xbf')
    assert "'=1+1" in r.text

def test_local_day_boundaries(client):
    p=product(client,stock=0)
    # Às 02:30 UTC ainda é o dia anterior em Brasília.
    client.post('/api/movements',json=dict(product_id=p['id'],quantity=10,kind='inicial',reason='Teste temporal',occurred_at='2020-01-01T00:00:00Z'))
    assert sell(client,[(p,1)],occurred_at='2020-01-03T02:30:00Z').status_code==201
    d=client.get('/api/dashboard?start=2020-01-02&end=2020-01-02').json()
    assert d['sales_count']==1 and d['daily'][0]['revenue_cents']==101
    assert client.get('/api/dashboard?start=2020-01-03&end=2020-01-03').json()['sales_count']==0

def test_all_exports_and_cors(client):
    p=product(client)
    sale=sell(client,[(p,1)]).json()
    client.post(f"/api/sales/{sale['id']}/cancel")
    for kind in ['products','movements','sale-items','indicators']:
        r=client.get(f'/api/exports/{kind}?start=2020-01-01&end=2030-01-01')
        assert r.status_code==200 and r.content.startswith(b'\xef\xbb\xbf')
        assert 'attachment;' in r.headers['content-disposition']
    assert 'True' in client.get('/api/exports/sale-items?start=2020-01-01&end=2030-01-01').text
    allowed=client.options('/api/sales',headers={'Origin':'http://127.0.0.1:5173','Access-Control-Request-Method':'POST'})
    assert allowed.headers['access-control-allow-origin']=='http://127.0.0.1:5173'
    denied=client.options('/api/sales',headers={'Origin':'https://example.com','Access-Control-Request-Method':'POST'})
    assert 'access-control-allow-origin' not in denied.headers

def test_rollback_historical_exit_and_duplicate_initial(client):
    p=product(client,stock=0)
    a=dict(product_id=p['id'],quantity=5,kind='inicial',reason='Entrada de teste',occurred_at='2020-01-01T00:00:00Z')
    assert client.post('/api/movements',json=a).status_code==201
    assert client.post('/api/movements',json=a).status_code==409
    assert sell(client,[(p,4)],occurred_at='2020-01-03T12:00:00Z').status_code==201
    # Havia cinco unidades no dia 2, mas retirar duas deixaria a venda do dia 3 sem saldo.
    assert client.post('/api/movements',json={**a,'kind':'saida','quantity':2,'occurred_at':'2020-01-02T12:00:00Z'}).status_code==409
    assert stock(client,p)==1
