import requests
import re
import time
import json
import os.path
from web3 import Web3

# Update the below with your own API keys and Telegram bot token
ETHERSCAN_API_KEY = '<add_your_key_here>'
BSCSCAN_API_KEY = '<add_your_key_here>'
ARBISCAN_API_KEY = '<add_your_key_here>'
OPTIMSIM_API_KEY = '<add_your_key_here>'
TELEGRAM_BOT_TOKEN = '<add_your_bot_token_here>'
TELEGRAM_CHAT_ID = '<add_your_chat_id_here>'

# Define some helper functions
def get_wallet_transactions(wallet_address, blockchain):
    if blockchain == 'eth':
        url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}'
    elif blockchain == 'bnb':
        url = f'https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={BSCSCAN_API_KEY}'
    elif blockchain == 'arb':
        url = f'https://api.arbiscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ARBISCAN_API_KEY}'
    elif blockchain == 'op':
        url = f'https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={BSCSCAN_API_KEY}'
    else:
        raise ValueError('Blockchain not supported')

    response = requests.get(url)
    data = json.loads(response.text)

    result = data.get('result', [])
    if not isinstance(result, list):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching transactions for {wallet_address} on {blockchain.upper()} blockchain: {data}")
        return []

    return result

def send_telegram_notification(message, value, usd_value, tx_hash, blockchain):
    if blockchain == 'eth':
        etherscan_link = f'<a href="https://etherscan.io/tx/{tx_hash}">Etherscan</a>'
    elif blockchain == 'bnb':
        etherscan_link = f'<a href="https://bscscan.com/tx/{tx_hash}">BscScan</a>'
    else:
        raise ValueError('Invalid blockchain specified')

    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': f'{TELEGRAM_CHAT_ID}', 'text': f'{message}: {etherscan_link}\nValue: {value:.6f} {blockchain.upper()} (${usd_value:.2f})',
               'parse_mode': 'HTML'}
    response = requests.post(url, data=payload)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram notification sent with message: {message}, value: {value} {blockchain.upper()} (${usd_value:.2f})")
    return response

def monitor_wallets():
    watched_wallets = set()
    file_path = "watched_wallets.txt"
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    latest_tx_hashes = {}
    latest_tx_hashes_path = "latest_tx_hashes.json"
    if os.path.exists(latest_tx_hashes_path):
        with open(latest_tx_hashes_path, "r") as f:
            latest_tx_hashes = json.load(f)

    last_run_time = 0
    last_run_time_path = "last_run_time.txt"
    if os.path.exists(last_run_time_path):
        with open(last_run_time_path, "r") as f:
            last_run_time = int(f.read())

    while True:
        try:
            # Fetch current ETH and BNB prices in USD from CoinGecko API
            eth_price_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbinancecoin&vs_currencies=usd'
            response = requests.get(eth_price_url)
            data = json.loads(response.text)
            eth_price = data['ethereum']['usd']
            bnb_price = data['binancecoin']['usd']

            # Read from file
            with open(file_path, 'r') as f:
                watched_wallets = set(f.read().splitlines())

            for wallet in watched_wallets:
                blockchain, wallet_address = wallet.split(':')
                transactions = get_wallet_transactions(wallet_address, blockchain)
                for tx in transactions:
                    tx_hash = tx['hash']
                    tx_time = int(tx['timeStamp'])

                    if tx_hash not in latest_tx_hashes and tx_time > last_run_time:
                        if tx['to'].lower() == wallet_address.lower():
                            value = float(tx['value']) / 10**18 # Convert from wei to ETH or BNB
                            usd_value = value * (eth_price if blockchain == 'eth' else bnb_price) # Calculate value in USD
                            message = f'Incoming tx detected on {wallet_address}'
                            send_telegram_notification(message, value, usd_value, tx['hash'], blockchain)
                            #print(f'\n{message}, Value: {value} {blockchain.upper()}, ${usd_value:.2f}\n')
                        elif tx['from'].lower() == wallet_address.lower():
                            value = float(tx['value']) / 10**18 # Convert from wei to ETH or BNB
                            usd_value = value * (eth_price if blockchain == 'eth' else bnb_price) # Calculate value in USD
                            message = f'Outgoing tx detected on {wallet_address}'
                            send_telegram_notification(message, value, usd_value, tx['hash'], blockchain)
                            #print(f'\n{message}, Value: {value} {blockchain.upper()}, ${usd_value:.2f}\n')

                        latest_tx_hashes[tx_hash] = int(tx['blockNumber'])

            # Save latest_tx_hashes to file
            with open(latest_tx_hashes_path, "w") as f:
                json.dump(latest_tx_hashes, f)

            # Update last_run_time
            last_run_time = int(time.time())
            with open(last_run_time_path, "w") as f:
                f.write(str(last_run_time))

            # Sleep for 1 minute
            time.sleep(60)
        except Exception as e:
            print(f'An error occurred: {e}')
            # Sleep for 10 seconds before trying again
            time.sleep(10)

def add_wallet(wallet_address, blockchain):
    file_path = "watched_wallets.txt"
    with open(file_path, 'a') as f:
        f.write(f'{blockchain}:{wallet_address}\n')

def remove_wallet(wallet_address, blockchain):
    file_path = "watched_wallets.txt"
    temp_file_path = "temp.txt"
    with open(file_path, 'r') as f, open(temp_file_path, 'w') as temp_f:
        for line in f:
            if line.strip() != f'{blockchain}:{wallet_address}':
                temp_f.write(line)
    os.replace(temp_file_path, file_path)

# Define command handlers for the TG bot
def start(update, context):
    message = """
Welcome to the TG Crypto Wallet Tracking Bot!

Use /add <blockchain> <wallet_address> to add a new wallet to monitor.

Example: /add ETH 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /add BNB 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /add ARB 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /add OP 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

Use /remove <blockchain> <wallet_address> to stop monitoring a wallet.

Example: /remove ETH 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /remove BNB 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /remove ARB 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
         /remove OP 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

Use /list <blockchain> to see all wallets you track for a particular blockchain.

Example: /list ETH or just /list

    """
    context.bot.send_message(chat_id=update.message.chat_id, text=message)

def add(update, context):
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id, text="Please add a blockchain and wallet address to track.")
        return

    blockchain = context.args[0].lower()
    wallet_address = context.args[1]

    # Check if the wallet address is in the correct format for the specified blockchain
    if blockchain == 'eth':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Ethereum wallet address.")
            return
    elif blockchain == 'bnb':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Binance Smart Chain wallet address.")
            return
    elif blockchain == 'arb':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Arbitrum wallet address.")
            return
    elif blockchain == 'op':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Optimism wallet address.")
            return
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
        return
    
    add_wallet(wallet_address, blockchain)
    message = f'Successfully added {wallet_address} to the list of watched {blockchain.upper()} wallets.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)

def remove(update, context):
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id, text="Please provide a blockchain and wallet address to remove.\nUsage: /remove ETH 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        return
    blockchain = context.args[0].lower()
    wallet_address = context.args[1]
    remove_wallet(wallet_address, blockchain)
    message = f'Successfully removed {wallet_address} from the list of watched {blockchain.upper()} wallets.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)

def list_wallets(update, context):
    with open("watched_wallets.txt", "r") as f:
        wallets = [line.strip() for line in f.readlines()]
    if wallets:
        eth_wallets = []
        bnb_wallets = []
        arb_wallets = []
        op_wallets = []
        for wallet in wallets:
            blockchain, wallet_address = wallet.split(':')
            if blockchain == 'eth':
                eth_wallets.append(wallet_address)
            elif blockchain == 'bnb':
                bnb_wallets.append(wallet_address)
            elif blockchain == 'arb':
                arb_wallets.append(wallet_address)
            else:
                op_wallets.append(wallet_address)

        message = "The following wallets are currently being tracked\n"
        message += "\n"
        if eth_wallets:
            message += "Ethereum Wallets:\n"
            for i, wallet in enumerate(eth_wallets):
                message += f"{i+1}. {wallet}\n"
            message += "\n"
        if bnb_wallets:
            message += "Binance Coin Wallets:\n"
            for i, wallet in enumerate(bnb_wallets):
                message += f"{i+1}. {wallet}\n"
        if arb_wallets:
            message += "Arbitrum Wallets:\n"
            for i, wallet in enumerate(arb_wallets):
                message += f"{i+1}. {wallet}\n"
        if op_wallets:
            message += "Optimism Wallets:\n"
            for i, wallet in enumerate(op_wallets):
                message += f"{i+1}. {wallet}\n"
        context.bot.send_message(chat_id=update.message.chat_id, text=message)
    else:
        message = "There are no wallets currently being tracked."
        context.bot.send_message(chat_id=update.message.chat_id, text=message)

# Configure TG Bot
from telegram.ext import Updater, CommandHandler

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define command handlers
start_handler = CommandHandler('start', start)
add_handler = CommandHandler('add', add)
remove_handler = CommandHandler('remove', remove)
list_handler = CommandHandler('list', list_wallets)

# Add command handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(remove_handler)
dispatcher.add_handler(list_handler)

updater.start_polling()
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tracking bot started.")

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tracking wallets...")
monitor_wallets()
