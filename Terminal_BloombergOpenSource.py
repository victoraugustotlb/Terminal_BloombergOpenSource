import readchar
from time import sleep

from rich.live import Live
from rich.progress import track

from Terminal_BloombergOpenSource_Functions import (
    console, tela,
    top_10, consultar_acao, historico, watchlist,
    mercados, grafico, noticias, alertas, ajuda, iniciar_cotacoes,
)


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
    )   # o menu precisa devolver o texto: sem o return, vira None e o painel fica vazio


# tecla apertada -> função que devolve o conteúdo daquela tela
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


def process_data():
    sleep(0.05)


def main():
    for _ in track(range(100), description="[white]Loading terminal", console=console):
        process_data()

    iniciar_cotacoes()
    current_view = menu()
    estado = {"view": menu()}   # dicionário, para o Live enxergar o valor atual

    with Live(
        get_renderable=lambda: tela(estado["view"]),   # o Live chama isso a cada redesenho
        console=console,
        screen=True,
        refresh_per_second=4,                          # 4 vezes por segundo
        ) as live:
        while True:
            tecla = readchar.readkey()
            if tecla == "0":
                break
            elif tecla == "m":
                estado["view"] = menu()
            elif tecla in TELAS:
                estado["view"] = TELAS[tecla]()


if __name__ == "__main__":
    main()