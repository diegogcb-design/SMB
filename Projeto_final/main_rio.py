# Configuração e arquivos do jogo
# ----------------------------------------------------------------------

from pygame import *
import sys
import os
import json
from pygame.locals import QUIT

from poderes import carregar_bola, BolaColecionavel, ProjetilBola   # super-pouvoir du ballon

init()

LARGURA = 900
ALTURA = 600
TILE_SIZE = 64
FPS = 60

screen = display.set_mode((LARGURA, ALTURA))
display.set_caption('SMB - Cenario e Camera')
clock = time.Clock()

pasta = os.path.dirname(os.path.abspath(__file__))
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

# Aceita os arquivos tanto na pasta principal quanto nas subpastas.
def localizar_arquivo(nome, *pastas):
    for pasta_opcao in pastas:
        caminho = os.path.join(pasta_opcao, nome)
        if os.path.isfile(caminho):
            return caminho
    raise FileNotFoundError(f'Arquivo {nome} nao encontrado em: {pastas}')

# Imagens e indice do pacote
# Os sprites sao ampliados 4 vezes
tileset = image.load(os.path.join(pasta_assets, 'tileset_16x16.png')).convert_alpha()
props = image.load(os.path.join(pasta_assets, 'props_sheet.png')).convert_alpha()

with open(os.path.join(pasta_assets, 'sprite_index.json'), 'r', encoding='utf-8') as arquivo:
    indice = json.load(arquivo)  # Coordenadas do JSON -> dicionario Python

sprites = {}  # Dicionario vazio

for nome, dados in indice.items():
    # Escolhe de qual PNG tiramos o sprite
    origem = props if dados.get('sheet') == 'props_sheet.png' else tileset

    # Seleciona o retangulo que sera recortado
    area = Rect(dados['x'], dados['y'], dados['w'], dados['h'])

    # Cria uma superficie vazia e transparente
    imagem = Surface((dados['w'], dados['h']), SRCALPHA)

    # Copia a parte selecionada da imagem original
    imagem.blit(origem, (0, 0), area)

    # Amplia a imagem e guarda no dicionario
    sprites[nome] = transform.scale(
        imagem, (dados['w'] * 4, dados['h'] * 4)
    )

# Cenario do Rio: panorama e tiles originais em pixel art
planche_rio = image.load(localizar_arquivo('rio_tiles.png', pasta, pasta_assets)).convert_alpha()
letras_rio = 'a1fb2gc3hd4ie5jklmnozp'
for i, letra in enumerate(letras_rio):
    area_rio = Rect(i * 16, 0, 16, 16)
    sprites['rio_' + letra] = transform.scale(planche_rio.subsurface(area_rio), (TILE_SIZE, TILE_SIZE))

fundo_rio = image.load(localizar_arquivo('rio_bg.png', pasta, pasta_assets)).convert()
fundo_rio = transform.scale(fundo_rio, (fundo_rio.get_width() * 4, ALTURA))


# Áudio
# ----------------------------------------------------------------------


# Musica de fundo - funk carioca
mixer.init()
mixer.music.load(os.path.join(pasta, "musica.mp3"))
mixer.music.set_volume(0.4)
mixer.music.play(-1)

# Efeito sonoro do Flavio
som_flavio = mixer.Sound(os.path.join(pasta, "flavio.wav"))
som_flavio.set_volume(0.8)

# Efeitos sonoros do jogo
som_salto = mixer.Sound(os.path.join(pasta, "salto.wav"))
som_moeda = mixer.Sound(os.path.join(pasta, "moeda.wav"))
som_chute = mixer.Sound(os.path.join(pasta, "chute.wav"))
# O arquivo morte.wav contem o efeito de power-up.
# Aceita tambem powerup.wav caso o arquivo tenha sido renomeado.
arquivo_powerup = os.path.join(pasta, "powerup.wav")
if not os.path.isfile(arquivo_powerup):
    arquivo_powerup = os.path.join(pasta, "morte.wav")
som_powerup = mixer.Sound(arquivo_powerup)
som_bloco = mixer.Sound(os.path.join(pasta, "bloco.wav"))

som_salto.set_volume(0.4)
som_moeda.set_volume(0.5)
som_chute.set_volume(0.6)
som_powerup.set_volume(0.5)
som_bloco.set_volume(0.5)


# Mapa, colisores e cenário
# ----------------------------------------------------------------------


# Mapa em arquivo de texto
with open(localizar_arquivo('level_1.txt', pasta, os.path.join(pasta, 'levels')), 'r', encoding='utf-8') as arquivo:
    mapa_original = [linha.rstrip('\n') for linha in arquivo if linha.strip()]

mapa = [list(linha) for linha in mapa_original]   # liste de listes : permet de changer un 'Q' en 'U'

# Letras do mapa e sprites correspondentes
tiles = {
    'G': 'grass_t',              # Grama superior
    'T': 'grass_m',              # Terra
    'B': 'bricks',               # Tijolos
    'Q': 'question_block',       # Bloco dourado
    'U': 'question_block_used',  # Bloco utilizado
    'S': 'stone_bricks',         # Tijolos de pedra
    'W': 'wood_planks',          # Madeira
    'F': 'flowers_red',          # Flores
    'R': 'rock',                 # Pedra decorativa
    'H': 'grass_tuft',           # Vegetacao pequena
    'P': 'spikes',               # Espinhos
    'A': 'tree',                 # Arvore
    'N': 'pine_tree',            # Pinheiro
    'V': 'bush',                 # Arbusto
    'O': 'cloud',                # Nuvem
    'M': 'mushroom',             # Cogumelo
    'E': 'star'                  # Estrela
}

tiles.update({letra: 'rio_' + letra for letra in letras_rio})

# Blocos que possuem colisao com o personagem
blocos_solidos = ['G', 'T', 'B', 'Q', 'U', 'S', 'W'] + list('abcde12345fghij')

# Colisoes do cenario
colisores = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] in blocos_solidos:
            colisores.append(
                Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )

largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE
# As dez linhas de baixo formam a faixa de jogo original.
altura_extra = max(0, len(mapa) - 10) * TILE_SIZE


ceu_alto = transform.scale(fundo_rio.subsurface((0, 0, fundo_rio.get_width(), 1)),
                           (fundo_rio.get_width(), max(1, altura_extra // 3 + 1)))

# Fachadas em segundo plano. Janelas e sombras distinguem as paredes da rota jogável.
for marca, janela, parede in [(':', 'g', '2'), (';', 'j', '5'), (',', 'h', '3')]:
    for chave in [janela, parede]:
        fundo = sprites['rio_' + chave].copy()
        fundo.fill((146, 153, 176), special_flags=BLEND_RGB_MULT)
        sprites['parede_' + chave] = fundo
    tiles[marca] = 'parede_' + parede
janelas = {':': 'parede_g', ';': 'parede_j', ',': 'parede_h'}

# Varal de bandeirinhas entre as duas marcas no terraço.
varais = []
for i, linha in enumerate(mapa):
    postes = [j for j, letra in enumerate(linha) if letra == '~']
    varais.extend((a, b, i) for a, b in zip(postes[::2], postes[1::2]))


def desenhar_cenario():
    # Parallax: a cidade se move mais devagar do que o primeiro plano.
    deslocamento_fundo = min(int(camera_x * 0.53), fundo_rio.get_width() - LARGURA)
    ceu = (altura_extra - camera_y) // 3
    screen.blit(ceu_alto, (-deslocamento_fundo, ceu - ceu_alto.get_height()))
    screen.blit(fundo_rio, (-deslocamento_fundo, ceu))

    # Dessin du mapa
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):

            letra = mapa[i][j]

            if letra in tiles:
                # Busca a imagem correspondente a letra
                chave = tiles[letra]
                if letra in janelas and j % 3 == 1 and i % 2 == 0:
                    chave = janelas[letra]
                imagem = sprites[chave]

                # Calcula a posicao horizontal considerando a camera
                x_tela = int(j * TILE_SIZE - camera_x)

                # Ajusta a altura dos objetos maiores que um bloco
                # Assim as arvores crescem para cima
                y_tela = (i + 1) * TILE_SIZE - imagem.get_height() - camera_y

                # Ajusta o arbusto para ficar mais perto do chao
                if letra == 'V':
                    y_tela += 8

                # Verifica se a imagem esta visivel na tela
                largura_imagem = imagem.get_width()

                if -largura_imagem < x_tela < LARGURA:
                    screen.blit(imagem, (x_tela, y_tela))

    for inicio, fim, linha in varais:
        x1 = inicio*TILE_SIZE + 12 - camera_x
        x2 = (fim+1)*TILE_SIZE - 12 - camera_x
        if x2 < 0 or x1 >= LARGURA:
            continue
        base = (linha+1)*TILE_SIZE - camera_y
        for x in (x1, x2):
            draw.line(screen, (87, 63, 65), (x, base), (x, base-78), 4)
        cores = [(255, 194, 62), (45, 160, 111), (245, 109, 89), (100, 175, 211)]
        pontos = []
        for k in range(17):
            t = k/16
            x = round(x1 + (x2-x1)*t)
            y = round(base-76 + 75*t*(1-t))
            pontos.append((x,y))
            if 0 < k < 16:
                draw.polygon(screen, cores[k%4], [(x-6,y), (x+6,y), (x,y+13)])
        draw.lines(screen, (71, 63, 72), False, pontos, 2)


# Câmera
# ----------------------------------------------------------------------


camera_x = 0.0
camera_y = altura_extra


def atualizar_camera(mort):
    global camera_x, camera_y
    # Camera
    # A camera acompanha Mario horizontalmente
    camera_x = mario.centerx - LARGURA // 2

    # Impede a camera de mostrar areas fora do mapa
    camera_x = max(
        0,
        min(camera_x, max(0, largura_mapa - LARGURA))
    )

    # Zona morta: a câmera começa a subir perto do topo da tela.
    if mort:
        camera_y = max(0, min(altura_extra, mario.bottom - 440))
    camera_y = max(0, min(altura_extra, min(camera_y, mario.top - 100)))
    camera_y = min(altura_extra, max(camera_y, mario.bottom - 445))


# Moedas
# ----------------------------------------------------------------------


moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == 'C':
            moedas.append(
                (j * TILE_SIZE + 16, i * TILE_SIZE + 16)
            )  # Centraliza a moeda


moedas_depart = moedas[:]       # copie des pieces, pour tout remettre en cas de game over


def coletar_moedas():
    global pieces
    for moeda in moedas[:]:                     # [:] = copie de la liste, pour pouvoir supprimer dedans
        x, y = moeda
        if mario.colliderect(Rect(x + 16, y + 16, 32, 32)):   # Mario touche la piece ?
            moedas.remove(moeda)                # la piece disparait
            som_moeda.play()
            pieces += 1                         # +1 au compteur


def desenhar_moedas():
    # Alterna entre as quatro imagens da moeda
    frame_moeda = (time.get_ticks() // 150) % 4
    nome_moeda = 'coin_' + str(frame_moeda)

    if nome_moeda in sprites:
        for x, y in moedas:

            # Posicao horizontal da moeda na tela
            x_tela = int(x - camera_x)

            if -TILE_SIZE < x_tela < LARGURA:
                screen.blit(sprites[nome_moeda], (x_tela, y - camera_y))


# Mario: movimento, colisões e animação
# ----------------------------------------------------------------------


CASE = 32
ECHELLE = 2

DEBUT = 8                                             # numero de la premiere image du perso dans la planche
REPOS = DEBUT
COURSE = [DEBUT + 1, DEBUT + 2, DEBUT + 3, DEBUT + 2]
SAUT = DEBUT + 4
CHUTE = DEBUT + 5

def charger_planche(nom):                                       # decoupe la planche en petites images
    dossier = os.path.dirname(os.path.abspath(__file__))        # dossier ou se trouve ce fichier .py
    planche = image.load(os.path.join(dossier, nom)).convert_alpha()  # ouvre l'image (avec transparence)
    images = []                                                 # liste vide qui va contenir les images
    for i in range(planche.get_width() // CASE):                # nombre d'images = largeur / 32
        case = planche.subsurface(Rect(i * CASE, 0, CASE, CASE))  # decoupe la i-eme case
        images.append(transform.scale(case, (CASE * ECHELLE, CASE * ECHELLE)))  # l'agrandit et l'ajoute a la liste
    return images                                               # renvoie la liste des images

images = charger_planche("Perso.png")   # toutes les images du perso, rangees dans une liste
images_futebol = charger_planche("Perso_futebol.png")   # images du perso en footballeur (avec le pouvoir)

DEPART = (100, altura_extra + 8 * TILE_SIZE)
mario = images[REPOS].get_rect(midbottom=DEPART)  # rectangle de Mario (position + taille), pieds sur DEPART
vitesse_y = 0
au_sol = False
regarde_a_gauche = False
compteur = 0               # compte les images pour faire defiler l'animation de course
pieces = 0                 # nombre de pieces ramassees


compteur_mort = 3                # nombre de vies restantes


def mover_mario(touches):
    global regarde_a_gauche, vitesse_y, au_sol
    # Deplacement gauche / droite
    en_mouvement = False
    movimento_x = 0             # deplacement horizontal de cette image (- gauche, + droite)

    if touches[K_LEFT]:
        movimento_x -= 7
        regarde_a_gauche = True
        en_mouvement = True

    if touches[K_RIGHT]:
        movimento_x += 7
        regarde_a_gauche = False
        en_mouvement = True

    mario.x += movimento_x

    # Colisao horizontal com os blocos (selon le vrai sens du deplacement)
    for bloc in colisores:
        if mario.colliderect(bloc):
            if movimento_x > 0:
                mario.right = bloc.left
            elif movimento_x < 0:
                mario.left = bloc.right

    #limite do mapa para Mario
    mario.left = max(0, min(mario.left, largura_mapa - mario.width))

    # Saut et gravite
    if touches[K_UP] and au_sol:
        vitesse_y = -22
        som_salto.play()
    vitesse_y += 1
    topo_anterior = mario.top   # haut de Mario avant de bouger (pour savoir s'il tape un bloc par dessous)
    mario.y += vitesse_y
    au_sol = False

    # Colisao vertical: encontra todos os blocos antes de corrigir a posicao.
    blocos_tocados = [bloc for bloc in colisores if mario.colliderect(bloc)]

    if blocos_tocados:
        if vitesse_y > 0:
            # Mario estava caindo: pousa na superficie mais alta.
            mario.bottom = min(bloc.top for bloc in blocos_tocados)
            au_sol = True

        elif vitesse_y < 0:
            # Mario estava subindo: encontra o teto atingido primeiro.
            limite = max(bloc.bottom for bloc in blocos_tocados)

            # Verifica todos os blocos nesse teto, inclusive os blocos Q.
            for bloc in blocos_tocados:
                if bloc.bottom == limite and topo_anterior >= bloc.bottom:
                    linha = bloc.y // TILE_SIZE
                    coluna = bloc.x // TILE_SIZE
                    if mapa[linha][coluna] == 'Q' and (linha, coluna) not in blocos_usados:
                        blocos_usados.add((linha, coluna))
                        mapa[linha][coluna] = 'U'
                        som_bloco.play()
                        bolas_colecionaveis.append(
                            BolaColecionavel(bloc.x, bloc.y, frames_bola)
                        )

            mario.top = limite

        vitesse_y = 0
    return en_mouvement


def desenhar_mario(en_mouvement):
    global compteur
    imagens_ativas = images_futebol if tem_poder_bola else images
    if not au_sol:
        sprite = imagens_ativas[SAUT if vitesse_y < 0 else CHUTE]   # image de saut s'il monte, de chute s'il descend
    elif en_mouvement:                                      # s'il marche
        compteur += 1                                       # on avance le compteur
        sprite = imagens_ativas[COURSE[compteur // 6 % len(COURSE)]]  # change d'image de course toutes les 6 images
    else:                                                   # s'il est immobile
        compteur = 0
        sprite = imagens_ativas[REPOS]

    # Dessine Mario e inverte a imagem quando olha para a esquerda
    screen.blit(
        transform.flip(sprite, regarde_a_gauche, False),
        (int(mario.x - camera_x), mario.y - camera_y)
    )


# Inimigos: Flavio, palmeira e lula
# ----------------------------------------------------------------------


images_flavio = charger_planche(os.path.join("Monstres", "flavio.png"))  # 5 images : 0-3 marche, 4 ecrase

MARCHE_FLAVIO = [0, 1, 2, 3]   # images utilisees pour l'animation de marche

# Zone d'aller-retour de Flavio (en pixels dans le MONDE, pas a l'ecran)
FLAVIO_MIN_X = 5 * TILE_SIZE    # bord gauche de la patrouille (colonne 5 du mapa)
FLAVIO_MAX_X = 12 * TILE_SIZE   # bord droit de la patrouille (colonne 12 du mapa)
FLAVIO_SOL   = altura_extra + 8 * TILE_SIZE    # haut de la ligne 'G' (ligne 8) -> ses pieds sont poses dessus

flavio = images_flavio[0].get_rect(midbottom=(FLAVIO_MIN_X, FLAVIO_SOL))  # rectangle de Flavio
vitesse_flavio = 2              # pixels par image ; le signe donne la direction (+ droite, - gauche)
compteur_flavio = 0             # pour faire defiler son animation
touche_flavio = False           # True tant que Mario est en contact avec Flavio
flavio_vivo = True              # False quand Flavio a ete touche par un ballon

def reiniciar_flavio():                 # remet Flavio vivant a sa position de depart
    global vitesse_flavio, compteur_flavio, touche_flavio, flavio_vivo
    flavio_vivo = True
    flavio.midbottom = (FLAVIO_MIN_X, FLAVIO_SOL)
    vitesse_flavio = 2
    compteur_flavio = 0
    touche_flavio = False

def charger_palmier(nom):                                       # decoupe la planche en petites images
    dossier = os.path.dirname(os.path.abspath(__file__))        # dossier ou se trouve ce fichier .py
    planche = image.load(os.path.join(dossier, nom)).convert_alpha()  # ouvre l'image (avec transparence)
    images = []                                                 # liste vide qui va contenir les images
    for i in range(planche.get_width() // CASE):                # nombre d'images = largeur / 32
        case = planche.subsurface(Rect(i * CASE, 0, CASE, CASE))  # decoupe la i-eme case
        images.append(transform.scale(case, (CASE * 4, CASE * 4)))  # l'agrandit et l'ajoute a la liste
    return images

images_palmier = charger_palmier(os.path.join("Monstres", "palmier.png"))  # 4 images : 0-3 marche

MARCHE_PALMIER = [0, 1, 2, 3]   # images utilisees pour l'animation de marche du palmier
PALMIER_MIN_X = 23 * TILE_SIZE    # bord gauche de la patrouille (colonne 5 du mapa)
PALMIER_MAX_X = 26 * TILE_SIZE   # bord droit de la patrouille (colonne 12 du mapa)
PALMIER_SOL   = altura_extra + 8 * TILE_SIZE    # haut de la ligne 'G' (ligne 8) -> ses pieds sont poses dessus

palmier = images_palmier[0].get_rect(midbottom=(PALMIER_MIN_X, PALMIER_SOL))  # rectangle du palmier

vitesse_palmier = 3              # pixels par image ; le signe donne la direction (+ droite, - gauche)
compteur_palmier = 0             # pour faire defiler son animation
touche_palmier = False           # True tant que Mario est en contact avec le palmier
palmier_vivo = True              # False quand le palmier a ete touche par un ballon

def reiniciar_palmier():                 # remet le palmier vivant a sa position de depart
    global vitesse_palmier, compteur_palmier, touche_palmier, palmier_vivo
    palmier_vivo = True
    palmier.midbottom = (PALMIER_MIN_X, PALMIER_SOL)
    vitesse_palmier = 3
    compteur_palmier = 0
    touche_palmier = False


# LULA

images_lula = charger_planche(os.path.join("Monstres", "lula.png"))  # 4 images : 0-3 marche

MARCHE_LULA = [0, 1, 2, 3]   # images utilisees pour l'animation de marche de la lula
LULA_MIN_X = 51 * TILE_SIZE    # bord gauche de la patrouille (colonne 5 du mapa)  # bord droit de la patrouille
LULA_SOL   = altura_extra + 5 * TILE_SIZE    # haut de la ligne 'G'

lula = images_lula[0].get_rect(midbottom=(LULA_MIN_X, LULA_SOL))  # rectangle de la lula

vitesse_lula = -9              # pixels par image ; le signe donne la direction (+ droite, - gauche)
compteur_lula = 0             # pour faire defiler son animation
touche_lula = False           # True tant que Mario est en contact avec la lula
lula_viva = True              # False quand la lula a ete touche par un ballon

def reiniciar_lula():                 # remet la lula vivante a sa position de depart
    global vitesse_lula, compteur_lula, touche_lula, lula_viva
    lula_viva = True
    lula.midbottom = (LULA_MIN_X, LULA_SOL)
    vitesse_lula = 2
    compteur_lula = 0
    touche_lula = False


def mover_inimigos():
    global vitesse_flavio, vitesse_palmier, vitesse_lula, compteur_flavio, compteur_palmier, compteur_lula
    if flavio_vivo:
        flavio.x += vitesse_flavio
        if flavio.right >= FLAVIO_MAX_X:        # arrive au bout a droite -> repart a gauche
            flavio.right = FLAVIO_MAX_X         # permet de remettre flavio a sa sprint d'avant
            vitesse_flavio = -2
        elif flavio.left <= FLAVIO_MIN_X:       # arrive au bout a gauche -> repart a droite
            flavio.left = FLAVIO_MIN_X          # permet de remettre flavio a sa sprint d'avant
            vitesse_flavio = 2
        compteur_flavio += 1

    if palmier_vivo:
        palmier.x += vitesse_palmier
        if palmier.right >= PALMIER_MAX_X:        # arrive au bout a droite -> repart a gauche
            palmier.right = PALMIER_MAX_X         # permet de remettre le palmier a sa sprint d'avant
            vitesse_palmier = -3
        elif palmier.left <= PALMIER_MIN_X:       # arrive au bout a gauche -> repart a droite
            palmier.left = PALMIER_MIN_X          # permet de remettre le palmier a sa sprint d'avant
            vitesse_palmier = 3
        compteur_palmier += 1

    if lula_viva:
        lula.y += vitesse_lula
        if lula.bottom >= LULA_SOL:  # Si il arrive en bas
            lula.bottom = LULA_SOL  # Il reste dans la limite
            vitesse_lula = -9  # Il remonte
        elif lula.bottom <= LULA_SOL - 4 * TILE_SIZE:  # Si il arrive en haut
            lula.bottom = LULA_SOL - 4 * TILE_SIZE  # Il reste dans la limite
            vitesse_lula = 9  # Il redescend

    compteur_lula += 1  # Anime Lula


def verificar_contato_com_inimigos():
    global touche_flavio, touche_palmier, touche_lula
    mort = False
    # Mario touche Flavio -> perd UNE seule vie par contact
    if flavio_vivo and mario.colliderect(flavio):
        if not touche_flavio:          # le contact vient de commencer
            som_flavio.play()
            mort = True
        touche_flavio = True           # tant qu'il reste colle, on ne retire plus rien
    else:
        touche_flavio = False          # contact termine -> la prochaine touche comptera

    if palmier_vivo and mario.colliderect(palmier):
        if not touche_palmier:          # le contact vient de commencer
            mort = True
        touche_palmier = True           # tant qu'il reste colle, on ne retire plus rien``
    else:
        touche_palmier = False          # contact termine -> la prochaine touche comptera

    if lula_viva and mario.colliderect(lula):
        if not touche_lula:          # le contact vient de commencer
            mort = True
        touche_lula = True           # tant qu'il reste colle, on ne retire plus rien``
    else:
        touche_lula = False          # contact termine -> la prochaine touche comptera
    return mort


def desenhar_inimigos():
    if flavio_vivo:
        image_flavio = images_flavio[MARCHE_FLAVIO[compteur_flavio // 8 % len(MARCHE_FLAVIO)]]
        x_tela_flavio = int(flavio.x - camera_x)          # position a l'ecran (camera)
        if -flavio.width < x_tela_flavio < LARGURA:        # dessine seulement s'il est visible
            screen.blit(
                transform.flip(image_flavio, vitesse_flavio < 0, False),  # regarde dans le sens de la marche
                (x_tela_flavio, flavio.y - camera_y)
            )

    if palmier_vivo:
        image_palmier = images_palmier[MARCHE_PALMIER[compteur_palmier // 8 % len(MARCHE_PALMIER)]]
        x_tela_palmier = int(palmier.x - camera_x)          # position a l'ecran (camera)
        if -palmier.width < x_tela_palmier < LARGURA:        # dessine seulement s'il est visible
            screen.blit(
                transform.flip(image_palmier, vitesse_palmier < 0, False),  # regarde dans le sens de la marche
                (x_tela_palmier, palmier.y - camera_y)
            )

    if lula_viva:
        image_lula = images_lula[MARCHE_LULA[compteur_lula // 8 % len(MARCHE_LULA)]]
        x_tela_lula = int(lula.x - camera_x)          # position a l'ecran (camera)
        if -lula.width < x_tela_lula < LARGURA:        # dessine seulement s'il est visible
            screen.blit(
                transform.flip(image_lula, vitesse_lula < 0, False),  # regarde dans le sens de la marche
                (x_tela_lula, lula.y - camera_y)
            )


# Poder da bola e projéteis
# ----------------------------------------------------------------------


frames_bola = carregar_bola()   # images animees du ballon

bolas_colecionaveis = []        # ballons sortis des blocs '?' (a ramasser)
blocos_usados = set()           # blocs '?' deja frappes (ligne, colonne)

tem_poder_bola = False          # True quand Mario a ramasse un ballon
projeteis = []                  # ballons tires par Mario

ultimo_disparo = -1000          # moment du dernier tir (en ms)
TEMPO_ENTRE_DISPAROS = 350      # temps minimum entre deux tirs (en ms)


def atualizar_poder(touches):
    global tem_poder_bola, ultimo_disparo
    for bola in bolas_colecionaveis:
        if bola.atualizar(mario):
            if not tem_poder_bola:
                som_powerup.play()
            tem_poder_bola = True

    # Tir d'un ballon avec la touche F
    agora = time.get_ticks()
    if touches[K_f] and tem_poder_bola and agora - ultimo_disparo >= TEMPO_ENTRE_DISPAROS:
        direcao = -1 if regarde_a_gauche else 1
        x_bola = mario.left - 32 if regarde_a_gauche else mario.right   # le ballon part devant Mario
        projeteis.append(ProjetilBola(x_bola, mario.centery - 16, direcao, frames_bola))
        ultimo_disparo = agora
        som_chute.play()


def atualizar_projeteis():
    global flavio_vivo, palmier_vivo
    for projetil in projeteis[:]:
        projetil.atualizar(colisores, largura_mapa)
        if flavio_vivo and projetil.ativo and projetil.rect.colliderect(flavio):
            flavio_vivo = False
            projetil.ativo = False
        if palmier_vivo and projetil.ativo and projetil.rect.colliderect(palmier):
            palmier_vivo = False
            projetil.ativo = False
        if not projetil.ativo:
            projeteis.remove(projetil)


def desenhar_bolas():
    for bola in bolas_colecionaveis:
        bola.desenhar(screen, camera_x, camera_y)
    for projetil in projeteis:
        projetil.desenhar(screen, camera_x, camera_y)


# Checkpoints, vidas e reaparecimento
# ----------------------------------------------------------------------


planche_cristo = image.load(os.path.join(pasta, 'Checkpoints', 'cristo.png')).convert_alpha()
LARG_CRISTO = planche_cristo.get_width() // 2          # 2 images : 0 = eteint, 1 = active (aureole)
HAUT_CRISTO = planche_cristo.get_height()
images_cristo = [
    transform.scale(
        planche_cristo.subsurface(Rect(i * LARG_CRISTO, 0, LARG_CRISTO, HAUT_CRISTO)),
        (LARG_CRISTO * 4, HAUT_CRISTO * 4)              # agrandi x4 comme le tileset
    )
    for i in range(2)
]

# Un checkpoint = la lettre 'X' dans le mapa
checkpoints = []        # liste de rectangles (zone ou Mario active le checkpoint)
for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == 'X':
            checkpoints.append(
                images_cristo[0].get_rect(midbottom=(j * TILE_SIZE + TILE_SIZE // 2, (i + 1) * TILE_SIZE))
            )

checkpoints_actives = []        # checkpoints deja touches par Mario (pour l'image avec aureole)
point_reapparition = DEPART     # ou Mario reapparait apres une mort (au debut : le depart)


def ativar_checkpoint():
    global point_reapparition
    for cp in checkpoints:
        if mario.colliderect(cp) and cp not in checkpoints_actives:
            checkpoints_actives.append(cp)
            point_reapparition = (cp.centerx, cp.bottom)


def desenhar_checkpoints():
    for cp in checkpoints:
        x_tela_cp = int(cp.x - camera_x)                # position a l'ecran (on enleve le decalage de la camera)
        if -cp.width < x_tela_cp < LARGURA:            # dessine seulement s'il est visible
            image_cp = images_cristo[1] if cp in checkpoints_actives else images_cristo[0]   # avec aureole s'il est active
            screen.blit(image_cp, (x_tela_cp, cp.y - camera_y))


def perder_vida():
    global compteur_mort, vitesse_y, au_sol, pieces, tem_poder_bola
    global point_reapparition, checkpoints_actives, moedas, mapa
    som_powerup.stop()
    compteur_mort -= 1
    vitesse_y = 0
    au_sol = False
    pieces = 0
    tem_poder_bola = False          # Mario perd le pouvoir
    # Reativa os blocos de poder depois de perder uma vida.
    for linha, coluna in blocos_usados:
        mapa[linha][coluna] = 'Q'
    blocos_usados.clear()
    bolas_colecionaveis.clear()
    projeteis.clear()               # les ballons tires disparaissent
    reiniciar_flavio()              # Flavio revient
    reiniciar_palmier()             # le palmier revient
    reiniciar_lula()                 # la lula revient
    if compteur_mort > 0:
        # Il reste des vies -> retour au dernier checkpoint
        mario.midbottom = point_reapparition
    else:
        # Plus de vies -> tout recommence depuis le debut
        mario.midbottom = DEPART
        compteur_mort = 3
        point_reapparition = DEPART
        checkpoints_actives = []
        moedas = moedas_depart[:]
        mapa = [list(linha) for linha in mapa_original]   # les blocs '?' reviennent
        blocos_usados.clear()
        bolas_colecionaveis.clear()


# Bandeira e condição de vitória
# ----------------------------------------------------------------------


# A exclamação marca o pé do mastro no arquivo do nível.
linha_meta, coluna_meta = next((i, linha.index('!')) for i, linha in enumerate(mapa) if '!' in linha)
base_meta = (linha_meta + 1) * TILE_SIZE
mastro = Rect(coluna_meta * TILE_SIZE + 24, base_meta - 4 * TILE_SIZE, 8, 4 * TILE_SIZE)

def desenhar_meta():
    x = mastro.x - int(camera_x)
    y = mastro.top - camera_y
    draw.rect(screen, (236, 238, 226), (x, y, mastro.width, mastro.height))
    draw.circle(screen, (255, 205, 57), (x + 4, y), 7)
    draw.rect(screen, (19, 145, 79), (x + 8, y + 6, 56, 36))
    draw.polygon(screen, (255, 216, 55), [(x+12, y+24), (x+36, y+9), (x+60, y+24), (x+36, y+39)])
    draw.circle(screen, (35, 68, 146), (x+36, y+24), 9)


def chegou_a_meta():
    return mario.colliderect(mastro)


# Interface: menu, tela final e placar
# ----------------------------------------------------------------------


police = font.Font(None, 48)   # police pour afficher le compteur de pieces
police_poder = font.Font(None, 32)   # police plus petite pour le message du pouvoir


def painel(titulo, linhas):
    caixa = Rect(120, 174, 660, 250)
    draw.rect(screen, (23, 42, 54), caixa, border_radius=12)
    draw.rect(screen, (255, 205, 57), caixa, 3, border_radius=12)
    for i, linha in enumerate([titulo, *linhas]):
        fonte = police if i == 0 else police_poder
        cor = (255, 215, 65) if i == 0 else (255, 255, 255)
        texto = fonte.render(linha, True, cor)
        screen.blit(texto, texto.get_rect(center=(caixa.centerx, caixa.top + 52 + 46*i)))


def desenhar_placar():
    texte = police.render('Moedas : ' + str(pieces), True, (255, 255, 255))
    if compteur_mort == 2 :
        vidas = police.render('Vidas : ' + str(compteur_mort), True, "orange")
    elif compteur_mort == 1 :
        vidas = police.render('Vidas : ' + str(compteur_mort), True, "red")
    else :
        vidas = police.render('Vidas : ' + str(compteur_mort), True, (255, 255, 255))
    screen.blit(texte, (15, 15))
    screen.blit(vidas, (750, 15))

    # Message quand Mario a le pouvoir
    if tem_poder_bola:
        texte_poder = police_poder.render('PODER BOLA - F PARA DISPARAR', True, (255, 255, 0))
        screen.blit(texte_poder, (15, 65))


# Loop principal
# ----------------------------------------------------------------------


estado = 'inicio'

while True:
    dt = min(clock.tick(FPS), 40)

    for ev in event.get():
        if ev.type == QUIT or (ev.type == KEYDOWN and ev.key == K_ESCAPE):
            quit()
            sys.exit()

        if ev.type == KEYDOWN and ev.key == K_RETURN:
            if estado == 'inicio':
                estado = 'jogando'
            elif estado == 'final':
                quit()
                sys.exit()

    if estado == 'inicio':
        screen.blit(fundo_rio, (0, 0))
        painel('Mario no Rio', ['Setas para mover e pular   |   F para chutar',
                               'Chegue à bandeira brasileira', 'Enter para jogar'])
        display.flip()
        continue
    if estado == 'final':
        # Seu colega pode substituir este painel pela tela final.
        painel('Chegou à bandeira!', [f'Moedas: {pieces}', 'Enter para sair'])
        display.flip()
        continue

    touches = key.get_pressed()
    en_mouvement = mover_mario(touches)
    atualizar_poder(touches)
    caiu = mario.top > altura_extra + ALTURA
    coletar_moedas()
    mover_inimigos()
    atualizar_projeteis()
    atingido = verificar_contato_com_inimigos()
    mort = caiu or atingido
    ativar_checkpoint()
    if mort:
        perder_vida()
    elif chegou_a_meta():
        estado = 'final'

    atualizar_camera(mort)
    desenhar_cenario()
    desenhar_meta()
    desenhar_moedas()
    desenhar_checkpoints()
    desenhar_bolas()
    desenhar_inimigos()
    desenhar_mario(en_mouvement)
    desenhar_placar()
    display.update()
