
from pygame import *
import pygame
import sys
import os
import json

from poderes import carregar_bola, BolaColecionavel, ProjetilBola

init()

LARGURA = 900
ALTURA = 600
TILE_SIZE = 64
FPS = 60

screen = display.set_mode((LARGURA, ALTURA))
display.set_caption("SMB - Futebol Brasileiro")
clock = time.Clock()

pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, "PixelPlatformerTileset")

#####################################################################
# TILESET
#####################################################################

tileset = image.load(
    os.path.join(pasta_assets, "tileset_16x16.png")
).convert_alpha()

props = image.load(
    os.path.join(pasta_assets, "props_sheet.png")
).convert_alpha()

with open(
    os.path.join(pasta_assets, "sprite_index.json"),
    "r", encoding="utf-8"
) as arquivo:
    indice = json.load(arquivo)

sprites = {}

for nome, dados in indice.items():

    origem = props if dados.get("sheet") == "props_sheet.png" else tileset

    area = Rect(dados["x"], dados["y"], dados["w"], dados["h"])
    imagem = Surface((dados["w"], dados["h"]), SRCALPHA)
    imagem.blit(origem, (0, 0), area)

    sprites[nome] = transform.scale(
        imagem,
        (dados["w"] * 4, dados["h"] * 4)
    )

#####################################################################
# MAPA
#####################################################################

with open(
    os.path.join(pasta, "levels", "level_1.txt"),
    "r", encoding="utf-8"
) as arquivo:
    mapa_original = [
        linha.rstrip("\n")
        for linha in arquivo
        if linha.strip()
    ]

mapa = [list(linha) for linha in mapa_original]

tiles = {
    "G": "grass_t",
    "T": "grass_m",
    "B": "bricks",
    "Q": "question_block",
    "U": "question_block_used",
    "S": "stone_bricks",
    "W": "wood_planks",
    "F": "flowers_red",
    "R": "rock",
    "H": "grass_tuft",
    "P": "spikes",
    "A": "tree",
    "N": "pine_tree",
    "V": "bush",
    "O": "cloud",
    "M": "mushroom",
    "E": "star"
}

blocos_solidos = ["G", "T", "B", "Q", "U", "S", "W"]

colisores = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] in blocos_solidos:
            colisores.append(
                Rect(
                    j * TILE_SIZE,
                    i * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE
                )
            )

largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE

moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == "C":
            moedas.append(
                (j * TILE_SIZE + 16, i * TILE_SIZE + 16)
            )

moedas_depart = moedas[:]
camera_x = 0

#####################################################################
# PERSONAGEM NORMAL
#####################################################################

CASE = 32
ECHELLE = 2

DEBUT = 8
REPOS = DEBUT
COURSE = [DEBUT + 1, DEBUT + 2, DEBUT + 3, DEBUT + 2]
SAUT = DEBUT + 4
CHUTE = DEBUT + 5


def charger_planche(nom):
    caminho = os.path.join(pasta, nom)
    planche = image.load(caminho).convert_alpha()

    imagens = []

    for i in range(planche.get_width() // CASE):
        area = Rect(i * CASE, 0, CASE, CASE)
        recorte = planche.subsurface(area)

        imagens.append(
            transform.scale(
                recorte,
                (CASE * ECHELLE, CASE * ECHELLE)
            )
        )

    return imagens


images = charger_planche("Perso.png")

#####################################################################
# PERSONAGEM BRASILEIRO
#####################################################################

def carregar_futebol(nom):
    # Carrega a imagem com os personagens brasileiros
    caminho = os.path.join(pasta, nom)
    planche = image.load(caminho).convert_alpha()

    largura, altura = planche.get_size()

    # Remove o fundo preto
    # Considera transparente o preto quase puro
    for x in range(largura):
        for y in range(altura):
            cor = planche.get_at((x, y))

            if max(cor.r, cor.g, cor.b) <= 25:
                planche.set_at((x, y), (0, 0, 0, 0))

    # Procura colunas que contem partes dos personagens
    colunas = []

    for x in range(largura):
        ocupado = False

        for y in range(altura):
            cor = planche.get_at((x, y))

            if cor.a > 30 and max(cor.r, cor.g, cor.b) > 45:
                ocupado = True
                break

        colunas.append(ocupado)

    # Encontra os limites horizontais de cada personagem
    grupos = []
    inicio = None

    for x, ocupado in enumerate(colunas):
        if ocupado and inicio is None:
            inicio = x

        if not ocupado and inicio is not None:
            grupos.append([inicio, x])
            inicio = None

    if inicio is not None:
        grupos.append([inicio, largura])

    # Une partes separadas por espacos pequenos
    grupos_unidos = []

    for grupo in grupos:
        if grupos_unidos and grupo[0] - grupos_unidos[-1][1] <= 8:
            grupos_unidos[-1][1] = grupo[1]
        else:
            grupos_unidos.append(grupo[:])

    frames = []

    for x1, x2 in grupos_unidos:
        y1 = altura
        y2 = 0

        for x in range(x1, x2):
            for y in range(altura):
                cor = planche.get_at((x, y))

                if cor.a > 30 and max(cor.r, cor.g, cor.b) > 45:
                    y1 = min(y1, y)
                    y2 = max(y2, y + 1)

        if y2 <= y1:
            continue

        recorte = planche.subsurface(
            Rect(x1, y1, x2 - x1, y2 - y1)
        ).copy()

        # Mantem a proporcao dentro de uma imagem 64x64
        escala = min(
            60 / recorte.get_width(),
            60 / recorte.get_height()
        )

        novo_w = max(1, int(recorte.get_width() * escala))
        novo_h = max(1, int(recorte.get_height() * escala))

        recorte = transform.scale(
            recorte, (novo_w, novo_h)
        )

        frame = Surface((64, 64), SRCALPHA)

        # Centraliza horizontalmente e alinha os pes
        frame.blit(
            recorte,
            ((64 - novo_w) // 2, 64 - novo_h)
        )

        frames.append(frame)

    print("Frames brasileiros encontrados:", len(frames))

    return frames


nome_sprite_futebol = "Sprite de Fútbol Brasileño en Pixel Art.png"
caminho_futebol = os.path.join(pasta, nome_sprite_futebol)

images_futebol = []

if os.path.exists(caminho_futebol):
    images_futebol = carregar_futebol(nome_sprite_futebol)
else:
    print("Sprite brasileiro nao encontrado:", caminho_futebol)


def criar_mario_futebol(sprite_original):
    # Aparencia provisoria caso o spritesheet nao funcione
    sprite_novo = sprite_original.copy()

    sprite_novo.fill(
        (255, 235, 80),
        special_flags=BLEND_RGB_MULT
    )

    return sprite_novo


#####################################################################
# CONFIGURACOES DE MARIO
#####################################################################

DEPART = (100, 8 * TILE_SIZE)

mario = images[REPOS].get_rect(midbottom=DEPART)

vitesse_y = 0
au_sol = False
regarde_a_gauche = False
compteur = 0

pieces = 0
compteur_mort = 3

police = font.Font(None, 48)
police_poder = font.Font(None, 32)

#####################################################################
# FLAVIO
#####################################################################

def charger_monstre(nom):
    caminho = os.path.join(pasta, nom)
    planche = image.load(caminho).convert_alpha()

    imagens = []

    for i in range(planche.get_width() // CASE):
        area = Rect(i * CASE, 0, CASE, CASE)
        recorte = planche.subsurface(area)

        imagens.append(
            transform.scale(
                recorte,
                (CASE * ECHELLE, CASE * ECHELLE)
            )
        )

    return imagens


images_flavio = charger_monstre(
    os.path.join("Monstres", "flavio.png")
)

MARCHE_FLAVIO = [0, 1, 2, 3]

FLAVIO_MIN_X = 26 * TILE_SIZE
FLAVIO_MAX_X = 36 * TILE_SIZE
FLAVIO_SOL = 8 * TILE_SIZE

flavio = images_flavio[0].get_rect(
    midbottom=(FLAVIO_MIN_X, FLAVIO_SOL)
)

vitesse_flavio = 2
compteur_flavio = 0
touche_flavio = False
flavio_vivo = True


def reiniciar_flavio():
    global vitesse_flavio
    global compteur_flavio
    global touche_flavio
    global flavio_vivo

    flavio_vivo = True
    flavio.midbottom = (FLAVIO_MIN_X, FLAVIO_SOL)

    vitesse_flavio = 2
    compteur_flavio = 0
    touche_flavio = False


#####################################################################
# CHECKPOINTS
#####################################################################

planche_cristo = image.load(
    os.path.join(pasta, "Checkpoints", "cristo.png")
).convert_alpha()

LARG_CRISTO = planche_cristo.get_width() // 2
HAUT_CRISTO = planche_cristo.get_height()

images_cristo = []

for i in range(2):
    recorte = planche_cristo.subsurface(
        Rect(i * LARG_CRISTO, 0, LARG_CRISTO, HAUT_CRISTO)
    )

    images_cristo.append(
        transform.scale(
            recorte,
            (LARG_CRISTO * 4, HAUT_CRISTO * 4)
        )
    )

checkpoints = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == "X":
            checkpoints.append(
                images_cristo[0].get_rect(
                    midbottom=(
                        j * TILE_SIZE + TILE_SIZE // 2,
                        (i + 1) * TILE_SIZE
                    )
                )
            )

checkpoints_actives = []
point_reapparition = DEPART

#####################################################################
# PODER DA BOLA
#####################################################################

frames_bola = carregar_bola()

bolas_colecionaveis = []
blocos_usados = set()

tem_poder_bola = False
projeteis = []

ultimo_disparo = -1000
TEMPO_ENTRE_DISPAROS = 350

#####################################################################
# LOOP PRINCIPAL
#####################################################################

while True:

    dt = min(clock.tick(FPS), 40)

    for ev in event.get():
        if ev.type == QUIT:
            quit()
            sys.exit()

    touches = key.get_pressed()

    #################################################################
    # MOVIMENTO HORIZONTAL
    #################################################################

    en_mouvement = False

    if touches[K_LEFT]:
        mario.x -= 7
        regarde_a_gauche = True
        en_mouvement = True

    if touches[K_RIGHT]:
        mario.x += 7
        regarde_a_gauche = False
        en_mouvement = True

    for bloc in colisores:
        if mario.colliderect(bloc):
            if regarde_a_gauche:
                mario.left = bloc.right
            else:
                mario.right = bloc.left

    mario.left = max(
        0, min(mario.left, largura_mapa - mario.width)
    )

    #################################################################
    # SALTO E GRAVIDADE
    #################################################################

    if touches[K_UP] and au_sol:
        vitesse_y = -22

    vitesse_y += 1
    topo_anterior = mario.top

    mario.y += vitesse_y
    au_sol = False

    for bloc in colisores:
        if mario.colliderect(bloc):

            if vitesse_y > 0:
                mario.bottom = bloc.top
                au_sol = True

            elif vitesse_y < 0:
                mario.top = bloc.bottom

                # Mario bateu na parte inferior de um bloco
                if topo_anterior >= bloc.bottom:
                    coluna = bloc.x // TILE_SIZE
                    linha = bloc.y // TILE_SIZE

                    if mapa[linha][coluna] == "Q":
                        posicao_bloco = (linha, coluna)

                        if posicao_bloco not in blocos_usados:
                            blocos_usados.add(posicao_bloco)
                            mapa[linha][coluna] = "U"

                            nova_bola = BolaColecionavel(
                                bloc.x, bloc.y, frames_bola
                            )

                            bolas_colecionaveis.append(nova_bola)

                            print("Bola criada no bloco:", linha, coluna)

            vitesse_y = 0

    #################################################################
    # COLETA DO PODER
    #################################################################

    for bola in bolas_colecionaveis:
        if bola.atualizar(mario):
            tem_poder_bola = True
            print("Mario ganhou o poder da bola!")

    #################################################################
    # DISPARO
    #################################################################

    agora = time.get_ticks()

    if touches[K_f] and tem_poder_bola:
        if agora - ultimo_disparo >= TEMPO_ENTRE_DISPAROS:

            direcao = -1 if regarde_a_gauche else 1

            if direcao == 1:
                x_bola = mario.right
            else:
                x_bola = mario.left - 32

            y_bola = mario.centery - 16

            projeteis.append(
                ProjetilBola(
                    x_bola, y_bola, direcao, frames_bola
                )
            )

            ultimo_disparo = agora

    #################################################################
    # QUEDA E MOEDAS
    #################################################################

    mort = False

    if mario.top > ALTURA:
        mort = True

    for moeda in moedas[:]:
        x, y = moeda

        if mario.colliderect(
            Rect(x + 16, y + 16, 32, 32)
        ):
            moedas.remove(moeda)
            pieces += 1

    #################################################################
    # MOVIMENTO DE FLAVIO
    #################################################################

    if flavio_vivo:
        flavio.x += vitesse_flavio

        if flavio.right >= FLAVIO_MAX_X:
            flavio.right = FLAVIO_MAX_X
            vitesse_flavio = -2

        elif flavio.left <= FLAVIO_MIN_X:
            flavio.left = FLAVIO_MIN_X
            vitesse_flavio = 2

        compteur_flavio += 1

    #################################################################
    # PROJETEIS
    #################################################################

    for projetil in projeteis[:]:
        projetil.atualizar(colisores, largura_mapa)

        if flavio_vivo and projetil.ativo:
            if projetil.rect.colliderect(flavio):
                flavio_vivo = False
                projetil.ativo = False
                print("Flavio foi eliminado!")

        if not projetil.ativo:
            projeteis.remove(projetil)

    #################################################################
    # MARIO E FLAVIO
    #################################################################

    if flavio_vivo and mario.colliderect(flavio):
        if not touche_flavio:
            mort = True
        touche_flavio = True
    else:
        touche_flavio = False

    #################################################################
    # CHECKPOINTS
    #################################################################

    for cp in checkpoints:
        if mario.colliderect(cp) and cp not in checkpoints_actives:
            checkpoints_actives.append(cp)
            point_reapparition = (cp.centerx, cp.bottom)

    #################################################################
    # MORTE DE MARIO
    #################################################################

    if mort:
        compteur_mort -= 1
        vitesse_y = 0
        au_sol = False
        pieces = 0

        # Mario perde o poder
        tem_poder_bola = False
        projeteis.clear()

        # Flavio volta quando Mario perde uma vida
        reiniciar_flavio()

        if compteur_mort > 0:
            mario.midbottom = point_reapparition

        else:
            mario.midbottom = DEPART
            compteur_mort = 3

            point_reapparition = DEPART
            checkpoints_actives = []
            moedas = moedas_depart[:]

            mapa = [list(linha) for linha in mapa_original]

            blocos_usados.clear()
            bolas_colecionaveis.clear()

            reiniciar_flavio()

    #################################################################
    # CAMERA
    #################################################################

    camera_x = mario.centerx - LARGURA // 2

    camera_x = max(
        0,
        min(camera_x, max(0, largura_mapa - LARGURA))
    )

    #################################################################
    # DESENHO DO MAPA
    #################################################################

    screen.fill((120, 180, 220))

    for i in range(len(mapa)):
        for j in range(len(mapa[i])):

            letra = mapa[i][j]

            if letra in tiles:
                imagem = sprites[tiles[letra]]

                x_tela = int(j * TILE_SIZE - camera_x)
                y_tela = (
                    (i + 1) * TILE_SIZE - imagem.get_height()
                )

                if letra == "V":
                    y_tela += 8

                if -imagem.get_width() < x_tela < LARGURA:
                    screen.blit(imagem, (x_tela, y_tela))

    #################################################################
    # MOEDAS
    #################################################################

    frame_moeda = (time.get_ticks() // 150) % 4
    nome_moeda = "coin_" + str(frame_moeda)

    if nome_moeda in sprites:
        for x, y in moedas:
            x_tela = int(x - camera_x)

            if -TILE_SIZE < x_tela < LARGURA:
                screen.blit(
                    sprites[nome_moeda],
                    (x_tela, y)
                )

    #################################################################
    # CHECKPOINTS
    #################################################################

    for cp in checkpoints:
        x_tela_cp = int(cp.x - camera_x)

        if -cp.width < x_tela_cp < LARGURA:
            imagem_cp = (
                images_cristo[1]
                if cp in checkpoints_actives
                else images_cristo[0]
            )

            screen.blit(
                imagem_cp,
                (x_tela_cp, cp.y)
            )

    #################################################################
    # BOLAS COLECIONAVEIS E PROJETEIS
    #################################################################

    for bola in bolas_colecionaveis:
        bola.desenhar(screen, camera_x)

    for projetil in projeteis:
        projetil.desenhar(screen, camera_x)

    #################################################################
    # FLAVIO
    #################################################################

    if flavio_vivo:
        indice_flavio = (
            compteur_flavio // 8
        ) % len(MARCHE_FLAVIO)

        imagem_flavio = images_flavio[
            MARCHE_FLAVIO[indice_flavio]
        ]

        x_tela_flavio = int(flavio.x - camera_x)

        if -flavio.width < x_tela_flavio < LARGURA:
            screen.blit(
                transform.flip(
                    imagem_flavio,
                    vitesse_flavio < 0,
                    False
                ),
                (x_tela_flavio, flavio.y)
            )

    #################################################################
    # ANIMACAO DE MARIO
    #################################################################

    # Quando Mario tem o poder, usa o jogador brasileiro
    usando_futebol = (
        tem_poder_bola and len(images_futebol) > 0
    )

    if usando_futebol:
        imagens_ativas = images_futebol

        # A nova planilha tem sua propria sequencia
        repos_atual = 0
        corrida_atual = [
            i for i in (1, 2, 3)
            if i < len(imagens_ativas)
        ]

        if not corrida_atual:
            corrida_atual = [0]

        salto_atual = min(4, len(imagens_ativas) - 1)
        chute_atual = min(5, len(imagens_ativas) - 1)

    else:
        imagens_ativas = images
        repos_atual = REPOS
        corrida_atual = COURSE
        salto_atual = SAUT
        chute_atual = CHUTE

    if not au_sol:
        if vitesse_y < 0:
            sprite = imagens_ativas[salto_atual]
        else:
            sprite = imagens_ativas[chute_atual]

    elif en_mouvement:
        compteur += 1

        indice_corrida = (
            contador_corrida
            if False
            else contador_corrida
        ) if False else contador_corrida if False else (
            compteur // 6
        ) % len(corrida_atual)

        sprite = imagens_ativas[
            corrida_atual[indice_corrida]
        ]

    else:
        compteur = 0
        sprite = imagens_ativas[repos_atual]

    # Cor alternativa se o PNG brasileiro nao foi carregado
    if tem_poder_bola and not usando_futebol:
        sprite = criar_mario_futebol(sprite)

    screen.blit(
        transform.flip(
            sprite,
            regarde_a_gauche,
            False
        ),
        (int(mario.x - camera_x), mario.y)
    )

    #################################################################
    # INTERFACE
    #################################################################

    texto_moedas = police.render(
        "Moedas : " + str(pieces),
        True,
        (255, 255, 255)
    )

    if compteur_mort == 2:
        cor_vidas = "orange"
    elif compteur_mort == 1:
        cor_vidas = "red"
    else:
        cor_vidas = (255, 255, 255)

    texto_vidas = police.render(
        "Vidas : " + str(compteur_mort),
        True,
        cor_vidas
    )

    screen.blit(texto_moedas, (15, 15))
    screen.blit(texto_vidas, (750, 15))

    if tem_poder_bola:
        texto_poder = police_poder.render(
            "PODER BOLA - F PARA DISPARAR",
            True,
            (255, 255, 0)
        )

        screen.blit(texto_poder, (15, 65))

    display.update()
