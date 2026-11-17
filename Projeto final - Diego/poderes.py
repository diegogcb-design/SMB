
import pygame
import os

# Configuracoes das bolas
TAMANHO_FRAME = 64
NUM_FRAMES = 8
VELOCIDADE_BOLA = 12


def carregar_bola():
    # Carrega a planilha de sprites da bola
    pasta = os.path.dirname(__file__)
    caminho = os.path.join(pasta,"Sprite de balón de fútbol retro en píxeles.png")

    planche = pygame.image.load(caminho).convert_alpha()
    frames = []

    # Cada imagem tem 64x64 pixels
    for i in range(NUM_FRAMES):
        area = pygame.Rect(i * TAMANHO_FRAME, 0,
                           TAMANHO_FRAME, TAMANHO_FRAME)

        frame = planche.subsurface(area).copy()
        frames.append(frame)

    return frames


class BolaColecionavel:
    def __init__(self, x, y, frames):
        self.frames = frames

        # A bola comeca dentro do bloco
        self.rect = pygame.Rect(x, y, 64, 64)

        # Posicao final: em cima do bloco
        self.y_final = y - 64

        self.coletada = False
        self.saindo = True

    def atualizar(self, mario):
        if self.coletada:
            return False

        # Animacao da bola saindo do bloco
        if self.saindo:
            self.rect.y -= 4

            if self.rect.y <= self.y_final:
                self.rect.y = self.y_final
                self.saindo = False

        # Mario so pode pegar depois que a bola saiu
        elif self.rect.colliderect(mario):
            self.coletada = True
            return True

        return False

    def desenhar(self, tela, camera_x):
        if not self.coletada:
            indice = (
                pygame.time.get_ticks() // 120
            ) % len(self.frames)

            imagem = self.frames[indice]

            tela.blit(imagem, (
                int(self.rect.x - camera_x),
                self.rect.y
            ))


class ProjetilBola:
    def __init__(self, x, y, direcao, frames):
        # O projetil e menor que a bola colecionavel
        self.frames = [
            pygame.transform.scale(frame, (32, 32))
            for frame in frames
        ]

        self.rect = pygame.Rect(x, y, 32, 32)
        self.direcao = direcao
        self.ativo = True

        # Guarda a posicao para animar a rotacao
        self.distancia = 0

    def atualizar(self, colisores, largura_mapa):
        if not self.ativo:
            return

        # Movimento horizontal da bola
        movimento = VELOCIDADE_BOLA * self.direcao
        self.rect.x += movimento
        self.distancia += movimento

        # Colisao com os blocos do cenario
        for bloco in colisores:
            if self.rect.colliderect(bloco):
                self.ativo = False
                break

        # Remove a bola fora dos limites
        if self.rect.right < 0 or self.rect.left > largura_mapa:
            self.ativo = False

    def desenhar(self, tela, camera_x):
        if not self.ativo:
            return

        # A rotacao depende da distancia percorrida
        indice = (
            abs(self.distancia) // 12
        ) % len(self.frames)

        imagem = self.frames[indice]

        # Inverte a animacao ao disparar para a esquerda
        if self.direcao < 0:
            imagem = pygame.transform.flip(imagem, True, False)

        tela.blit(imagem, (
            int(self.rect.x - camera_x),
            self.rect.y
        ))
