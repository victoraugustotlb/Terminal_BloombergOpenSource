from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yfinance as yf

console = Console()
tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA", "BBAS3.SA"]

dados = yf.download(tickers, period="5d", progress=False)["Close"]
retorno = ((dados.iloc[-1] - dados.iloc[0]) / dados.iloc[0]) * 100
ranking = retorno.sort_values(ascending=False)

tabela = Table(show_header=True, header_style="bold magenta")
tabela.add_column("Ativo", style="cyan")
tabela.add_column("Variação (5d)", justify="right")

for ativo, valor in ranking.items():
    estilo_cor = "green" if valor >= 0 else "red"
    tabela.add_row(ativo, f"[{estilo_cor}]{valor:+.2f}%[/{estilo_cor}]")

console.print(Panel(tabela, title="[bold yellow]Destaques do Mercado[/bold yellow]", expand=False))

####
console = Console()

input_ticker = input("Digite o ticker da ação (ex: PETR4.SA): ")
# 1. Instanciando uma ação da B3
acao = yf.Ticker(input_ticker)

info = acao.info
# 2. Pegando o preço atual e setor
nome = info.get("shortName", "N/A")
preco_atual = info.get("currentPrice", "N/A")
pl_ratio = info.get("trailingPE", "N/A")

# 3. Exibindo as informações em um painel
conteudo = f"Nome: {nome}\nPreço Atual: {preco_atual}\nP/L (P/E Ratio): {pl_ratio}"
caixa = Panel(conteudo, title="Informações da Ação")
console.print(caixa)
####