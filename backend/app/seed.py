"""Execute explicitamente: python -m app.seed. Recusa qualquer banco com dados."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from .db import make_engine, writing
from .models import Product, Sale, Movement
from .schemas import MovementInput, SaleInput
from .services import add_movement, create_sale, cancel_sale

def seed():
    engine = make_engine()
    with writing(engine) as s:
        if any(s.scalar(select(func.count()).select_from(model)) for model in [Product,Sale,Movement]):
            raise SystemExit('Demonstração não carregada: o banco já contém dados. Nada foi apagado.')
        now = datetime.now(timezone.utc)
        examples = [('TEC-001','Mouse sem fio','Periféricos',8990,5),('TEC-002','Teclado compacto','Periféricos',15990,4),
            ('CAB-001','Cabo USB-C','Acessórios',2990,10),('SUP-001','Suporte para notebook','Escritório',12990,3),
            ('FON-001','Fone de ouvido','Áudio',11990,6),('HUB-001','Hub USB','Acessórios',9990,4)]
        ids=[]
        for code,name,category,price,minimum in examples:
            p=Product(code=code,name=name,category=category,price_cents=price,minimum_stock=minimum,active=True)
            s.add(p);s.flush();ids.append(p.id)
            add_movement(s,MovementInput(product_id=p.id,quantity=100,kind='inicial',reason='Estoque fictício de demonstração',occurred_at=now-timedelta(days=35)))
        for day in range(28):
            a,b=ids[day%6],ids[(day+2)%6]
            sale=create_sale(s,SaleInput(items=[dict(product_id=a,quantity=1+day%3),dict(product_id=b,quantity=1)],occurred_at=now-timedelta(days=28-day)))
            if day==5: cancel_sale(s,sale['id'])
        # Exemplo de alerta, mantendo todo o histórico.
        from .services import balance
        add_movement(s,MovementInput(product_id=ids[2],quantity=balance(s,ids[2])-7,kind='saida',reason='Ajuste fictício para demonstrar alerta'))
    print('Demonstração criada: 6 produtos, 28 vendas (uma cancelada), estoque e histórico coerentes.')
if __name__=='__main__': seed()
