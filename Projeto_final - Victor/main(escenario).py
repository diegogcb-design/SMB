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
VELOCIDADE_CAMERA = 0.45  # pixels por milissegundo (teste sem jogador)

screen = display.set_mode((LARGURA, ALTURA))
display.set_caption('SMB - Cenario e Camera')
clock = time.Clock()

pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

# Imagens e indice do pacote
# Os sprites sao 16x16, ampliados 4 vezes para 64x64.
tileset = image.load(os.path.join(pasta_assets, 'tileset_16x16.png')).convert_alpha()
props = image.load(os.path.join(pasta_assets, 'props_sheet.png')).convert_alpha()

with open(os.path.join(pasta_assets, 'sprite_index.json'), 'r', encoding='utf-8') as arquivo:
    indice = json.load(arquivo) #coordenadas do JSON -> diccionario Python

sprites = {} #diccionario vazio
for nome, dados in indice.items():
    origem = props if dados.get('sheet') == 'props_sheet.png' else tileset #escolhe de qual png tiramos o sprite
    area = Rect(dados['x'], dados['y'], dados['w'], dados['h']) #selecciona o rectangulo a ser recortado con esas coordenadas
    imagem = Surface((dados['w'], dados['h']), SRCALPHA) #cria uma superfície vazia e transparente
    imagem.blit(origem, (0, 0), area) #copia a parte seleccionada da imagen original para a nova superificie
    sprites[nome] = transform.scale(imagem, (dados['w'] * 4, dados['h'] * 4)) #agranda a imagen e guarda no diccionario com seu nome

# Mapa em arquivo de texto
with open(os.path.join(pasta, 'levels', 'level_1.txt'), 'r', encoding='utf-8') as arquivo:
    mapa = [linha.rstrip('\n') for linha in arquivo if linha.strip()]

# Letras do mapa e sprites correspondentes
tiles = {
    'G': 'grass_t',
    'T': 'grass_m',
    'B': 'bricks',
    'Q': 'question_block'
}
blocos_solidos = ['G', 'T', 'B', 'Q']

# Colisoes do cenario, para o colega usar depois
colisores = []
for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] in blocos_solidos:
            colisores.append(Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE))


largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE
camera_x = 0.0

# Posicoes das moedas no mapa (sem coleta nesta versao)
moedas = []
for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == 'C':
            moedas.append((j * TILE_SIZE + 16, i * TILE_SIZE + 16)) #centrar a moeda

#print("Columnas:", len(mapa[0]))
#print("Ancho del mapa:", largura_mapa)
#print("Posición cámara:", camera_x)

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

#####################################################################################################

while True:
    dt = min(clock.tick(FPS), 40)   

    for ev in event.get():          
        if ev.type == QUIT:         
            quit()                  
            sys.exit()              

    touches = key.get_pressed()     

    #Deplacement gauche / droite
    en_mouvement = False            # par defaut, Mario ne bouge pas
    if touches[K_LEFT]:             
        mario.x -= 5               
        regarde_a_gauche = True    
        en_mouvement = True        
    if touches[K_RIGHT]:           
        mario.x += 5               
        regarde_a_gauche = False    
        en_mouvement = True         
    for bloc in colisores:          # on regarde chaque bloc solide du mapa
        if mario.colliderect(bloc): # si Mario est rentre dans ce bloc
            if regarde_a_gauche:            # il allait a gauche
                mario.left = bloc.right     
            else:                           # il allait a droite
                mario.right = bloc.left     
    mario.left = max(0, min(mario.left, largura_mapa - mario.width))  # empeche Mario de sortir du mapa

    #Saut et gravite
    if touches[K_UP] and au_sol:    
        vitesse_y = -18            
    vitesse_y += 1                  # gravite : a chaque image il est tire un peu plus vers le bas
    mario.y += vitesse_y            
    au_sol = False                  
    for bloc in colisores:          # on regarde chaque bloc solide
        if mario.colliderect(bloc): # si Mario touche ce bloc
            if vitesse_y > 0:               # il tombait
                mario.bottom = bloc.top     # on le pose sur le dessus du bloc
                au_sol = True               # il est au sol, il pourra sauter
            else:                           # il montait
                mario.top = bloc.bottom     # sa tete tape le dessous du bloc
            vitesse_y = 0                   # dans les 2 cas, il s'arrete verticalement

    #Chute dans un trou
    if mario.top > ALTURA:          # Mario est sorti par le bas de l'ecran
        mario.midbottom = DEPART    # on le remet au point de depart
        vitesse_y = 0               # et on remet sa vitesse a zero

    #Camera
    camera_x = mario.centerx - LARGURA // 2                           # la camera place Mario au milieu de l'ecran
    camera_x = max(0, min(camera_x, max(0, largura_mapa - LARGURA)))  # sans depasser le debut ni la fin du mapa

    screen.fill((120, 180, 220))

    #Dessin du mapa
    for i in range(len(mapa)):                 
        for j in range(len(mapa[i])):           
            letra = mapa[i][j]                  
            if letra in tiles:                  # si c'est un bloc a dessiner
                x_tela = int(j * TILE_SIZE - camera_x)   # position a l'ecran = position dans le mapa - camera
                if -TILE_SIZE < x_tela < LARGURA:        # on dessine seulement si c'est visible
                    screen.blit(sprites[tiles[letra]], (x_tela, i * TILE_SIZE))  # dessine le bloc

    #Dessin des pieces
    frame_moeda = (time.get_ticks() // 150) % 4    # change d'image toutes les 150 ms (0,1,2,3,0...)
    nome_moeda = 'coin_' + str(frame_moeda)        # nom de l'image : coin_0, coin_1...
    if nome_moeda in sprites:                      # si cette image existe
        for x, y in moedas:                        # pour chaque piece
            x_tela = int(x - camera_x)             # position a l'ecran
            if -TILE_SIZE < x_tela < LARGURA:      # si elle est visible
                screen.blit(sprites[nome_moeda], (x_tela, y))  # on la dessine

    #Choix de l'image de Mario
    if not au_sol:                                          # s'il est en l'air
        sprite = images[SAUT if vitesse_y < 0 else CHUTE]   # image de saut s'il monte, de chute s'il descend
    elif en_mouvement:                                      # s'il marche
        compteur += 1                                       # on avance le compteur
        sprite = images[COURSE[compteur // 6 % len(COURSE)]]  # change d'image de course toutes les 6 images
    else:                                                   # s'il est immobile
        compteur = 0                                        # on remet le compteur a zero
        sprite = images[REPOS]                              # image de repos

    screen.blit(transform.flip(sprite, regarde_a_gauche, False), (mario.x - camera_x, mario.y))  # dessine Mario (retourne s'il regarde a gauche)
    display.update()    # affiche a l'ecran tout ce qu'on vient de dessiner
