
from pygame import *
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

pasta = os.path.dirname(os.path.abspath(__file__))
pasta_assets = os.path.join(pasta, "PixelPlatformerTileset")

#####################################################################
# TILESET E SPRITES
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

# Lista de listas para trocar Q por U
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

largura_mapa = max(
    len(linha) for linha in mapa
) * TILE_SIZE

camera_x = 0

#####################################################################
# MOEDAS
#####################################################################

moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        if mapa[i][j] == "C":
            moedas.append(
                (j * TILE_SIZE + 16, i * TILE_SIZE + 16)
            )

moedas_depart = moedas[:]

#####################################################################
# PERSONAGEM NORMAL E FUTEBOLISTA
#####################################################################

CASE = 32
ECHELLE = 2

DEBUT = 8
REPOS = DEBUT
COURSE = [DEBUT + 1, DEBUT + 2, DEBUT + 3, DEBUT + 2]
SAUT = DEBUT + 4
CHUTE = DEBUT + 5


def charger_planche(nom):
    # Recorta sprites de 32x32 e amplia para 64x64
    caminho = os.path.join(pasta, nom)
    planche = image.load(caminho).convert_alpha()

    imagens = []

    if planche.get_width() % CASE != 0:
        raise ValueError("Largura incorreta do spritesheet: " + nom)

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


# Sprites do personagem
images = charger_planche("Perso.png")
images_futebol = charger_planche("Perso_futebol.png")

if len(images) <= CHUTE or len(images_futebol) <= CHUTE:
    raise ValueError("Spritesheet sem frames suficientes")

print("Frames normais:", len(images))
print("Frames brasileiros:", len(images_futebol))

#####################################################################
# MARIO
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

images_flavio = charger_planche(
    os.path.join("Monstres", "flavio.png")
)

MARCHE_FLAVIO = [0, 1, 2, 3]

# Flavio fica perto do inicio do mapa
FLAVIO_MIN_X = 500
FLAVIO_MAX_X = 1100
FLAVIO_INICIO_X = 650
FLAVIO_SOL = 8 * TILE_SIZE

flavio = images_flavio[0].get_rect(
    midbottom=(FLAVIO_INICIO_X, FLAVIO_SOL)
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

    flavio.midbottom = (
        FLAVIO_INICIO_X,
        FLAVIO_SOL
    )

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

#Liste des rectangles des checkpoints
checkpoints = []

#On parcourt chaque ligne (i) puis chaque colonne (j) de la carte
for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        #Un "X" dans la carte = un checkpoint
        if mapa[i][j] == "X":

            #Rect de la taille de l'image du cristo, place par le milieu du bas
            #pour qu'il soit pose sur le sol et centre dans sa case
            checkpoints.append(
                images_cristo[0].get_rect(
                    midbottom=(
                        j * TILE_SIZE + TILE_SIZE // 2,  #x : centre de la case
                        (i + 1) * TILE_SIZE              #y : bas de la case
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
    movimento_x = 0

    if touches[K_LEFT]:
        movimento_x -= 7
        regarde_a_gauche = True
        en_mouvement = True

    if touches[K_RIGHT]:
        movimento_x += 7
        regarde_a_gauche = False
        en_mouvement = True

    mario.x += movimento_x

    # Colisao horizontal com os blocos
    for bloc in colisores:

        if mario.colliderect(bloc):

            if movimento_x > 0:
                mario.right = bloc.left

            elif movimento_x < 0:
                mario.left = bloc.right

    mario.left = max(
        0,
        min(mario.left, largura_mapa - mario.width)
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

                # Detecta quando Mario bate no bloco por baixo
                if topo_anterior >= bloc.bottom:

                    coluna = bloc.x // TILE_SIZE
                    linha = bloc.y // TILE_SIZE

                    if mapa[linha][coluna] == "Q":

                        posicao_bloco = (linha, coluna)

                        if posicao_bloco not in blocos_usados:

                            blocos_usados.add(posicao_bloco)

                            # Bloco dourado vira bloco usado
                            mapa[linha][coluna] = "U"

                            # Cria a bola dentro do bloco
                            nova_bola = BolaColecionavel(
                                bloc.x,
                                bloc.y,
                                frames_bola
                            )

                            bolas_colecionaveis.append(
                                nova_bola
                            )

                            print(
                                "Bola criada no bloco:",
                                linha, coluna
                            )

            vitesse_y = 0

    #################################################################
    # COLETA DO PODER
    #################################################################

    for bola in bolas_colecionaveis:

        if bola.atualizar(mario):

            tem_poder_bola = True

            print("Mario ganhou o poder da bola!")

    #################################################################
    # DISPARO COM F
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
                    x_bola,
                    y_bola,
                    direcao,
                    frames_bola
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
    # PROJETEIS E COLISAO COM FLAVIO
    #################################################################

    for projetil in projeteis[:]:

        projetil.atualizar(
            colisores,
            largura_mapa
        )

        if flavio_vivo and projetil.ativo:

            if projetil.rect.colliderect(flavio):

                flavio_vivo = False
                projetil.ativo = False

                print("Flavio foi eliminado!")

        if not projetil.ativo:
            projeteis.remove(projetil)

    #################################################################
    # MARIO TOCA FLAVIO
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

            point_reapparition = (
                cp.centerx,
                cp.bottom
            )

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

        # Remove os projeteis
        projeteis.clear()

        # Flavio reaparece
        reiniciar_flavio()

        if compteur_mort > 0:

            mario.midbottom = point_reapparition

        else:

            # Reinicia o jogo inteiro
            mario.midbottom = DEPART
            compteur_mort = 3

            point_reapparition = DEPART
            checkpoints_actives = []
            moedas = moedas_depart[:]

            mapa = [
                list(linha)
                for linha in mapa_original
            ]

            blocos_usados.clear()
            bolas_colecionaveis.clear()

            reiniciar_flavio()

    #################################################################
    # CAMERA
    #################################################################

    camera_x = mario.centerx - LARGURA // 2

    camera_x = max(
        0,
        min(
            camera_x,
            max(0, largura_mapa - LARGURA)
        )
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
                    (i + 1) * TILE_SIZE
                    - imagem.get_height()
                )

                if letra == "V":
                    y_tela += 8

                if -imagem.get_width() < x_tela < LARGURA:

                    screen.blit(
                        imagem,
                        (x_tela, y_tela)
                    )

    #################################################################
    # DESENHO DAS MOEDAS
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
    # DESENHO DOS CHECKPOINTS
    #################################################################

    for cp in checkpoints:

        x_tela_cp = int(cp.x - camera_x)

        if -cp.width < x_tela_cp < LARGURA:

            if cp in checkpoints_actives:
                imagem_cp = images_cristo[1]
            else:
                imagem_cp = images_cristo[0]

            screen.blit(
                imagem_cp,
                (x_tela_cp, cp.y)
            )

    #################################################################
    # DESENHO DAS BOLAS COLECIONAVEIS
    #################################################################

    for bola in bolas_colecionaveis:
        bola.desenhar(screen, camera_x)

    #################################################################
    # DESENHO DOS PROJETEIS
    #################################################################

    for projetil in projeteis:
        projetil.desenhar(screen, camera_x)

    #################################################################
    # DESENHO DE FLAVIO
    #################################################################

    if flavio_vivo:

        indice_flavio = (
            compteur_flavio // 8
        ) % len(MARCHE_FLAVIO)

        imagem_flavio = images_flavio[
            MARCHE_FLAVIO[indice_flavio]
        ]

        x_tela_flavio = int(flavio.x - camera_x)

        # Desenha Flavio na posicao correta da camera
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

    # Mario muda para o futebolista ao ganhar o poder
    if tem_poder_bola:
        imagens_ativas = images_futebol
    else:
        imagens_ativas = images

    if not au_sol:

        if vitesse_y < 0:
            sprite = imagens_ativas[SAUT]
        else:
            sprite = imagens_ativas[CHUTE]

    elif en_mouvement:

        compteur += 1

        indice_corrida = (
            compteur // 6
        ) % len(COURSE)

        sprite = imagens_ativas[
            COURSE[indice_corrida]
        ]

    else:

        compteur = 0
        sprite = imagens_ativas[REPOS]

    screen.blit(
        transform.flip(
            sprite,
            regarde_a_gauche,
            False
        ),
        (
            int(mario.x - camera_x),
            mario.y
        )
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

    #################################################################
    # ATUALIZA A TELA
    #################################################################

    display.update()
