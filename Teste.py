import readchar
from datetime import datetime, time
from time import sleep
from zoneinfo import ZoneInfo

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import track
from rich.rule import Rule
from rich.table import Table

console = Console(width=100)


# ---------------------------------------------------------------
# CONTEÚDOS: cada função devolve só o texto (ou tabela) que vai
# dentro do painel. Quem desenha a borda é a função tela().
# ---------------------------------------------------------------

def menu():
    return (
        "[1]-Top 10 ações\n"
        "[2]-Consultar ações\n"
        "[3]-Histórico de ações\n"
        "[4]-Watchlist\n"
        "[5]-Mercados\n"
        "[6]-Gráfico de ativo\n"
        "[7]-Notícias\n"
        "[8]-Alertas de preço\n"
        "[9]-Ajuda\n"
        "[0]-Sair"
    )

4


# tecla apertada -> função que devolve o conteúdo daquela tela
# (as funções ficam SEM parênteses: guardamos a função, rodamos depois)
TELAS = {
    "1": top_10,
    "2": consultar_acao,
    "3": historico,
    "4": watchlist,
    "5": mercados,
    "6": grafico,
    "7": noticias,
    "8": alertas,
    "9": ajuda,
}


# ---------------------------------------------------------------
# MERCADOS: bloco fixo da direita, com horário e status de cada bolsa
# ---------------------------------------------------------------

# nome, fuso horário, abertura, fechamento (no horário local de cada bolsa)
MERCADOS = [
    ("São Paulo (B3)", "America/Sao_Paulo", time(10, 0), time(17, 55)),
    ("New York",       "America/New_York",  time(9, 30), time(16, 0)),
    ("Londres",        "Europe/London",     time(8, 0),  time(16, 30)),
    ("Tóquio",         "Asia/Tokyo",        time(9, 0),  time(15, 30)),
]


def bloco_mercados():
    tabela = Table.grid(padding=(0, 2))   # tabela sem borda, só para alinhar
    tabela.add_column()
    tabela.add_column()
    tabela.add_column()

    tabela.add_row("[bold]MERCADOS[/bold]", "", "")
    for nome, fuso, abre, fecha in MERCADOS:
        agora = datetime.now(ZoneInfo(fuso))          # hora atual naquela cidade
        dia_util = agora.weekday() < 5                # 0-4 = segunda a sexta
        aberto = dia_util and abre <= agora.time() <= fecha
        status = "[green]● Open/green]" if aberto else "[red]● Closed[/red]"
        tabela.add_row(nome, agora.strftime("%H:%M"), status)

    return tabela


# ---------------------------------------------------------------
# MOLDURA: o painel único que envolve qualquer conteúdo
# ---------------------------------------------------------------

def tela(conteudo):
    colunas = Table.grid(expand=True)
    colunas.add_column(ratio=1)   # esquerda: o que muda (menu, telas)
    colunas.add_column(ratio=1)   # direita: mercados
    colunas.add_row(conteudo, bloco_mercados())

    return Panel(
        Group(
            colunas,
            Rule(style="red"),
            "[dim]\\[m] Menu   \\[0] Sair[/dim]",
        ),
        title="[bold yellow]TERMINAL BLOOMBERG OPENSOURCE[/bold yellow]",
        subtitle="[dim]v1.0.0[/dim]",
        border_style="red",
        padding=(1, 2),
    )


def process_data():
    sleep(0.05)


def main():
    for _ in track(range(100), description="[white]Loading terminal", console=console):
        process_data()

    conteudo_atual = menu()   # o que está aparecendo agora no painel

    with Live(console=console, screen=True, auto_refresh=False) as live:
        while True:
            live.update(tela(conteudo_atual), refresh=True)   # redesenha o painel

            tecla = readchar.readkey()                        # espera uma tecla
            if tecla == "0":
                break
            elif tecla == "m":
                conteudo_atual = menu()
            elif tecla in TELAS:
                conteudo_atual = TELAS[tecla]()               # aqui sim, com parênteses


main()