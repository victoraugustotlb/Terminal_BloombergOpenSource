import os
import time
import yfinance as yf
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_menu_renderable():
    # Retorna o texto formatado para o Panel
    conteudo = (
        "[bold cyan]Terminal Bloomberg OpenSource[/bold cyan]\n\n"
        "[1] Consultar Cotação de Ativo\n"
        "[2] Resumo do Mercado (B3 / S&P500)\n"
        "[3] Sair"
    )
    return Panel(
        conteudo,
        title="[bold yellow]FINANCE CLI[/bold yellow]",
        subtitle="[dim]v0.1.0[/dim]",
        border_style="green",
        expand=False
    )

def consultar_ativo():
    ticker_input = console.input("\n[bold]Digite o ticker do ativo (ex: PETR4.SA, AAPL): [/bold]").strip().upper()
    if not ticker_input:
        return

    with console.status(f"[cyan]Buscando dados de {ticker_input}...[/cyan]"):
        try:
            ticker = yf.Ticker(ticker_input)
            info = ticker.fast_info
            preco = info.last_price
            moeda = info.currency
            
            table = Table(title=f"Dados: {ticker_input}")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            table.add_row("Último Preço", f"{preco:.2f} {moeda}")
            table.add_row("Máxima do Dia", f"{info.day_high:.2f} {moeda}")
            table.add_row("Mínima do Dia", f"{info.day_low:.2f} {moeda}")

            console.print(table)
        except Exception as e:
            console.print(f"[red]Erro ao buscar ativo: {e}[/red]")

def main():
    while True:
        limpar_tela()
        console.print(get_menu_renderable())
        
        opcao = console.input("\n[bold yellow]Selecione uma opção > [/bold yellow]").strip()

        match opcao:
            case "1":
                consultar_ativo()
                input("\nPressione ENTER para voltar ao menu...")
            case "2":
                console.print("\n[dim]Funcionalidade em desenvolvimento...[/dim]")
                time.sleep(1.5)
            case "3":
                console.print("[bold red]\nEncerrando terminal... Até mais![/bold red]")
                break
            case _:
                console.print("[red]\nOpção inválida![/red]")
                time.sleep(1.2)

if __name__ == "__main__":
    main()
