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

screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('SMB - Super Mario Brasileiro')
clock = pygame.time.Clock()
fonte = pygame.font.Font(None, 36)

pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

# Sprites originais de 16x16. Ampliamos 4 vezes ao desenhar.
tileset = pygame.image.load(os.path.join(pasta_assets, 'tileset_16x16.png')).convert_alpha()
props = pygame.image.load(os.path.join(pasta_assets, 'props_sheet.png')).convert_alpha()

with open(os.path.join(pasta_assets, 'sprite_index.json'), 'r', encoding='utf-8') as arquivo:
    indice = json.load(arquivo)

# Dicionario de imagens cortadas usando o indice do proprio pack.
sprites = {}
for nome, dados in indice.items():
    imagem_origem = props if dados.get('sheet') == 'props_sheet.png' else tileset
    area = pygame.Rect(dados['x'], dados['y'], dados['w'], dados['h'])
    imagem = pygame.Surface((dados['w'], dados['h']), pygame.SRCALPHA)
    imagem.blit(imagem_origem, (0, 0), area)
    sprites[nome] = pygame.transform.scale(imagem, (dados['w'] * 4, dados['h'] * 4))

with open(os.path.join(pasta, 'levels', 'level_1.txt'), 'r', encoding='utf-8') as arquivo:
    mapa = [linha.rstrip('\n') for linha in arquivo if linha.strip()]

# G = grama, T = terra, B = tijolo, Q = bloco de pergunta, C = moeda.
tiles = {
    'G': 'grass_t',
    'T': 'grass_m',
    'B': 'bricks',
    'Q': 'question_block'
}
blocos_solidos = ['G', 'T', 'B', 'Q']

# Cada moeda tem uma posicao no mundo.
moedas = []
for i in range(len(mapa)):
    for j in range(len(mapa[i])):
        if mapa[i][j] == 'C':
            moedas.append(pygame.Rect(j * TILE_SIZE + 16, i * TILE_SIZE + 16, 32, 32))

pos_x = 100.0
pos_y = 100.0
largura_jogador = 40
altura_jogador = 55
velocidade = 0.25
vel_y = 0.0
gravidade = 0.0015
forca_pulo = -0.65
no_chao = False
direita = True
camera_x = 0
pontos = 0

# O personagem do pack tem dois desenhos: parado e correndo.
while True:
    dt = min(clock.tick(FPS), 40)

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    andando = False

    # Movimento horizontal
    old_pos_x = pos_x
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        pos_x += velocidade * dt
        direita = True
        andando = True
    elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
        pos_x -= velocidade * dt
        direita = False
        andando = True

    collider_jogador = pygame.Rect(int(pos_x), int(pos_y), largura_jogador, altura_jogador)

    # Colisao horizontal
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):
            if mapa[i][j] in blocos_solidos:
                collider_tile = pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if collider_jogador.colliderect(collider_tile):
                    pos_x = old_pos_x
                    collider_jogador.x = int(pos_x)

    # Pulo
    if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and no_chao:
        vel_y = forca_pulo
        no_chao = False

    # Gravidade
    old_pos_y = pos_y
    vel_y += gravidade * dt
    pos_y += vel_y * dt
    collider_jogador = pygame.Rect(int(pos_x), int(pos_y), largura_jogador, altura_jogador)
    no_chao = False

    # Colisao vertical
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):
            if mapa[i][j] in blocos_solidos:
                collider_tile = pygame.Rect(j * TILE_SIZE, i * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if collider_jogador.colliderect(collider_tile):
                    if vel_y > 0 and old_pos_y + altura_jogador <= collider_tile.top + 3:
                        pos_y = collider_tile.top - altura_jogador
                        vel_y = 0
                        no_chao = True
                    elif vel_y < 0 and old_pos_y >= collider_tile.bottom - 3:
                        pos_y = collider_tile.bottom
                        vel_y = 0
                    collider_jogador.y = int(pos_y)

    largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE
    pos_x = max(0, min(pos_x, largura_mapa - largura_jogador))
    collider_jogador = pygame.Rect(int(pos_x), int(pos_y), largura_jogador, altura_jogador)

    # Coletar moedas
    for moeda in moedas[:]:
        if collider_jogador.colliderect(moeda):
            moedas.remove(moeda)
            pontos += 1

    # Reiniciar se cair num buraco
    if pos_y > ALTURA + TILE_SIZE:
        pos_x = 100
        pos_y = 100
        vel_y = 0

    camera_x = max(0, min(pos_x - LARGURA / 2, max(0, largura_mapa - LARGURA)))

    # Fundo e mapa
    screen.fill((120, 180, 220))
    for i in range(len(mapa)):
        for j in range(len(mapa[i])):
            letra = mapa[i][j]
            if letra in tiles:
                screen.blit(sprites[tiles[letra]], (int(j * TILE_SIZE - camera_x), i * TILE_SIZE))

    # Moedas animadas
    frame_moeda = (pygame.time.get_ticks() // 150) % 4
    for moeda in moedas:
        imagem_moeda = sprites['coin_' + str(frame_moeda)]
        screen.blit(imagem_moeda, (int(moeda.x - camera_x - 16), moeda.y - 16))

    # Personagem: sprite original orientado para a direita (ajustar se necessario).
    imagem_jogador = sprites['hero_run'] if andando else sprites['hero_idle']
    if not direita:
        imagem_jogador = pygame.transform.flip(imagem_jogador, True, False)
    screen.blit(imagem_jogador, (int(pos_x - camera_x - 12), int(pos_y - 9)))

    texto = fonte.render('Moedas: ' + str(pontos), True, (255, 255, 255))
    screen.blit(texto, (20, 20))
    pygame.display.update()
