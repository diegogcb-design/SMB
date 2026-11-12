
from pygame import *
import sys
import os
import json
from pygame.locals import QUIT

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

# Mapa em arquivo de texto
with open(os.path.join(pasta, 'levels', 'level_1.txt'), 'r', encoding='utf-8') as arquivo:
    mapa = [linha.rstrip('\n') for linha in arquivo if linha.strip()]

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

# Blocos que possuem colisao com o personagem
blocos_solidos = ['G', 'T', 'B', 'Q', 'U', 'S', 'W']

# Colisoes do cenario
colisores = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] in blocos_solidos:
            colisores.append(
                Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )

largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE
camera_x = 0.0

# Posicoes das moedas no mapa (sem coleta nesta versao)
moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == 'C':
            moedas.append(
                (j * TILE_SIZE + 16, i * TILE_SIZE + 16)
            )  # Centraliza a moeda

#####################################################################################################
# Personnage

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

DEPART = (100, 8 * TILE_SIZE)                     
mario = images[REPOS].get_rect(midbottom=DEPART)  # rectangle de Mario (position + taille), pieds sur DEPART
vitesse_y = 0              
au_sol = False             
regarde_a_gauche = False   
compteur = 0               # compte les images pour faire defiler l'animation de course
pieces = 0                 # nombre de pieces ramassees
police = font.Font(None, 48)   # police pour afficher le compteur de pieces

#####################################################################################################

while True:
    dt = min(clock.tick(FPS), 40)

    for ev in event.get():
        if ev.type == QUIT:
            quit()
            sys.exit()

    touches = key.get_pressed()

    # Deplacement gauche / droite
    en_mouvement = False

    if touches[K_LEFT]:
        mario.x -= 7
        regarde_a_gauche = True
        en_mouvement = True

    if touches[K_RIGHT]:
        mario.x += 7
        regarde_a_gauche = False
        en_mouvement = True

    # Colisao horizontal com os blocos
    for bloc in colisores:
        if mario.colliderect(bloc):
            if regarde_a_gauche:
                mario.left = bloc.right
            else:
                mario.right = bloc.left

    #limite do mapa para Mario
    mario.left = max(0, min(mario.left, largura_mapa - mario.width))

    # Saut et gravite
    if touches[K_UP] and au_sol:
        vitesse_y = -22
    vitesse_y += 1
    mario.y += vitesse_y
    au_sol = False

    # Colisao vertical com os blocos
    for bloc in colisores:
        if mario.colliderect(bloc):
            if vitesse_y > 0:
                # Mario estava caindo
                mario.bottom = bloc.top
                au_sol = True
            else:
                # Mario estava subindo
                mario.top = bloc.bottom

            vitesse_y = 0

    # Chute dans un trou
    if mario.top > ALTURA:
        mario.midbottom = DEPART
        vitesse_y = 0
        pieces = 0
    
    # Ramassage des pieces
    for moeda in moedas[:]:                     # [:] = copie de la liste, pour pouvoir supprimer dedans
        x, y = moeda
        if mario.colliderect(Rect(x + 16, y + 16, 32, 32)):   # Mario touche la piece ?
            moedas.remove(moeda)                # la piece disparait
            pieces += 1                         # +1 au compteur

    # Camera
    # A camera acompanha Mario horizontalmente
    camera_x = mario.centerx - LARGURA // 2

    # Impede a camera de mostrar areas fora do mapa
    camera_x = max(
        0,
        min(camera_x, max(0, largura_mapa - LARGURA))
    )

    screen.fill((120, 180, 220))

    # Dessin du mapa
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):

            letra = mapa[i][j]

            if letra in tiles:
                # Busca a imagem correspondente a letra
                imagem = sprites[tiles[letra]]

                # Calcula a posicao horizontal considerando a camera
                x_tela = int(j * TILE_SIZE - camera_x)

                # Ajusta a altura dos objetos maiores que um bloco
                # Assim as arvores crescem para cima
                y_tela = (i + 1) * TILE_SIZE - imagem.get_height()

                # Ajusta o arbusto para ficar mais perto do chao
                if letra == 'V':
                    y_tela += 8

                # Verifica se a imagem esta visivel na tela
                largura_imagem = imagem.get_width()

                if -largura_imagem < x_tela < LARGURA:
                    screen.blit(imagem, (x_tela, y_tela))

    # Dessin des pieces
    # Alterna entre as quatro imagens da moeda
    frame_moeda = (time.get_ticks() // 150) % 4
    nome_moeda = 'coin_' + str(frame_moeda)

    if nome_moeda in sprites:
        for x, y in moedas:

            # Posicao horizontal da moeda na tela
            x_tela = int(x - camera_x)

            if -TILE_SIZE < x_tela < LARGURA:
                screen.blit(sprites[nome_moeda], (x_tela, y))

    #Choix de l'image de Mario
    if not au_sol:                                          
        sprite = images[SAUT if vitesse_y < 0 else CHUTE]   # image de saut s'il monte, de chute s'il descend
    elif en_mouvement:                                      # s'il marche
        compteur += 1                                       # on avance le compteur
        sprite = images[COURSE[compteur // 6 % len(COURSE)]]  # change d'image de course toutes les 6 images
    else:                                                   # s'il est immobile
        compteur = 0                                        
        sprite = images[REPOS]  

    # Dessine Mario e inverte a imagem quando olha para a esquerda
    screen.blit(
        transform.flip(sprite, regarde_a_gauche, False),
        (int(mario.x - camera_x), mario.y)
    )

    # Compteur de pieces en haut a gauche
    texte = police.render('Moedas : ' + str(pieces), True, (255, 255, 255))
    screen.blit(texte, (15, 15))

    # Atualiza a tela
    display.update()

