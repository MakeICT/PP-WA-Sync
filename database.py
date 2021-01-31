from sqlalchemy import create_engine
engine = create_engine('sqlite:///database', echo=False)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Boolean



class Link(Base):
    __tablename__ = 'link'

    recurring_id = Column(String, primary_key=True, autoincrement=False)
    wa_id = Column(Integer)
    ended = Column(Boolean, default=False)

    def __repr__(self):
        return "<Link(recurring_id='%s', wa_id=%d)>" % (
                            self.recurring_id, self.wa_id)

class Status(Base):
    __tablename__ = 'status'

    id = Column(Integer, primary_key=True)
    skip = Column(Integer)
    complete = Column(Boolean)

    def __repr__(self):
        return "<Status(id=%d, skip=%d, complete=%b)>" % (
                        self.id, self.skip, self.complete)

class Payment(Base):
    __tablename__ = 'payment'

    pp_transaction_id = Column(String, primary_key=True, autoincrement=False)
    wa_payment_id = Column(String)

    def __repr__(self):
        return "<Payment(pp_transaction_id=%s, wa_payment_id=%s)>"


Base.metadata.create_all(engine)

session = Session()