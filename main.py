import requests
import schedule
import time
import datetime
import os

# No proxy needed for Render

# Configuration
BOT_TOKEN = '8280620366:AAH4-kwAdQ8ySuH2-cRMssoEmEeicLZebww'
CHANNEL_ID = '@pricetokenbott'

# APIs
COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price'
WALLEX_URL = 'https://api.wallex.ir/v1/markets'
GOLD_API_URL = 'https://call3.tgju.org/ajax.json'

def get_global_prices():
    """Fetch prices in USD from CoinGecko"""
    params = {
        'ids': 'bitcoin,ethereum,ripple,binancecoin,solana,toncoin,the-open-network',
        'vs_currencies': 'usd'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(COINGECKO_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching global prices: {e}")
        return None

def get_iran_prices():
    """Fetch prices in Toman from Wallex"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(WALLEX_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        symbols = data.get('result', {}).get('symbols', {})
        
        # Get USDT price in Toman
        usdt_data = symbols.get('USDTTMN', {}).get('stats', {})
        usdt_price = usdt_data.get('lastPrice', '0')
        
        # Get Gold price per gram in Rial from tgju.org
        try:
            gold_response = requests.get(GOLD_API_URL, timeout=10)
            gold_response.raise_for_status()
            gold_data = gold_response.json()
            # Get gold price per gram (18 karat)
            gold_price_rial = gold_data.get('geram18', {}).get('p', '0')
        except Exception as e:
            print(f"Error fetching gold price: {e}")
            gold_price_rial = '0'
        
        return {
            'usdt': usdt_price,
            'gold': gold_price_rial
        }
    except Exception as e:
        print(f"Error fetching Iran prices: {e}")
        return None

def format_price(price):
    """Helper to format numbers with commas"""
    try:
        return f"{float(price):,}"
    except (ValueError, TypeError):
        return "N/A"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

def job():
    print(f"Running job at {datetime.datetime.now()}")
    
    global_data = get_global_prices()
    iran_data = get_iran_prices()

    if not global_data:
        global_data = {}
    if not iran_data:
        iran_data = {}

    # Extract Global Prices (USD)
    btc = format_price(global_data.get('bitcoin', {}).get('usd', 0))
    eth = format_price(global_data.get('ethereum', {}).get('usd', 0))
    xrp = format_price(global_data.get('ripple', {}).get('usd', 0))
    bnb = format_price(global_data.get('binancecoin', {}).get('usd', 0))
    sol = format_price(global_data.get('solana', {}).get('usd', 0))
    
    # TON Fix: Try 'toncoin' first, then 'the-open-network'
    ton_price = global_data.get('toncoin', {}).get('usd', 0)
    if not ton_price:
        ton_price = global_data.get('the-open-network', {}).get('usd', 0)
    ton = format_price(ton_price)

    # Extract Iran Prices
    try:
        usdt_raw = iran_data.get('usdt', 0)
        gold_raw = iran_data.get('gold', 0)
        
        if usdt_raw and float(usdt_raw) > 0:
            usdt_toman = format_price(float(usdt_raw))
        else:
            usdt_toman = "N/A"
            
        if gold_raw and float(gold_raw) > 0:
            gold_rial = format_price(float(gold_raw))
        else:
            gold_rial = "N/A"
    except Exception as e:
        print(f"Error formatting prices: {e}")
        usdt_toman = "N/A"
        gold_rial = "N/A"

    message = (
        f"🔴 *Market Update* 🔴\n"
        f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        f"🌍 *Global Market (USD)*\n"
        f"🟠 BTC: ${btc}\n"
        f"🔵 ETH: ${eth}\n"
        f"🟡 BNB: ${bnb}\n"
        f"🟣 SOL: ${sol}\n"
        f"⚫ XRP: ${xrp}\n"
        f"🔷 TON: ${ton}\n\n"
        
        f"💰 *Iran Market*\n"
        f"💵 USDT: {usdt_toman} T\n"
        f"🪙 Gold (per gram): {gold_rial} R\n\n"
        
        f"📢 @pricetokenbott"
    )
    
    send_telegram_message(message)

if __name__ == "__main__":
    print("Bot started...")
    # Run once immediately to verify
    job()
    
    # Schedule every 1 hour
    schedule.every(1).hours.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
