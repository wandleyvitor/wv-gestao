from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from fastapi import HTTPException
from sqlalchemy import select, func
from .models import Product, Sale, SaleItem, Movement

LOCAL = ZoneInfo('America/Sao_Paulo')
def timestamp(value=None):
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise HTTPException(422, 'Informe data e hora com fuso horário.')
    if value > datetime.now(timezone.utc) + timedelta(minutes=1):
        raise HTTPException(422, 'A data não pode estar no futuro.')
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds')

def balance(s, product_id):
    return s.scalar(select(func.coalesce(func.sum(Movement.quantity), 0)).where(Movement.product_id == product_id))

def product_or_fail(s, product_id):
    p = s.get(Product, product_id)
    if p is None:
        raise HTTPException(404, 'Produto não encontrado.')
    return p

def product_view(s, p):
    stock = balance(s, p.id)
    return dict(id=p.id, code=p.code, name=p.name, category=p.category,
                price_cents=p.price_cents, minimum_stock=p.minimum_stock,
                active=p.active, stock=stock, low_stock=stock <= p.minimum_stock)

def products(s, q=''):
    stmt = select(Product).order_by(Product.name)
    if q:
        stmt = stmt.where(Product.name.icontains(q, autoescape=True) | Product.code.icontains(q, autoescape=True))
    return [product_view(s, p) for p in s.scalars(stmt)]

def add_movement(s, data):
    p = product_or_fail(s, data.product_id)
    when = timestamp(data.occurred_at)
    if data.kind == 'inicial' and s.scalar(select(func.count()).select_from(Movement).where(Movement.product_id == p.id)):
        raise HTTPException(409, 'Estoque inicial só pode ser registrado antes de outras movimentações.')
    quantity = -data.quantity if data.kind == 'saida' else data.quantity
    ensure_timeline(s, p.id, when, quantity)
    m = Movement(product_id=p.id, quantity=quantity, kind=data.kind, reason=data.reason, occurred_at=when)
    s.add(m); s.flush()
    return dict(id=m.id, stock=balance(s, p.id))

def ensure_timeline(s, product_id, when, delta):
    # Uma saída retroativa também não pode tornar um saldo histórico negativo.
    events = list(s.execute(select(Movement.occurred_at, Movement.quantity).where(Movement.product_id == product_id)))
    events.append((when, delta))
    daily = defaultdict(int)
    for at, qty in events:
        daily[at] += qty
    running = 0
    for at in sorted(daily):
        running += daily[at]
        if running < 0:
            raise HTTPException(409, 'Estoque insuficiente na data informada ou em movimentações posteriores.')

def create_sale(s, data):
    when = timestamp(data.occurred_at)
    ids = [item.product_id for item in data.items]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, 'Cada produto deve aparecer uma única vez na venda.')
    checked = []
    for item in data.items:
        p = product_or_fail(s, item.product_id)
        if not p.active:
            raise HTTPException(409, f'Produto desativado: {p.name}.')
        ensure_timeline(s, p.id, when, -item.quantity)
        checked.append((p, item.quantity))
    total = sum(p.price_cents * qty for p, qty in checked)
    sale = Sale(occurred_at=when, total_cents=total)
    s.add(sale); s.flush()
    for p, qty in checked:
        s.add(SaleItem(sale_id=sale.id, product_id=p.id, product_name=p.name, category=p.category,
                      quantity=qty, unit_price_cents=p.price_cents, subtotal_cents=p.price_cents * qty))
        s.add(Movement(product_id=p.id, sale_id=sale.id, quantity=-qty, kind='venda',
                       reason=f'Venda #{sale.id}', occurred_at=when))
    s.flush()
    return sale_view(s, sale)

def sale_view(s, sale):
    items = [dict(id=i.id, product_id=i.product_id, product_name=i.product_name, category=i.category,
                  quantity=i.quantity, unit_price_cents=i.unit_price_cents, subtotal_cents=i.subtotal_cents)
             for i in s.scalars(select(SaleItem).where(SaleItem.sale_id == sale.id))]
    return dict(id=sale.id, occurred_at=sale.occurred_at, total_cents=sale.total_cents,
                canceled_at=sale.canceled_at, items=items)

def cancel_sale(s, sale_id):
    sale = s.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(404, 'Venda não encontrada.')
    if sale.canceled_at:
        return sale_view(s, sale)  # Repetir o pedido não devolve estoque novamente.
    now = timestamp()
    for item in s.scalars(select(SaleItem).where(SaleItem.sale_id == sale.id)):
        s.add(Movement(product_id=item.product_id, sale_id=sale.id, quantity=item.quantity,
                       kind='cancelamento', reason=f'Cancelamento da venda #{sale.id}', occurred_at=now))
    sale.canceled_at = now
    s.flush()
    return sale_view(s, sale)

def period(start: date, end: date):
    if start > end or (end - start).days > 3660:
        raise HTTPException(422, 'Período inválido. Use início até fim, com no máximo 10 anos.')
    a = datetime.combine(start, time.min, LOCAL).astimezone(timezone.utc).isoformat(timespec='microseconds')
    b = datetime.combine(end + timedelta(days=1), time.min, LOCAL).astimezone(timezone.utc).isoformat(timespec='microseconds')
    return a, b

def sales_in_period(s, start, end):
    a, b = period(start, end)
    return list(s.scalars(select(Sale).where(Sale.occurred_at >= a, Sale.occurred_at < b).order_by(Sale.occurred_at.desc())))

def dashboard(s, start, end):
    valid = [sale for sale in sales_in_period(s, start, end) if sale.canceled_at is None]
    revenue = sum(sale.total_cents for sale in valid)
    top, categories, daily = {}, defaultdict(int), defaultdict(int)
    for sale in valid:
        day = datetime.fromisoformat(sale.occurred_at).astimezone(LOCAL).date().isoformat()
        daily[day] += sale.total_cents
        for i in s.scalars(select(SaleItem).where(SaleItem.sale_id == sale.id)):
            top.setdefault(i.product_id, dict(product_id=i.product_id, name=i.product_name, quantity=0))['quantity'] += i.quantity
            categories[i.category] += i.subtotal_cents
    dates = []
    day = start
    while day <= end:
        dates.append(dict(date=day.isoformat(), revenue_cents=daily[day.isoformat()]))
        day += timedelta(days=1)
    n = len(valid)
    # Arredondamento half-up exato do ticket médio para o centavo.
    ticket = (2 * revenue + n) // (2 * n) if n else 0
    return dict(revenue_cents=revenue, sales_count=n, average_ticket_cents=ticket,
        top_products=sorted(top.values(), key=lambda x: (-x['quantity'], x['product_id']))[:10],
        categories=[dict(category=c, revenue_cents=v) for c, v in sorted(categories.items())],
        daily=dates, low_stock=[p for p in products(s) if p['active'] and p['low_stock']])
