import yfinance as yf

ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1d")
print(hist)
