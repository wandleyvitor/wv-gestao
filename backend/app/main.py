from datetime import date, timedelta
import csv
import io
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from .db import make_engine, writing
from .models import Product, SaleItem, Movement
from .schemas import ProductInput, SaleInput, MovementInput
from . import services as svc

def csv_response(rows, filename, fields):
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=fields, delimiter=';')
    writer.writeheader()
    for row in rows:
        safe = {}
        for key in fields:
            value = row.get(key, '')
            # Aspas CSV não impedem fórmulas. Neutraliza também espaços e
            # caracteres de controle que precedem os operadores de planilha.
            if isinstance(value, str) and (value.lstrip(' \t\r\n\ufeff').startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n'))):
                value = "'" + value
            safe[key] = value
        writer.writerow(safe)
    return Response('\ufeff' + buf.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="{filename}.csv"'})

def create_app(engine=None):
    app = FastAPI(title='WV Gestão — demonstração local', version='1.0.0')
    app.state.engine = engine or make_engine()
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
                       allow_methods=['GET', 'POST', 'PUT'], allow_headers=['Content-Type'])

    @app.exception_handler(RequestValidationError)
    async def invalid(_, exc):
        return JSONResponse(status_code=422, content={'detail': 'Confira os campos: textos obrigatórios, valores não negativos e quantidades inteiras positivas.'})

    @app.exception_handler(IntegrityError)
    async def conflict(_, exc):
        return JSONResponse(status_code=409, content={'detail': 'Código já cadastrado ou registro incompatível com as regras do banco.'})

    @app.exception_handler(OperationalError)
    async def unavailable(_, exc):
        return JSONResponse(status_code=503, content={'detail': 'Banco indisponível ou ocupado. Confira as migrações e tente novamente.'})

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'mode': 'Demonstração local com dados fictícios'}

    @app.get('/api/products')
    def products(q: str = Query('', max_length=120)):
        with Session(app.state.engine) as s:
            return svc.products(s, q)

    @app.post('/api/products', status_code=201)
    def add_product(data: ProductInput):
        with writing(app.state.engine) as s:
            p = Product(**data.model_dump()); s.add(p); s.flush()
            return svc.product_view(s, p)

    @app.put('/api/products/{product_id}')
    def edit_product(product_id: int, data: ProductInput):
        with writing(app.state.engine) as s:
            p = svc.product_or_fail(s, product_id)
            for key, value in data.model_dump().items():
                setattr(p, key, value)
            s.flush()
            return svc.product_view(s, p)

    @app.get('/api/movements')
    def movements():
        with Session(app.state.engine) as s:
            return movement_rows(s)

    @app.post('/api/movements', status_code=201)
    def add_movement(data: MovementInput):
        with writing(app.state.engine) as s:
            return svc.add_movement(s, data)

    @app.get('/api/sales')
    def sales(start: date, end: date):
        with Session(app.state.engine) as s:
            return [svc.sale_view(s, sale) for sale in svc.sales_in_period(s, start, end)]

    @app.post('/api/sales', status_code=201)
    def add_sale(data: SaleInput):
        with writing(app.state.engine) as s:
            return svc.create_sale(s, data)

    @app.post('/api/sales/{sale_id}/cancel')
    def cancel(sale_id: int):
        with writing(app.state.engine) as s:
            return svc.cancel_sale(s, sale_id)

    @app.get('/api/dashboard')
    def indicators(start: date, end: date):
        with Session(app.state.engine) as s:
            return svc.dashboard(s, start, end)

    @app.get('/api/exports/{kind}')
    def export(kind: str, start: date, end: date):
        with Session(app.state.engine) as s:
            svc.period(start, end)
            if kind == 'products':
                return csv_response(svc.products(s), 'produtos', ['id','code','name','category','price_cents','minimum_stock','active','stock'])
            if kind == 'movements':
                return csv_response(movement_rows(s), 'movimentacoes', ['id','product_id','product_name','quantity','kind','reason','occurred_at','sale_id'])
            if kind == 'sale-items':
                rows = []
                for sale in svc.sales_in_period(s, start, end):
                    for i in svc.sale_view(s, sale)['items']:
                        rows.append(dict(**i, sale_id=sale.id, occurred_at=sale.occurred_at, canceled=bool(sale.canceled_at)))
                return csv_response(rows, 'itens_vendas', ['sale_id','occurred_at','canceled','product_id','product_name','category','quantity','unit_price_cents','subtotal_cents'])
            if kind == 'indicators':
                d = svc.dashboard(s, start, end)
                rows = [dict(tipo='resumo', referencia='periodo', indicador=k, valor=d[k]) for k in ['revenue_cents','sales_count','average_ticket_cents']]
                rows += [dict(tipo='diario',referencia=x['date'],indicador='revenue_cents',valor=x['revenue_cents']) for x in d['daily']]
                rows += [dict(tipo='categoria',referencia=x['category'],indicador='revenue_cents',valor=x['revenue_cents']) for x in d['categories']]
                rows += [dict(tipo='produto',referencia=x['name'],indicador='quantity',valor=x['quantity']) for x in d['top_products']]
                return csv_response(rows, 'indicadores', ['tipo','referencia','indicador','valor'])
            raise HTTPException(404, 'Exportação não encontrada.')
    return app

def movement_rows(s):
    return [dict(id=m.id, product_id=m.product_id, product_name=name, quantity=m.quantity,
                 kind=m.kind, reason=m.reason, occurred_at=m.occurred_at, sale_id=m.sale_id)
            for m, name in s.execute(select(Movement, Product.name).join(Product).order_by(Movement.occurred_at.desc(),Movement.id.desc()))]

app = create_app()
