from sqlalchemy import Column, Numeric, Integer, String

from database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    country = Column(String)
    sector = Column(String)
    forward_pe = Column(Numeric(10, 2))
    marketcap = Column(Numeric(10, 2))
    ma200 = Column(Numeric(10, 2))
    ma50 = Column(Numeric(10, 2))
    price = Column(Numeric(10, 2))
    volume = Column(Numeric(10, 2))
