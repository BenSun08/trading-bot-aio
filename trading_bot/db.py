from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date
)

# __all__ = ['question', 'choice', 'scores']
__all__ = ['scores']

meta = MetaData()

# question = Table(
#     'question', meta,

#     Column('id', Integer, primary_key=True),
#     Column('question_text', String(200), nullable=False),
#     Column('pub_data', Date, nullable=False),
# )

# choice = Table(
#     'choice', meta,

#     Column('id', Integer, primary_key=True),
#     Column('choice_text', String(200), nullable=False),
#     Column('votes', Integer, server_default="0", nullable=False),

#     Column('question_id', Integer, ForeignKey('question.id', ondelete='CASCADE')),
# )

scores = Table(
    'scores', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('topic', String(200), nullable=False),
    Column('date', String(200), nullable=False),
    Column('articles', String(200000), nullable=False),
    Column('score', Integer, nullable=False),
)

async def pg_context(app):
    conf = app['config']['postgres']
    engine = await create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine

    yield

    app['db'].close()
    await app['db'].wait_closed()
