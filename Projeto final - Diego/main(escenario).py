
import pygame
import sys
import os
import json
from pygame.locals import QUIT

pygame.init()

# Configurações da janela
LARGURA = 900
ALTURA = 600
TILE_SIZE = 64
FPS = 60
VELOCIDADE_CAMERA = 0.45  # Pixels por milissegundo

screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('SMB - Cenario e Camera')
clock = pygame.time.Clock()

# Caminhos dos arquivos
pasta = os.path.dirname(__file__)
pasta_assets = os.path.join(pasta, 'PixelPlatformerTileset')

# Carrega as imagens do pacote
tileset = pygame.image.load(
    os.path.join(pasta_assets, 'tileset_16x16.png')
).convert_alpha()

props = pygame.image.load(
    os.path.join(pasta_assets, 'props_sheet.png')
).convert_alpha()

# Carrega o arquivo JSON com as coordenadas dos sprites
with open(os.path.join(pasta_assets, 'sprite_index.json'), 'r', encoding='utf-8') as arquivo:
    indice = json.load(arquivo)

# Cria o dicionário com todas as imagens
sprites = {}

for nome, dados in indice.items():

    # Escolhe de qual imagem vamos recortar o sprite
    origem = props if dados.get('sheet') == 'props_sheet.png' else tileset

    # Define a área que será recortada
    area = pygame.Rect(
        dados['x'],
        dados['y'],
        dados['w'],
        dados['h']
    )

    # Cria uma superfície transparente
    imagem = pygame.Surface(
        (dados['w'], dados['h']),
        pygame.SRCALPHA
    )

    # Copia a imagem selecionada
    imagem.blit(origem, (0, 0), area)

    # Amplia a imagem 4 vezes e guarda no dicionário
    sprites[nome] = pygame.transform.scale(
        imagem,
        (dados['w'] * 4, dados['h'] * 4)
    )


# CARREGAMENTO DO MAPA

# Lê o mapa a partir do arquivo de texto
with open(os.path.join(pasta, 'levels', 'level_1.txt'), 'r', encoding='utf-8') as arquivo:
    mapa = []

    for linha in arquivo:
        if linha.strip():
            linha = linha.rstrip('\n')
            mapa.append(linha)


# LETRAS DO MAPA

# Cada letra representa uma imagem do pacote
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
    'H': 'grass_tuft',           # Vegetação pequena
    'P': 'spikes',               # Espinhos
    'A': 'tree',                 # Árvore
    'N': 'pine_tree',            # Pinheiro
    'V': 'bush',                 # Arbusto
    'O': 'cloud',                # Nuvem
    'M': 'mushroom',             # Cogumelo
    'E': 'star'                  # Estrela
}

# Blocos que terão colisão com o jogador
blocos_solidos = ['G', 'T', 'B', 'Q', 'U', 'S', 'W']

# Cria os retângulos de colisão
# O colega poderá utilizar esses retângulos para o personagem
colisores = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        if mapa[i][j] in blocos_solidos:
            colisores.append(
                pygame.Rect(
                    j * TILE_SIZE,
                    i * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE
                )
            )


# CÂMERA

# Calcula a largura total do mapa em pixels
largura_mapa = max(len(linha) for linha in mapa) * TILE_SIZE

# Posição inicial da câmera
camera_x = 0.0


# MOEDAS

# Guarda as posições das moedas
moedas = []

for i in range(len(mapa)):
    for j in range(len(mapa[i])):

        if mapa[i][j] == 'C':
            moedas.append(
                (j * TILE_SIZE + 16, i * TILE_SIZE + 16)
            )


# LOOP PRINCIPAL DO JOGO

while True:

    # Controla o tempo entre os frames
    dt = min(clock.tick(FPS), 40)

    # Verifica se o jogador fechou a janela
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # CONTROLE TEMPORÁRIO DA CÂMERA

    # Verifica quais teclas estão pressionadas
    keys = pygame.key.get_pressed()

    # Move a câmera para a direita
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        camera_x += VELOCIDADE_CAMERA * dt

    # Move a câmera para a esquerda
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        camera_x -= VELOCIDADE_CAMERA * dt

    # Impede que a câmera ultrapasse os limites do mapa
    camera_x = max(
        0,
        min(camera_x, max(0, largura_mapa - LARGURA))
    )

    # Preenche o fundo com a cor do céu
    screen.fill((120, 180, 220))


    # DESENHO DO MAPA

    # Percorre todas as linhas do mapa
    for i in range(len(mapa)):

        # Percorre todas as colunas da linha
        for j in range(len(mapa[i])):

            # Obtém a letra da posição atual
            letra = mapa[i][j]

            # Verifica se a letra existe no dicionário
            if letra in tiles:

                # Busca a imagem correspondente
                imagem = sprites[tiles[letra]]

                # Calcula a posição horizontal considerando a câmera
                x_tela = int(j * TILE_SIZE - camera_x)

                # Ajusta a altura dos objetos maiores que um bloco
                # Assim as árvores crescem para cima
                y_tela = (i + 1) * TILE_SIZE - imagem.get_height()
                # Ajusta a posição do arbusto para ficar no chão
                if letra == 'V':
                    y_tela += 8
                    
                # Obtém a largura da imagem
                largura_imagem = imagem.get_width()

                # Verifica se a imagem está visível na tela
                if -largura_imagem < x_tela < LARGURA:

                    # Desenha a imagem na posição calculada
                    screen.blit(imagem, (x_tela, y_tela))


    # DESENHO E ANIMAÇÃO DAS MOEDAS

    # Alterna entre as quatro imagens da moeda
    # A imagem muda a cada 150 milissegundos
    frame_moeda = (pygame.time.get_ticks() // 150) % 4

    # Cria o nome da imagem atual
    nome_moeda = 'coin_' + str(frame_moeda)

    # Verifica se a imagem existe
    if nome_moeda in sprites:

        # Percorre todas as moedas do mapa
        for x, y in moedas:

            # Calcula a posição horizontal na tela
            x_tela = int(x - camera_x)

            # Verifica se a moeda está visível
            if -TILE_SIZE < x_tela < LARGURA:

                # Desenha a moeda animada
                screen.blit(
                    sprites[nome_moeda],
                    (x_tela, y)
                )

    # Atualiza a imagem mostrada na janela
    pygame.display.update()
