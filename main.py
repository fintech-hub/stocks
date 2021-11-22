import models
import yfinance
from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from pydantic import BaseModel
from models import Stock
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

class StockRequest(BaseModel):
    symbol: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get('/')
def home(request: Request, symbol = None, forward_pe=None, sector=None, order=None, db: Session = Depends(get_db)):
    """
    Show all stocks in the database.
    Filters by symbol, p/e and sector if provided.
    """
    stocks = db.query(Stock)

    if symbol:
        stocks = stocks.filter(Stock.symbol == symbol)

    if forward_pe:
        stocks = stocks.filter(Stock.forward_pe > forward_pe)

    if sector:
        stocks = stocks.filter(Stock.sector == sector)

    if (order is None) or (order == 'Market Cap'):
        stocks = stocks.order_by(Stock.marketcap.desc()).all()
    elif order == 'Country':
        stocks = stocks.order_by(Stock.country).all()
    elif order == 'Sector':
        stocks = stocks.order_by(Stock.sector).all()
    elif order == 'P/E':
        stocks = stocks.order_by(Stock.forward_pe.desc()).all()
    elif order == 'Volume':
        stocks = stocks.order_by(Stock.volume.desc()).all()

    return templates.TemplateResponse("home.html", {
        "request": request,
        "stocks": stocks,
        "symbol": symbol
    })


def fetch_stock_data(symbol: str):
    """
    Background task to use yfinance and load key statistics
    """
    db = SessionLocal()

    stock = db.query(Stock).filter(Stock.symbol == symbol).first()

    yahoo_data = yfinance.Ticker(stock.symbol)

    if (stock.symbol is None) or (stock.symbol == "") or (yahoo_data.info['regularMarketPrice'] is None):
        db.delete(stock)
        db.commit()
        return None

    stock.name = yahoo_data.info['shortName']
    try:
        stock.country = yahoo_data.info['country']
    except KeyError:
        stock.country = None
    try:
        stock.sector = yahoo_data.info['sector']
    except KeyError:
        stock.sector = None
    stock.ma200 = yahoo_data.info['twoHundredDayAverage']
    stock.ma50 = yahoo_data.info['fiftyDayAverage']
    stock.price = yahoo_data.info['previousClose']
    stock.forward_pe = yahoo_data.info['forwardPE']
    stock.marketcap = yahoo_data.info['marketCap']
    stock.volume = yahoo_data.info['volume']

    db.add(stock)
    db.commit()


@app.post("/stock")
async def create_stock(stock_request: StockRequest, db: Session = Depends(get_db)):
    """
    Add one or more tickers to the database
    """
    stock = Stock()
    stock.symbol = stock_request.symbol

    if stock.symbol is None or stock.symbol == "":
        return None

    db.add(stock)
    db.commit()

    return {
        "code": "success",
        "message": "stock was added to the database"
    }


@app.post("/fetchall")
async def fetchall(stock_request: StockRequest, background_tasks: BackgroundTasks):
    """
    Get yfinance for update all symbols
    """
    stock = Stock()
    stock.symbol = stock_request.symbol

    if stock.symbol is None or stock.symbol == "":
        return None

    background_tasks.add_task(fetch_stock_data, stock.symbol)

    return {
        "code": "success",
        "message": "fetch all stocks"
    }
