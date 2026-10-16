import yfinance as yf
from datetime import datetime, time
from zoneinfo import ZoneInfo

from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

import threading
from time import sleep

# criado uma vez só aqui; o main importa este mesmo objeto
console = Console(width=100)

# nome, fuso horário, abertura, fechamento (no horário local de cada bolsa)
# nome, fuso horário, abertura, fechamento (no horário local de cada bolsa)
MERCADOS = [
    ("São Paulo",   "America/Sao_Paulo",  time(10, 0),  time(17, 55)),
    ("New York",    "America/New_York",   time(9, 30),  time(16, 0)),
    ("Toronto",     "America/Toronto",    time(9, 30),  time(16, 0)),
    ("Londres",     "Europe/London",      time(8, 0),   time(16, 30)),
    ("Frankfurt",   "Europe/Berlin",      time(9, 0),   time(17, 30)),
    ("Paris",       "Europe/Paris",       time(9, 0),   time(17, 30)),
    ("Zurique",     "Europe/Zurich",      time(9, 0),   time(17, 30)),
    ("Mumbai",      "Asia/Kolkata",       time(9, 15),  time(15, 30)),
    ("Xangai",      "Asia/Shanghai",      time(9, 30),  time(15, 0)),
    ("Hong Kong",   "Asia/Hong_Kong",     time(9, 30),  time(16, 0)),
    ("Tóquio",      "Asia/Tokyo",         time(9, 0),   time(15, 30)),
    ("Seul",        "Asia/Seoul",         time(9, 0),   time(15, 30)),
    ("Sydney",      "Australia/Sydney",   time(10, 0),  time(16, 0)),
]


def get_papers():
    # ainda NÃO está ligada ao menu: usa input/print, que não funcionam dentro do Live
    codigo = input("Ticker da ação (ex: PETR4): ").upper().strip()

    # ações da B3 precisam do sufixo .SA no yfinance
    if not codigo.endswith(".SA"):
        codigo += ".SA"

    ticker = yf.Ticker(codigo)
    historico_precos = ticker.history(period="5d")

    if historico_precos.empty:
        console.print(f"[red]Ticker {codigo} não encontrado.[/red]")
        return

    preco = historico_precos["Close"].iloc[-1]
    console.print(f"[bold]{codigo}[/bold]: R$ {preco:.2f}")


def em_breve(titulo):
    # tela provisória para as opções que ainda não foram feitas
    return (
        f"[bold]{titulo}[/bold]\n\n"
        "[yellow]Em breve...[/yellow]\n\n"
        "\\[m]-Voltar ao menu"   # \\[ evita que o Rich leia [m] como formatação
    )


def top_10():
    return em_breve("Top 10 ações")


def consultar_acao():
    return em_breve("Consultar ações")


def historico():
    return em_breve("Histórico de ações")


def watchlist():
    return em_breve("Watchlist")


def mercados():
    return em_breve("Mercados")


def grafico():
    return em_breve("Gráfico de ativo")


def noticias():
    return em_breve("Notícias")


def alertas():
    return em_breve("Alertas de preço")


def ajuda():
    return em_breve("Ajuda")


def bloco_mercados():
    tabela = Table.grid(padding=(0, 2))
    tabela.add_column()
    tabela.add_column()
    tabela.add_column()

    tabela.add_row("[bold]MERCADOS[/bold]", "", "")
    for nome, fuso, abre, fecha in MERCADOS:
        agora = datetime.now(ZoneInfo(fuso))          # hora atual naquela cidade
        dia_util = agora.weekday() < 5                # 0-4 = segunda a sexta
        aberto = dia_util and abre <= agora.time() <= fecha
        status = "[green]● Open[/green]" if aberto else "[red]● Closed[/red]"
        tabela.add_row(nome, agora.strftime("%H:%M"), status)

    return tabela    # alinhado com o "for": só devolve depois de passar por todos


def tela(conteudo):
    colunas = Table.grid(expand=True)
    colunas.add_column(ratio=1)   # esquerda: o que muda (menu, telas)
    colunas.add_column(ratio=1)   # direita: mercados
    colunas.add_row(conteudo, bloco_mercados())

    return Panel(
        Group(
            colunas,
            Rule(style="red"),
            faixa_ativos(),
        ),
        title="[bold yellow]TERMINAL BLOOMBERG OPENSOURCE[/bold yellow]",
        subtitle="[dim]v1.0.0[/dim]",
        border_style="red",
        padding=(1, 2),
    )




# nome na tela, símbolo no yfinance
ATIVOS = [
    ("IBOV",   "^BVSP"),
    ("DÓLAR",  "USDBRL=X"),
    ("S&P500", "^GSPC"),
    ("BRENT",  "BZ=F"),
    ("BTC",    "BTC-USD"),
]

cotacoes = {}   # nome -> (preço, variação em %)


def atualizar_cotacoes():
    for nome, simbolo in ATIVOS:
        try:
            fechamentos = yf.Ticker(simbolo).history(period="5d")["Close"]
            preco = fechamentos.iloc[-1]
            anterior = fechamentos.iloc[-2]
            cotacoes[nome] = (preco, (preco / anterior - 1) * 100)
        except Exception:
            cotacoes[nome] = None     # falhou: a tela mostra "..." em vez de quebrar


def loop_cotacoes():
    while True:
        sleep(60)                     # yfinance tem atraso; 1 minuto é suficiente
        atualizar_cotacoes()


def iniciar_cotacoes():
    atualizar_cotacoes()              # busca a primeira vez antes de abrir a tela
    threading.Thread(target=loop_cotacoes, daemon=True).start()


def faixa_ativos():
    tabela = Table.grid(expand=True)
    for _ in ATIVOS:
        tabela.add_column(justify="center", ratio=1)

    nomes, precos, variacoes = [], [], []
    for nome, _ in ATIVOS:
        nomes.append(f"[bold]{nome}[/bold]")
        dado = cotacoes.get(nome)
        if dado is None:
            precos.append("[dim]...[/dim]")
            variacoes.append("")
        else:
            preco, var = dado
            cor = "green" if var >= 0 else "red"
            seta = "▲" if var >= 0 else "▼"
            precos.append(f"{preco:,.2f}")
            variacoes.append(f"[{cor}]{seta} {var:+.2f}%[/{cor}]")

    tabela.add_row(*nomes)
    tabela.add_row(*precos)
    tabela.add_row(*variacoes)
    return tabela