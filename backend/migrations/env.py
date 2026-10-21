from alembic import context
from app.db import make_engine, Base
from app import models
config = context.config
if context.is_offline_mode():
    context.configure(url=config.get_main_option('sqlalchemy.url'), target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
else:
    with make_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
        with context.begin_transaction(): context.run_migrations()
