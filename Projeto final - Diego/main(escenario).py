import pygame
import sys
import os
import json
from pygame.locals import QUIT

pygame.init()

LARGURA = 900
ALTURA = 600
TILE_SIZE = 64
FPS = 60
VELOCIDADE_CAMERA = 0.45  # pixels por milissegundo (teste sem jogador)

screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('SMB - Cenario e Camera')
clock = pygame.time.Clock()

pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

# Imagens e indice do pacote
# Os sprites sao 16x16, ampliados 4 vezes para 64x64.
tileset = pygame.image.load(os.path.join(pasta_assets, 'tileset_16x16.png')).convert_alpha()
props = pygame.image.load(os.path.join(pasta_assets, 'props_sheet.png')).convert_alpha()

with open(os.path.join(pasta_assets, 'sprite_index.json'), 'r', encoding='utf-8') as arquivo:
    indice = json.load(arquivo) #coordenadas do JSON -> diccionario Python

sprites = {} #diccionario vazio
for nome, dados in indice.items():
    origem = props if dados.get('sheet') == 'props_sheet.png' else tileset #escolhe de qual png tiramos o sprite
    area = pygame.Rect(dados['x'], dados['y'], dados['w'], dados['h']) #selecciona o rectangulo a ser recortado con esas coordenadas
    imagem = pygame.Surface((dados['w'], dados['h']), pygame.SRCALPHA) #cria uma superfície vazia e transparente
    imagem.blit(origem, (0, 0), area) #copia a parte seleccionada da imagen original para a nova superificie
    sprites[nome] = pygame.transform.scale(imagem, (dados['w'] * 4, dados['h'] * 4)) #agranda a imagen e guarda no diccionario com seu nome

# Mapa em arquivo de texto
with open(os.path.join(pasta, 'levels', 'level_1.txt'), 'r', encoding='utf-8') as arquivo:
    mapa = []                    # Cria uma lista vazia
    for linha in arquivo:        # Percorre cada linha do arquivo
        if linha.strip():        # Verifica se a linha não está vazia
            linha = linha.rstrip('\n')  # Remove a quebra de linha do final
            mapa.append(linha)   # Adiciona a linha à lista mapa

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
            colisores.append(pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE))


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

while True:
    dt = min(clock.tick(FPS), 40)

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Controle TEMPORARIO da camera para testar o cenario sem jogador
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        camera_x += VELOCIDADE_CAMERA * dt
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        camera_x -= VELOCIDADE_CAMERA * dt

    # Limites da camera: nao mostrar area fora do mapa
    camera_x = max(0, min(camera_x, max(0, largura_mapa - LARGURA)))

    screen.fill((120, 180, 220))

    # Desenho do mapa
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):
            letra = mapa[i][j]
            if letra in tiles:
                x_tela = int(j * TILE_SIZE - camera_x)
                if -TILE_SIZE < x_tela < LARGURA:
                    screen.blit(sprites[tiles[letra]], (x_tela, i * TILE_SIZE))

    # Moedas: somente desenho; coleta sera integrada depois
    frame_moeda = (pygame.time.get_ticks() // 150) % 4
    nome_moeda = 'coin_' + str(frame_moeda)
    if nome_moeda in sprites:
        for x, y in moedas:
            x_tela = int(x - camera_x)
            if -TILE_SIZE < x_tela < LARGURA:
                screen.blit(sprites[nome_moeda], (x_tela, y))

    pygame.display.update()
