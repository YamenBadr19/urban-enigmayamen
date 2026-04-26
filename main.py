import os
import time
import threading
import requests
import telebot
from kucoin.client import Trade, Market, User

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
KU_KEY = os.getenv('KU_KEY')
KU_SECRET = os.getenv('KU_SECRET')
KU_PASS = os.getenv('KU_PASS')
CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
trade_client = Trade(key=KU_KEY, secret=KU_SECRET, passphrase=KU_PASS)
market_client = Market()
user_client = User(key=KU_KEY, secret=KU_SECRET, passphrase=KU_PASS)

ENGINE_ON = False
SYMBOLS = ['XAUT-USDT', 'BTC-USDT', 'ETH-USDT']
TRADE_AMOUNT_USDT = 95

def send(msg):
    bot.send_message(CHAT_ID, msg)

def get_balance():
    try:
        accounts = user_client.get_account_list()
        usdt = next((float(x['balance']) for x in accounts if x['currency']=='USDT' and x['type']=='trade'), 0)
        return usdt
    except:
        return 0

def trade_loop():
    global ENGINE_ON
    while ENGINE_ON:
        try:
            usdt = get_balance()
            if usdt < TRADE_AMOUNT_USDT:
                send(f'رصيد غير كافي: {usdt:.2f} USDT')
                time.sleep(60)
                continue
            for symbol in SYMBOLS:
                if not ENGINE_ON: break
                price = float(market_client.get_ticker(symbol)['price'])
                size = str(round(TRADE_AMOUNT_USDT / price, 6))
                order = trade_client.create_market_order(symbol, 'buy', size=size)
                send(f'شراء {symbol} بسعر {price}')
                tp = price * 1.008
                sl = price * 0.996
                while ENGINE_ON:
                    time.sleep(5)
                    now_price = float(market_client.get_ticker(symbol)['price'])
                    if now_price >= tp:
                        trade_client.create_market_order(symbol, 'sell', size=size)
                        send(f'بيع ربح {symbol} بسعر {now_price}')
                        break
                    if now_price <= sl:
                        trade_client.create_market_order(symbol, 'sell', size=size)
                        send(f'ستوب لوز {symbol} بسعر {now_price}')
                        break
                time.sleep(10)
            time.sleep(30)
        except Exception as e:
            send(f'خطأ: {str(e)[:100]}')
            time.sleep(30)

@bot.message_handler(commands=['start_engine'])
def start_engine(message):
    global ENGINE_ON
    if str(message.chat.id) != CHAT_ID: return
    if ENGINE_ON:
        send('المحرك شغال')
        return
    ENGINE_ON = True
    threading.Thread(target=trade_loop).start()
    send('تم تشغيل المحرك V13')

@bot.message_handler(commands=['stop_engine'])
def stop_engine(message):
    global ENGINE_ON
    if str(message.chat.id) != CHAT_ID: return
    ENGINE_ON = False
    send('تم ايقاف المحرك')

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    if str(message.chat.id) != CHAT_ID: return
    send(f'رصيدك: {get_balance():.2f} USDT')

print(f"Bot started. Owner CHAT_ID: {CHAT_ID}")
bot.polling()
