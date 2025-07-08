from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv
from binance.enums import *
import os
from logger import setup_logger
from bot import BinanceBot
from InquirerPy import inquirer
from datetime import datetime

load_dotenv()
console = Console()

bot = BinanceBot(
    api_key=os.getenv('BINANCE_TESTNET_API_KEY'),
    api_secret=os.getenv('BINANCE_TESTNET_API_SECRET'),
    testnet=True
)

def display_order_result(order):
    table = Table(title="Order Result")
    table.add_column("Field",style = "cyan", no_wrap = True)
    table.add_column("Value", style="magenta")
    for key in ["symbol", "side", "type", "status", "price", "executedQty"]:
        table.add_row(key, str(order.get(key, "-")))
    console.print(table)

def display_balance(balance):
    table = Table(title="USDT Balance")
    table.add_column("Asset", style="green")
    table.add_column("Balance", style="yellow")
    table.add_row(balance.get("asset", "USDT"), balance.get("balance", "0"))
    console.print(table)

def display_orders(orders):
    if not orders:
        console.print("[bold red]No orders found.[/bold red]")
        return
    table = Table(title="All Orders")
    table.add_column("Order ID", style="cyan")
    table.add_column("Symbol", style="bold yellow")
    table.add_column("Side", style="green")
    table.add_column("Type")
    table.add_column("Status", style="bold magenta")
    table.add_column("Qty")
    table.add_column("Avg Price", justify="right")
    table.add_column("Filled", justify="right")
    table.add_column("Time")

    for order in orders:
        table.add_row(
            str(order.get("orderId", "")),
            order.get("symbol", ""),
            order.get("side", ""),
            order.get("type", ""),
            order.get("status", ""),
            order.get("origQty", ""),
            order.get("avgPrice", ""),
            order.get("executedQty", ""),
            datetime.fromtimestamp(order.get("updateTime", "")/1000).strftime('%Y-%m-%d %H:%M:%S')
        )

    console = Console()
    console.print(table)

def main():
    console.print("\n[bold blue]Welcome to Binance Futures CLI Bot[/bold blue]\n")
    while True:
        action = inquirer.select(
            message="Choose an action:",
            choices=["Buy", "Sell", "Balance", "All Orders", "Exit"]
        ).execute()

        if action in ["Buy", "Sell"]:
            symbol = inquirer.text(message="Enter trading pair (e.g., BTCUSDT):").execute().upper()
            order_type = inquirer.select(message="Order type:", choices=["MARKET", "LIMIT"]).execute()
            quantity = float(inquirer.text(message="Enter quantity:").execute())
            price = None

            if order_type == "LIMIT":
                price = float(inquirer.text(message="Enter limit price:").execute())

            order = bot.place_order(
                symbol=symbol,
                side=SIDE_BUY if action == "Buy" else SIDE_SELL,
                order_type=ORDER_TYPE_MARKET if order_type == "MARKET" else ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=price
            )
            display_order_result(order)

        elif action == "Balance":
            symbols = bot.get_available_symbols()
            selected_symbol = inquirer.fuzzy(
                message="Search and select a trading symbol:",
                choices=symbols,
            ).execute() 
            
            base_asset = selected_symbol.replace("USDT", "")
            balance = bot.get_balance(base_asset)
            if not balance:
                console.print(f"[bold red]No balance found for {base_asset}[/bold red]")
            else:    
                display_balance(balance)

        elif action == "All Orders":
            orders = bot.get_all_orders()
            display_orders(orders)

        elif action == "Exit":
            console.print("\n[bold red]Goodbye![/bold red]")
            break

if __name__ == "__main__":
    main()





