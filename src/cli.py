from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from dotenv import load_dotenv
from binance.enums import *
import os
from src.logger import setup_logger
from src.bot import BinanceBot
from InquirerPy import inquirer
from datetime import datetime

load_dotenv()
setup_logger()
log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')
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
    for key in ["symbol", "side", "type", "status", "price", "executedQty","stopPrice","workingType","origQty"]:
        table.add_row(key, str(order.get(key, "-")))
    console.print(table)

    console.print("\n" * 2)

def get_fuzzy_symbol(symbols : list) -> any: 
    return inquirer.fuzzy(
        message="Search and select a trading symbol:",
        choices=symbols,
        default="BTCUSDT",
        max_height=10,
    ).execute().upper()

def display_balance(balance_data):
    table = Table(title="Account Balance Summary", show_header=True, header_style="bold magenta")
    table.add_column("Asset", style="bold green")
    table.add_column("Wallet Balance", justify="right", style="yellow")
    table.add_column("Available", justify="right", style="cyan")
    table.add_column("Max Withdraw", justify="right", style="bright_blue")
    table.add_column("Unrealized PnL", justify="right", style="red")

    if isinstance(balance_data, dict):
        # Single asset balance
        table.add_row(
            balance_data.get("asset", "-"),
            balance_data.get("balance", "-"),
            balance_data.get("availableBalance", "-"),
            balance_data.get("maxWithdrawAmount", "-"),
            balance_data.get("crossUnPnl", "-"),
        )
    elif isinstance(balance_data, list):
        # Multiple assets
        for bal in balance_data:
            table.add_row(
                bal.get("asset", "-"),
                bal.get("balance", "-"),
                bal.get("availableBalance", "-"),
                bal.get("maxWithdrawAmount", "-"),
                bal.get("crossUnPnl", "-"),
            )

    console.print(table)
    console.print("\n" * 2)

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

    console.print(table)

    console.print("\n" * 2)

def view_logs(log_file=log_file):
    if not os.path.exists(log_file):
        console.print("[bold red]No logs found[/bold red]")
        return

    with open(log_file, "r") as f:
        logs = f.readlines()

    if not logs:
        console.print("[yellow]No logs yet.[/yellow]")
        return

    PAGE_SIZE = 10  
    total_lines = len(logs)
    page = 0

    while True:
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        chunk = logs[start:end]

        if not chunk:
            console.print("[green]End of logs.[/green]")
            break

        table = Table(title=f"📄 Logs (Lines {start + 1}-{min(end, total_lines)} of {total_lines})", box=None)
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("Level", style="magenta", no_wrap=True)
        table.add_column("Message", style="white")

        for line in chunk:
            parts = line.strip().split(" - ", maxsplit=2)
            if len(parts) == 3:
                time, level, msg = parts
                table.add_row(time, level, msg)
            else:
                table.add_row("-", "-", line.strip())

        console.print(table)

        if end >= total_lines:
            break

        # Prompt for next page
        next_page = Prompt.ask("\nPress [bold green]Enter[/bold green] to show more, or [bold red]q[/bold red] to quit", default="")
        if next_page.lower() == 'q':
            break
        page += 1

    console.print("\n" * 2)

def main(): 
    console.print("\n[bold blue]Welcome to Binance Futures CLI Bot[/bold blue]\n")
    if not bot.client_ping():
        return
    while True:
        action = inquirer.select(
            message="Choose an action:",
            choices=[
                {"name": "Buy", "value": "Buy"},
                {"name": "Sell", "value": "Sell"},
                {"name": "TWAP Order", "value": "TWAP"},
                {"name": "Grid Orders", "value": "Grid"},
                {"name": "Balance", "value": "Balance"},
                {"name": "View Orders", "value": "All Orders"},
                {"name": "View Logs", "value": "View Logs"},
                {"name": "Exit", "value": "Exit"},
                ],
            default="Buy",
            instruction="Use ↑/↓ to navigate and Enter to select"
        ).execute()

        if action in ["Buy", "Sell"]:
            symbol = get_fuzzy_symbol(bot.get_trading_pairs())
            order_type = inquirer.select(message="Order type:", choices=["MARKET", "LIMIT","STOP_LIMIT"]).execute()
            quantity = float(inquirer.text(message="Enter quantity:").execute())
            price = None

            if order_type == "LIMIT":
                price = float(inquirer.text(message="Enter limit price:").execute())

            elif order_type == "STOP_LIMIT":
                stop_price = float(inquirer.text(message="Enter stop price: ").execute())
                price = float(inquirer.text(message="Enter limit price: ").execute())
            
            order = bot.place_order(
                symbol=symbol,
                side=SIDE_BUY if action == "Buy" else SIDE_SELL,
                order_type=ORDER_TYPE_MARKET if order_type == "MARKET" else ORDER_TYPE_LIMIT,
                quantity=quantity,
                price=price,
                stopPrice = stop_price if order_type == "STOP_LIMIT" else None
            )
            
            display_order_result(order)

        elif action == "TWAP":
            symbol = get_fuzzy_symbol(bot.get_trading_pairs())
            order_type = inquirer.select(
                message="Order type:",
                choices=["MARKET", "LIMIT", "STOP_LIMIT"]
            ).execute()

            side = inquirer.select(message="Order side:", choices=["BUY", "SELL"]).execute()
            total_quantity = float(inquirer.text(message="Enter total quantity:").execute())
            intervals = int(inquirer.text(message="Number of intervals:").execute())
            delay_sec = int(inquirer.text(message="Delay (seconds) between each order:").execute())

            kwargs = {
                "symbol": symbol,
                "side": SIDE_BUY if side == "BUY" else SIDE_SELL,
                "quantity": total_quantity,
                "intervals": intervals,
                "dealy_sec": delay_sec,
                "order_type": ORDER_TYPE_MARKET if order_type == "MARKET" else
                            ORDER_TYPE_LIMIT if order_type == "LIMIT" else
                            FUTURE_ORDER_TYPE_STOP
            }

            if order_type == "LIMIT":
                base_price = float(inquirer.text(message="Enter base price:").execute())
                price_step = float(inquirer.text(message="Enter price step per order:").execute())
                kwargs.update({"base_price": base_price, "price_step": price_step})

            elif order_type == "STOP_LIMIT":
                base_price = float(inquirer.text(message="Enter base limit price:").execute())
                base_stop_price = float(inquirer.text(message="Enter base stop price:").execute())
                price_step = float(inquirer.text(message="Enter price step per order:").execute())
                stop_step = float(inquirer.text(message="Enter stop price step per order:").execute())
                kwargs.update({
                    "base_price": base_price,
                    "base_stop_price": base_stop_price,
                    "price_step": price_step,
                    "stop_step": stop_step
                })

            twap_orders = bot.place_twap_order(**kwargs)

            if len(twap_orders)!=0:
                console.rule("[bold green]TWAP Orders Placed[/bold green]")
                for order in twap_orders:
                    display_order_result(order)

        elif action == "Grid":
            symbol = get_fuzzy_symbol(bot.get_trading_pairs())
            side = inquirer.select(message="Order type:", choices=["BUY","SELL"]).execute()
            base_price = float(inquirer.text(message="Enter base price:").execute())
            quantity = float(inquirer.text(message="Quantity per order:").execute())
            grid_size = int(inquirer.text(message="Number of buy/sell pairs:").execute())
            stop_percent = float(inquirer.text(message="Price stop percent (e.g., 0.5):").execute())

            grid_orders = bot.place_grid_orders(
                symbol=symbol,
                side=side,
                base_price=base_price,
                quantity=quantity,
                grid_size=grid_size,
                stop_percent=stop_percent
            )

            if len(grid_orders) != 0 :
                console.rule("[bold cyan]Grid Orders Placed[/bold cyan]")
                for order in grid_orders:
                    display_order_result(order)
            
        elif action == "Balance":    
            accounts = bot.get_balance()
            if not accounts:
                console.print(f"[bold red]No account found [/bold red]")
            else:    
                display_balance(accounts)

        elif action == "All Orders":
            orders = bot.get_all_orders()
            display_orders(orders)

        elif action == "Exit":
            console.print("\n[bold red]Goodbye![/bold red]")
            break

        elif action == "View Logs":
            view_logs()

if __name__ == "__main__":
    main()





