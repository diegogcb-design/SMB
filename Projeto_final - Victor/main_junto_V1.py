
from pygame import *
import pygame
import sys
import os
import json
from pygame.locals import QUIT

from poderes import carregar_bola, BolaColecionavel, ProjetilBola

init()

LARGURA = 900
ALTURA = 600
TILE_SIZE = 64
FPS = 60

screen = display.set_mode((LARGURA, ALTURA))
display.set_caption('SMB - Cenario e Camera')
clock = time.Clock()

pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

#####################################################################
# TILESET E SPRITES
#####################################################################

tileset = image.load(
    os.path.join(pasta_assets, 'tileset_16x16.png')
).convert_alpha()

props = image.load(
    os.path.join(pasta_assets, 'props_sheet.png')
).convert_alpha()

with open(
    os.path.join(pasta_assets, 'sprite_index.json'),
    'r',
    encoding='utf-8'
) as arquivo:
    indice = json.load(arquivo)

sprites = {}

for nome, dados in indice.items():

    origem = (
        props if dados.get('sheet') == 'props_sheet.png'
        else tileset
    )

    area = Rect(
        dados['x'],
        dados['y'],
        dados['w'],
        dados['h']
    )

    imagem = Surface(
        (dados['w'], dados['h']),
        SRCALPHA
    )

    imagem.blit(origem, (0, 0), area)

    sprites[nome] = transform.scale(
        imagem,
        (dados['w'] * 4, dados['h'] * 4)
    )

#####################################################################
# MAPA
#####################################################################

with open(
    os.path.join(pasta, 'levels', 'level_1.txt'),
    'r',
    encoding='utf-8'
) as arquivo:

    mapa_original = [
        linha.rstrip('\n')
        for linha in arquivo
        if linha.strip()
    ]

# Lista de listas para poder trocar Q por U
mapa = [list(linha) for linha in mapa_original]

tiles = {
    'G': 'grass_t',
    'T': 'grass_m',
    'B': 'bricks',
    'Q': 'question_block',
    'U': 'question_block_used',
    'S': 'stone_bricks',
    'W': 'wood_planks',
    'F': 'flowers_red',
    'R': 'rock',
    'H': 'grass_tuft',
    'P': 'spikes',
    'A': 'tree',
    'N': 'pine_tree',
    'V': 'bush',
    'O': 'cloud',
    'M': 'mushroom',
    'E': 'star'
}

blocos_solidos = ['G', 'T', 'B', 'Q', 'U', 'S', 'W']

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

camera_x = 0.0

#####################################################################
# MOEDAS
#####################################################################

moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        if mapa[i][j] == 'C':

            moedas.append(
                (
                    j * TILE_SIZE + 16,
                    i * TILE_SIZE + 16
                )
            )

moedas_depart = moedas[:]

#####################################################################
# MARIO
#####################################################################

CASE = 32
ECHELLE = 2

DEBUT = 8
REPOS = DEBUT
COURSE = [
    DEBUT + 1,
    DEBUT + 2,
    DEBUT + 3,
    DEBUT + 2
]
SAUT = DEBUT + 4
CHUTE = DEBUT + 5


def charger_planche(nom):

    caminho = os.path.join(pasta, nom)

    planche = image.load(caminho).convert_alpha()

    images = []

    for i in range(planche.get_width() // CASE):

        case = planche.subsurface(
            Rect(i * CASE, 0, CASE, CASE)
        )

        images.append(
            transform.scale(
                case,
                (CASE * ECHELLE, CASE * ECHELLE)
            )
        )

    return images


# Mario normal
images = charger_planche("Perso.png")

# Mario com poder de futebol
# Usa um spritesheet especial, se existir
caminho_futebol = os.path.join(
    pasta, "Perso_futebol.png"
)

if os.path.exists(caminho_futebol):

    images_futebol = charger_planche(
        "Perso_futebol.png"
    )

    if len(images_futebol) <= CHUTE:
        print("Spritesheet de futebol incompleto.")
        images_futebol = None

else:
    images_futebol = None


# Aparencia alternativa se nao houver spritesheet
def criar_mario_futebol(sprite_original):

    sprite_novo = sprite_original.copy()

    # Colore o sprite para indicar o poder
    sprite_novo.fill(
        (255, 235, 80),
        special_flags=BLEND_RGB_MULT
    )

    return sprite_novo


DEPART = (100, 8 * TILE_SIZE)

mario = images[REPOS].get_rect(
    midbottom=DEPART
)

vitesse_y = 0
au_sol = False
regarde_a_gauche = False
compteur = 0

pieces = 0
police = font.Font(None, 48)
police_poder = font.Font(None, 32)

compteur_mort = 3

#####################################################################
# MONSTROS
#####################################################################

def charger_monstre(nom):

    caminho = os.path.join(pasta, nom)

    planche = image.load(caminho).convert_alpha()

    images_monstre = []

    for i in range(planche.get_width() // CASE):

        case = planche.subsurface(
            Rect(i * CASE, 0, CASE, CASE)
        )

        images_monstre.append(
            transform.scale(
                case,
                (CASE * ECHELLE, CASE * ECHELLE)
            )
        )

    return images_monstre


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

#####################################################################
# CHECKPOINTS
#####################################################################

planche_cristo = image.load(
    os.path.join(
        pasta,
        'Checkpoints',
        'cristo.png'
    )
).convert_alpha()

LARG_CRISTO = planche_cristo.get_width() // 2
HAUT_CRISTO = planche_cristo.get_height()

images_cristo = []

for i in range(2):

    area = Rect(
        i * LARG_CRISTO,
        0,
        LARG_CRISTO,
        HAUT_CRISTO
    )

    imagem = planche_cristo.subsurface(area)

    images_cristo.append(
        transform.scale(
            imagem,
            (LARG_CRISTO * 4, HAUT_CRISTO * 4)
        )
    )

checkpoints = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        if mapa[i][j] == 'X':

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

# Carrega o spritesheet da bola
frames_bola = carregar_bola()

# Bolas que aparecem ao bater nos blocos Q
bolas_colecionaveis = []

# Guarda quais blocos Q ja foram usados
blocos_usados = set()

# Mario comeca sem poder
tem_poder_bola = False

# Bolas disparadas por Mario
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
        0,
        min(
            mario.left,
            largura_mapa - mario.width
        )
    )

    #################################################################
    # SALTO E GRAVIDADE
    #################################################################

    if touches[K_UP] and au_sol:
        vitesse_y = -22

    vitesse_y += 1

    # Guarda o topo antes do movimento
    topo_anterior = mario.top

    mario.y += vitesse_y
    au_sol = False

    for bloc in colisores:

        if mario.colliderect(bloc):

            if vitesse_y > 0:

                # Mario estava caindo
                mario.bottom = bloc.top
                au_sol = True

            elif vitesse_y < 0:

                # Mario estava subindo
                mario.top = bloc.bottom

                # Confere se bateu embaixo do bloco
                if topo_anterior >= bloc.bottom:

                    coluna = bloc.x // TILE_SIZE
                    linha = bloc.y // TILE_SIZE

                    # Verifica se e um bloco dourado
                    if mapa[linha][coluna] == 'Q':

                        posicao_bloco = (linha, coluna)

                        if posicao_bloco not in blocos_usados:

                            # Marca o bloco como utilizado
                            blocos_usados.add(posicao_bloco)

                            # Troca Q por U
                            mapa[linha][coluna] = 'U'

                            # Cria uma bola dentro do bloco
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
                                linha,
                                coluna
                            )

            vitesse_y = 0

    #################################################################
    # COLETA DO PODER
    #################################################################

    for bola in bolas_colecionaveis:

        # Atualiza a animacao da bola saindo do bloco
        if bola.atualizar(mario):

            tem_poder_bola = True

            print("Mario ganhou o poder da bola!")

    #################################################################
    # DISPARO COM A TECLA F
    #################################################################

    agora = time.get_ticks()

    if touches[K_f] and tem_poder_bola:

        if agora - ultimo_disparo >= TEMPO_ENTRE_DISPAROS:

            # Direcao do disparo
            if regarde_a_gauche:
                direcao = -1
            else:
                direcao = 1

            # Posicao inicial da bola
            if direcao == 1:
                x_bola = mario.right
            else:
                x_bola = mario.left - 32

            y_bola = mario.centery - 16

            # Cria o projetil
            nova_bola = ProjetilBola(
                x_bola,
                y_bola,
                direcao,
                frames_bola
            )

            projeteis.append(nova_bola)

            ultimo_disparo = agora

    #################################################################
    # QUEDA EM BURACO
    #################################################################

    mort = False

    if mario.top > ALTURA:
        mort = True

    #################################################################
    # COLETA DAS MOEDAS
    #################################################################

    for moeda in moedas[:]:

        x, y = moeda

        area_moeda = Rect(
            x + 16,
            y + 16,
            32,
            32
        )

        if mario.colliderect(area_moeda):

            moedas.remove(moeda)
            pieces += 1

    #################################################################
    # MOVIMENTO DE FLAVIO
    #################################################################

    if flavio_vivo:

        flavio.x += vitesse_flavio

        if flavio.right >= FLAVIO_MAX_X:

            flavio.right = FLAVIO_MAX_X
            vitesse_flavio = -abs(vitesse_flavio)

        elif flavio.left <= FLAVIO_MIN_X:

            flavio.left = FLAVIO_MIN_X
            vitesse_flavio = abs(vitesse_flavio)

        compteur_flavio += 1

    #################################################################
    # MOVIMENTO DOS PROJETEIS
    #################################################################

    for projetil in projeteis[:]:

        projetil.atualizar(
            colisores,
            largura_mapa
        )

        # Verifica colisao com Flavio
        if flavio_vivo and projetil.ativo:

            if projetil.rect.colliderect(flavio):

                flavio_vivo = False
                projetil.ativo = False

                print("Flavio foi eliminado!")

        # Remove bolas inativas
        if not projetil.ativo:

            projeteis.remove(projetil)

    #################################################################
    # COLISAO MARIO COM FLAVIO
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

        if mario.colliderect(cp):

            if cp not in checkpoints_actives:

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
        touche_flavio = False

        # Mario perde o poder
        tem_poder_bola = False

        # Remove todos os projeteis
        projeteis.clear()

        if compteur_mort > 0:

            # Volta ao ultimo checkpoint
            mario.midbottom = point_reapparition

        else:

            # Reinicia o jogo
            mario.midbottom = DEPART
            compteur_mort = 3

            point_reapparition = DEPART
            checkpoints_actives = []
            moedas = moedas_depart[:]

            # Restaura os blocos dourados
            mapa = [
                list(linha)
                for linha in mapa_original
            ]

            blocos_usados.clear()
            bolas_colecionaveis.clear()

            # Restaura Flavio
            flavio_vivo = True

            flavio.midbottom = (
                FLAVIO_MIN_X,
                FLAVIO_SOL
            )

            vitesse_flavio = 2
            compteur_flavio = 0

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
    # DESENHO DO CENARIO
    #################################################################

    screen.fill((120, 180, 220))

    for i in range(len(mapa)):
        for j in range(len(mapa[i])):

            letra = mapa[i][j]

            if letra in tiles:

                imagem = sprites[tiles[letra]]

                x_tela = int(
                    j * TILE_SIZE - camera_x
                )

                y_tela = (
                    (i + 1) * TILE_SIZE
                    - imagem.get_height()
                )

                if letra == 'V':
                    y_tela += 8

                largura_imagem = imagem.get_width()

                if -largura_imagem < x_tela < LARGURA:

                    screen.blit(
                        imagem,
                        (x_tela, y_tela)
                    )

    #################################################################
    # DESENHO DAS MOEDAS
    #################################################################

    frame_moeda = (time.get_ticks() // 150) % 4
    nome_moeda = 'coin_' + str(frame_moeda)

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
                image_cp = images_cristo[1]
            else:
                image_cp = images_cristo[0]

            screen.blit(
                image_cp,
                (x_tela_cp, cp.y)
            )

    #################################################################
    # DESENHO DAS BOLAS COLECIONAVEIS
    #################################################################

    # Desenha depois do cenario para ficarem visiveis
    for bola in bolas_colecionaveis:

        bola.desenhar(
            screen,
            camera_x
        )

    #################################################################
    # DESENHO DOS PROJETEIS
    #################################################################

    for projetil in projeteis:

        projetil.desenhar(
            screen,
            camera_x
        )

    #################################################################
    # DESENHO DE FLAVIO
    #################################################################

    if flavio_vivo:

        indice_flavio = (
            compteur_flavio // 8
        ) % len(MARCHE_FLAVIO)

        image_flavio = images_flavio[
            MARCHE_FLAVIO[indice_flavio]
        ]

        x_tela_flavio = int(
            flavio.x - camera_x
        )

        if -flavio.width < x_tela_flavio < LARGURA:

            screen.blit(
                transform.flip(
                    image_flavio,
                    vitesse_flavio < 0,
                    False
                ),
                (x_tela_flavio, flavio.y)
            )

    #################################################################
    # ANIMACAO DE MARIO
    #################################################################

    # Usa o spritesheet de futebol quando o poder esta ativo
    if tem_poder_bola and images_futebol is not None:
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

    # Se nao houver spritesheet especial,
    # aplica uma cor para indicar o poder
    if tem_poder_bola and images_futebol is None:

        sprite = criar_mario_futebol(sprite)

    # Desenha Mario
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
        'Moedas : ' + str(pieces),
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
        'Vidas : ' + str(compteur_mort),
        True,
        cor_vidas
    )

    screen.blit(
        texto_moedas,
        (15, 15)
    )

    screen.blit(
        texto_vidas,
        (750, 15)
    )

    # Indicador visual do poder de futebol
    if tem_poder_bola:

        texto_poder = police_poder.render(
            'PODER BOLA - F PARA DISPARAR',
            True,
            (255, 255, 0)
        )

        screen.blit(
            texto_poder,
            (15, 65)
        )

    #################################################################
    # ATUALIZA A TELA
    #################################################################

    display.update()

