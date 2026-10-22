import logging
import re
import threading
import traceback
from datetime import datetime, time
from time import sleep
from zoneinfo import ZoneInfo

import yfinance as yf
from rich.console import Console, Group
from rich.layout import Layout
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.segment import Segments
from rich.table import Table
from rich.text import Text

# o yfinance escreve avisos no terminal quando um ticker não existe; isso bagunça a tela
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

# sem width: o Rich lê o tamanho da janela a cada desenho
console = Console()


# ---------------------------------------------------------------
# FORMATAÇÃO (padrão brasileiro: 1.234,56)
# ---------------------------------------------------------------

def br(valor, casas=2):
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(variacao):
    sinal = "+" if variacao >= 0 else ""
    return f"{sinal}{br(variacao)}%"


DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def formatar_agora():
    agora = datetime.now()
    return f"{DIAS[agora.weekday()]} {agora.day:02d} {MESES[agora.month - 1]}  {agora:%H:%M:%S}"


# ---------------------------------------------------------------
# COTAÇÕES DO RODAPÉ (buscadas em segundo plano)
# ---------------------------------------------------------------

# nome na tela, símbolo no yfinance
ATIVOS = [
    ("IBOV",   "^BVSP"),
    ("DÓLAR",  "USDBRL=X"),
    ("S&P500", "^GSPC"),
    ("BRENT",  "BZ=F"),
    ("BTC",    "BTC-USD"),
]

cotacoes = {}                       # nome -> (preço, variação em %) ou None
ultima_atualizacao = {"hora": None}


def atualizar_cotacoes():
    for nome, simbolo in ATIVOS:
        try:
            fechamentos = yf.Ticker(simbolo).history(period="5d")["Close"].dropna()
            preco = float(fechamentos.iloc[-1])
            anterior = float(fechamentos.iloc[-2])
            cotacoes[nome] = (preco, (preco / anterior - 1) * 100)
        except Exception:
            cotacoes.setdefault(nome, None)   # falhou: mantém o valor anterior, se existir
    ultima_atualizacao["hora"] = datetime.now()


def loop_cotacoes():
    while True:
        sleep(60)                     # o yfinance tem atraso; 1 minuto é suficiente
        atualizar_cotacoes()


def iniciar_cotacoes():
    atualizar_cotacoes()              # busca a primeira vez antes de abrir a tela
    threading.Thread(target=loop_cotacoes, daemon=True).start()

# Stocks function
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
            precos.append(br(preco))
            variacoes.append(f"[{cor}]{seta} {pct(var)}[/{cor}]")

    tabela.add_row(*nomes)
    tabela.add_row(*precos)
    tabela.add_row(*variacoes)
    return tabela


# ---------------------------------------------------------------
# MERCADOS (horário e status de cada bolsa)
# ---------------------------------------------------------------

# nome, fuso, abertura, fechamento (horário local) e pausa de almoço (ou None) -> está em ordem 
MERCADOS = [
    ("São Paulo", "America/Sao_Paulo", time(10, 0),  time(17, 55), None),
    ("New York",  "America/New_York",  time(9, 30),  time(16, 0),  None),
    ("Toronto",   "America/Toronto",   time(9, 30),  time(16, 0),  None),
    ("Londres",   "Europe/London",     time(8, 0),   time(16, 30), None),
    ("Frankfurt", "Europe/Berlin",     time(9, 0),   time(17, 30), None),
    ("Paris",     "Europe/Paris",      time(9, 0),   time(17, 30), None),
    ("Zurique",   "Europe/Zurich",     time(9, 0),   time(17, 30), None),
    ("Mumbai",    "Asia/Kolkata",      time(9, 15),  time(15, 30), None),
    ("Xangai",    "Asia/Shanghai",     time(9, 30),  time(15, 0),  (time(11, 30), time(13, 0))),
    ("Hong Kong", "Asia/Hong_Kong",    time(9, 30),  time(16, 0),  (time(12, 0),  time(13, 0))),
    ("Tóquio",    "Asia/Tokyo",        time(9, 0),   time(15, 30), (time(11, 30), time(12, 30))),
    ("Seul",      "Asia/Seoul",        time(9, 0),   time(15, 30), None),
    ("Sydney",    "Australia/Sydney",  time(10, 0),  time(16, 0),  None),
]

STATUS_TEXTO = {
    "open":   "[green]● Open[/green]",
    "lunch":  "[yellow]● Lunch[/yellow]",
    "closed": "[red]● Closed[/red]",
}


def status_mercado(agora, abre, fecha, almoco):
    if agora.weekday() >= 5:                       # sábado e domingo
        return "closed"
    hora = agora.time()
    if not (abre <= hora <= fecha):
        return "closed"
    if almoco and almoco[0] <= hora < almoco[1]:
        return "lunch"
    return "open"


def bloco_mercados():
    tabela = Table.grid(padding=(0, 2))
    tabela.add_column()
    tabela.add_column()
    tabela.add_column()

    tabela.add_row("[bold dim]MERCADOS[/bold dim]", "", "")
    for nome, fuso, abre, fecha, almoco in MERCADOS:
        agora = datetime.now(ZoneInfo(fuso))       # hora atual naquela cidade
        status = status_mercado(agora, abre, fecha, almoco)
        tabela.add_row(nome, agora.strftime("%H:%M"), STATUS_TEXTO[status])

    return tabela


# ---------------------------------------------------------------
# TELAS (cada função devolve só o texto que vai no centro do painel)
# ---------------------------------------------------------------

def inicio():
    return (
        "[bold yellow]TERMINAL BLOOMBERG OPENSOURCE[/bold yellow]\n\n"
        "Aperte [bold yellow]/[/bold yellow] para abrir a barra de pesquisa e digite um\n"
        "ticker (ex: [bold cyan]PETR4[/bold cyan]) ou um comando (ex: [bold cyan]MKT[/bold cyan]).\n\n"
        "Digite [bold cyan]AJ[/bold cyan] para ver todos os comandos.\n"
        "Ou use os números do menu à esquerda."
    )

# tela provisória para as opções que ainda não foram feitas
def em_breve(titulo):
    return f"[bold]{titulo}[/bold]\n\n[yellow]Em breve...[/yellow]"


def top_10():
    return em_breve("Top 10 ações")


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


# Help function
def ajuda():
    linhas = ["[bold]Ajuda[/bold]\n"]
    linhas.append("Aperte [bold yellow]/[/bold yellow] e digite um comando, depois Enter:\n")
    for codigo, (descricao, _, _) in COMANDOS.items():
        linhas.append(f"  [bold cyan]{codigo:<8}[/bold cyan]{descricao}")
    linhas.append("\nQualquer outro código é tratado como ticker (ex: PETR4, VALE3, AAPL, ^BVSP).")
    linhas.append("[dim]Backspace com a barra vazia cancela a pesquisa.[/dim]")
    return "\n".join(linhas)


# número no menu -> (nome na tela, função da tela; None = abre a barra de pesquisa)
OPCOES = {
    "1": ("Top 10 ações", top_10),
    "2": ("Consultar ações", None),
    "3": ("Histórico de ações", historico),
    "4": ("Watchlist", watchlist),
    "5": ("Mercados", mercados),
    "6": ("Gráfico de ativo", grafico),
    "7": ("Notícias", noticias),
    "8": ("Alertas de preço", alertas),
    "9": ("Ajuda", ajuda),
}

# comando digitado na barra -> (descrição, opção do menu que fica destacada, função)
COMANDOS = {
    "INICIO": ("Tela inicial", "", inicio),
    "TOP":    ("Top 10 ações", "1", top_10),
    "HIST":   ("Histórico de ações", "3", historico),
    "WL":     ("Watchlist", "4", watchlist),
    "MKT":    ("Mercados", "5", mercados),
    "G":      ("Gráfico de ativo", "6", grafico),
    "N":      ("Notícias", "7", noticias),
    "AL":     ("Alertas de preço", "8", alertas),
    "AJ":     ("Ajuda", "9", ajuda),
    "SAIR":   ("Fechar o programa", "", None),
}


# ---------------------------------------------------------------
# CONSULTA DE AÇÃO
# ---------------------------------------------------------------

def normalizar_ticker(codigo):
    codigo = codigo.upper().strip()
    # ações da B3 (4 letras + 1 ou 2 números, ex: PETR4, BOVA11) precisam do .SA no yfinance
    if re.fullmatch(r"[A-Z]{4}\d{1,2}", codigo):
        codigo += ".SA"
    return codigo


def buscar_acao(codigo):
    codigo = normalizar_ticker(codigo)
    voltar = "[dim]Aperte / para nova pesquisa[/dim]"

    try:
        historico_precos = yf.Ticker(codigo).history(period="5d")
    except Exception:
        return f"[red]Erro ao buscar {escape(codigo)}.[/red]\n\nVerifique a internet e tente de novo.\n\n{voltar}"

    if historico_precos.empty:
        return f"[red]Ticker {escape(codigo)} não encontrado.[/red]\n\n{voltar}"

    fechamentos = historico_precos["Close"].dropna()
    preco = float(fechamentos.iloc[-1])
    anterior = float(fechamentos.iloc[-2]) if len(fechamentos) > 1 else preco
    var = (preco / anterior - 1) * 100
    cor = "green" if var >= 0 else "red"
    seta = "▲" if var >= 0 else "▼"
    moeda = "R$ " if codigo.endswith(".SA") else ""

    # devolve texto, em vez de imprimir: quem desenha é o painel
    return (
        f"[bold]{escape(codigo)}[/bold]\n\n"
        f"Preço:      {moeda}{br(preco)}\n"
        f"Variação:   [{cor}]{seta} {pct(var)}[/{cor}]\n"
        f"Máx 5 dias: {moeda}{br(float(fechamentos.max()))}\n"
        f"Mín 5 dias: {moeda}{br(float(fechamentos.min()))}\n\n"
        f"{voltar}"
    )


def executar_comando(texto):
    """Devolve (conteúdo, opção do menu) ou None se for para sair."""
    codigo = texto.upper().strip()
    if not codigo:
        return inicio(), ""
    if codigo == "SAIR":
        return None
    if codigo in COMANDOS:
        _, opcao, funcao = COMANDOS[codigo]
        return funcao(), opcao
    return buscar_acao(codigo), "2"      # qualquer outra coisa é tratada como ticker


# ---------------------------------------------------------------
# DESENHO DA TELA
# ---------------------------------------------------------------

def barra_topo(buffer, ativa):
    if ativa:
        esquerda = Text.from_markup(
            f"[bold yellow]>[/bold yellow] [bold cyan]{escape(buffer)}[/bold cyan]▌"
        )
    else:
        esquerda = Text.from_markup(
            "[bold yellow]>[/bold yellow] [dim]aperte / para pesquisar (ticker ou comando)[/dim]"
        )

    tabela = Table.grid(expand=True)
    tabela.add_column(ratio=1)
    tabela.add_column(justify="right")
    tabela.add_row(esquerda, Text(formatar_agora(), style="bold"))
    return tabela


def menu_lateral(ativa):
    linhas = [Text("MENU", style="bold dim"), Text("")]
    for numero, (nome, _) in OPCOES.items():
        if numero == ativa:
            linhas.append(Text(f" {numero}  {nome:<20}", style="bold black on yellow"))
        else:
            linhas.append(Text.assemble((f" {numero}", "yellow"), f"  {nome}"))
    linhas.append(Text.assemble((" 0", "yellow"), "  Sair"))
    return Group(*linhas)


def rodape_dicas():
    hora = ultima_atualizacao["hora"]
    cotacao = f"cotações: {hora:%H:%M}" if hora else "cotações: carregando..."

    dicas = Text.assemble(
        ("/", "bold yellow"), (" pesquisar   ", "dim"),
        ("1-9", "bold yellow"), (" telas   ", "dim"),
        ("m", "bold yellow"), (" início   ", "dim"),
        ("0", "bold yellow"), (" sair", "dim"),
    )

    tabela = Table.grid(expand=True)
    tabela.add_column(ratio=1)
    tabela.add_column(justify="right")
    tabela.add_row(dicas, Text(cotacao, style="dim"))
    return tabela


def separador(altura):
    # linha vertical; o Layout corta o excesso até a altura da região
    return Text("\n".join(["│"] * altura), style="red")


def tela(estado):
    largura = console.size.width
    altura = console.size.height

    regioes = [
        Layout(Padding(menu_lateral(estado["opcao"]), (0, 1)), name="menu", size=26),
        Layout(separador(altura), name="sep1", size=1),
        Layout(Padding(Text.from_markup(estado["view"]), (0, 2)), name="centro", ratio=1),
    ]
    if largura >= 100:                  # em janelas estreitas a coluna dos mercados some
        regioes += [
            Layout(separador(altura), name="sep2", size=1),
            Layout(Padding(bloco_mercados(), (0, 1)), name="mercados", size=34),
        ]

    meio = Layout(name="meio", ratio=1)
    meio.split_row(*regioes)

    raiz = Layout()
    raiz.split_column(
        Layout(Group(barra_topo(estado["buffer"], estado["digitando"]), Rule(style="red")),
               name="barra", size=2),
        meio,
        Layout(Group(Rule(style="red"), faixa_ativos(), Rule(style="red")),
               name="ativos", size=5),
        Layout(rodape_dicas(), name="dicas", size=1),
    )

    return Panel(
        raiz,
        title="[bold yellow]TERMINAL BLOOMBERG OPENSOURCE[/bold yellow]",
        subtitle="[dim]v1.0.0[/dim]",
        border_style="red",
        padding=(0, 1),
        width=largura,
        height=altura,
    )


def renderizar(estado):
    # O Live chama esta função 4 vezes por segundo, em outra thread.
    # Se o desenho der erro, mostramos o erro na tela em vez de congelar tudo.
    try:
        painel = tela(estado)
        # list(console.render(...)) desenha aqui dentro, para o erro cair no except
        return Segments(list(console.render(painel)))
    except Exception:
        erro = traceback.format_exc()
        with open("erro.log", "a") as arquivo:
            arquivo.write(erro + "\n")
        return Panel(
            f"[red]Erro ao desenhar a tela[/red]\n\n{escape(erro[-800:])}\n\n"
            "[dim]Aperte m para voltar ao início. O erro também foi salvo em erro.log[/dim]",
            border_style="red",
        )