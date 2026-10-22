import readchar
from time import sleep

from rich.live import Live
from rich.progress import track

# Functions file import
from Terminal_BloombergOpenSource_Functions import (
    console, renderizar, inicio, executar_comando, iniciar_cotacoes, OPCOES,
)

ENTER = ("\r", "\n")
BACKSPACE = ("\x7f", "\x08")

# tudo o que muda na tela fica aqui; o Live lê este dicionário a cada desenho
estado = {
    "view": "",          # texto (com formatação do Rich) que aparece no centro
    "opcao": "",         # número da opção do menu que fica destacada
    "digitando": False,  # True = a barra de pesquisa está ativa
    "buffer": "",        # o que foi digitado na barra
}


def processar_tecla(estado, tecla):
    """Atualiza o estado conforme a tecla apertada. Devolve False quando for para sair."""

    # MODO DIGITAÇÃO: as teclas viram texto da barra de pesquisa
    if estado["digitando"]:
        if tecla in ENTER:
            texto = estado["buffer"]
            estado["digitando"] = False
            estado["buffer"] = ""
            estado["view"] = "[yellow]Buscando...[/yellow]"
            resultado = executar_comando(texto)
            if resultado is None:                    # comando SAIR
                return False
            estado["view"], estado["opcao"] = resultado
        elif tecla in BACKSPACE:
            if estado["buffer"]:
                estado["buffer"] = estado["buffer"][:-1]
            else:                                    # barra vazia: Backspace cancela
                estado["digitando"] = False
        elif len(tecla) == 1 and (tecla.isalnum() or tecla in ".-^=") and len(estado["buffer"]) < 12:
            estado["buffer"] += tecla.upper()
        return True

    # MODO NORMAL: as teclas são atalhos
    if tecla == "0":
        return False
    elif tecla in ("/", "2"):                        # "/" e "2" abrem a barra de pesquisa
        estado["digitando"] = True
        estado["buffer"] = ""
    elif tecla == "m":
        estado["view"] = inicio()
        estado["opcao"] = ""
    elif tecla in OPCOES and OPCOES[tecla][1] is not None:
        estado["view"] = OPCOES[tecla][1]()          # aqui sim, com parênteses
        estado["opcao"] = tecla
    return True


# Progress bar time function  
def process_data():
    sleep(0.02)


def main():
    for _ in track(range(100), description="[white]Loading terminal", console=console): # Progress bar logic
        process_data()

    with console.status("Carregando cotações..."):
        iniciar_cotacoes()

    estado["view"] = inicio()

    try:
        with Live(
            get_renderable=lambda: renderizar(estado),   # o Live chama isso a cada desenho
            console=console,
            screen=True,
            refresh_per_second=4,
        ):
            while processar_tecla(estado, readchar.readkey()):
                pass
    except KeyboardInterrupt:
        pass    # Ctrl+C sai sem despejar erro no Terminal


if __name__ == "__main__":
    main()