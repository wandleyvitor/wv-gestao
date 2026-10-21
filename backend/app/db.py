"""SQLite local; escrita serializada antes de conferir saldos."""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase):
    pass

def make_engine(url=None):
    engine = create_engine(url or os.getenv('WV_DATABASE_URL', 'sqlite:///./wv_gestao.db'),
                           connect_args={'check_same_thread': False, 'timeout': 30})
    @event.listens_for(engine, 'connect')
    def configure(conn, _):
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=30000')
    return engine

@contextmanager
def writing(engine):
    with Session(engine) as session:
        try:
            # Adquire o bloqueio ANTES de consultar saldos. Todas as mutações
            # passam por aqui, inclusive cancelamentos e mudanças de produtos.
            session.execute(text('BEGIN IMMEDIATE'))
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
