# TG-Tracking-Bot
This is a telegram bot where you can monitor Ethereum wallets and receive notifications whenever a transaction is made. It currently supports Ethereum, Binance Smart Chain, Arbitrum, and Optimism. 

If you have any questions feel free to contact me on Telegram:
https://t.me/OxGCS

# Commands
/start display the welcome message and see instructions on how to use the bot.
/add add a new wallet to monitor. The wallet address must be in the correct format (starting with '0x' for the wallets and 'ETH', 'BNB', 'ARB', or 'OP' for the blockchain). Inputs without the correct format will be prompted by the bot to correct it.
/remove remove a wallet from your list. You must provide the wallet address in the correct format.
/list shows the wallets currently being tracked

# Requirements
To run the bot, you'll need to have Python 3.6 or later installed on your system, along with the following Python libraries:

- requests (for making HTTP requests to the block explorer APIs)
- web3 (for interacting with the Ethereum, BNB, Arbitrum, and Optimism blockchain)
- You will also need to get API Keys for the respective blockexplorers: Etherscan, BSCscan, Arbiscan, and Optimism Etherscan, as well as a Telegram bot token. 
