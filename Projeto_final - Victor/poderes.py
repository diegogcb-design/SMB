
import pygame
import os

# Configuracoes da bola de futebol
TAMANHO_FRAME = 64
NUM_FRAMES = 8
VELOCIDADE_BOLA = 12


def carregar_bola():
    # Carrega o spritesheet da bola de futebol
    pasta = os.path.dirname(__file__)

    caminho = os.path.join(
        pasta,
        "Sprite de balón de fútbol retro en píxeles.png"
    )

    planche = pygame.image.load(caminho).convert_alpha()

    print("Tamanho spritesheet:", planche.get_size())

    frames = []

    # Divide o spritesheet em 8 imagens
    largura_frame = planche.get_width() // NUM_FRAMES
    altura_frame = planche.get_height()

    for i in range(NUM_FRAMES):
        area = pygame.Rect(
            i * largura_frame,
            0,
            largura_frame,
            altura_frame
        )

        frame = planche.subsurface(area).copy()

        # Ajusta cada frame para 64x64
        frame = pygame.transform.scale(
            frame,
            (TAMANHO_FRAME, TAMANHO_FRAME)
        )

        frames.append(frame)

    return frames


class BolaColecionavel:

    def __init__(self, x, y, frames):

        self.frames = frames

        # A bola comeca dentro do bloco dourado
        self.rect = pygame.Rect(x, y, 64, 64)

        # Guarda a posicao inicial
        self.y_inicial = y

        # A bola deve subir 64 pixels
        self.y_final = y - 64

        self.coletada = False
        self.saindo = True

    def atualizar(self, mario):

        if self.coletada:
            return False

        # Faz a bola sair do bloco
        if self.saindo:

            self.rect.y -= 2

            if self.rect.y <= self.y_final:
                self.rect.y = self.y_final
                self.saindo = False

        # Mario pode coletar a bola depois que ela saiu
        elif self.rect.colliderect(mario):

            self.coletada = True

            return True

        return False

    def desenhar(self, tela, camera_x):

        if self.coletada:
            return

        # Escolhe o frame da animacao
        indice = (
            pygame.time.get_ticks() // 120
        ) % len(self.frames)

        imagem = self.frames[indice]

        x_tela = int(self.rect.x - camera_x)

        # Durante a saida, so mostra a parte fora do bloco
        if self.saindo:

            altura_visivel = self.y_inicial - self.rect.y

            if altura_visivel > 0:

                area = pygame.Rect(
                    0,
                    0,
                    64,
                    altura_visivel
                )

                tela.blit(
                    imagem,
                    (x_tela, self.rect.y),
                    area
                )

        else:

            # Bola completamente fora do bloco
            tela.blit(
                imagem,
                (x_tela, self.rect.y)
            )


class ProjetilBola:

    def __init__(self, x, y, direcao, frames):

        # O projetil tem metade do tamanho
        self.frames = [
            pygame.transform.scale(
                frame,
                (32, 32)
            )
            for frame in frames
        ]

        self.rect = pygame.Rect(
            x,
            y,
            32,
            32
        )

        self.direcao = direcao
        self.ativo = True

        # Distancia percorrida pela bola
        self.distancia = 0

    def atualizar(self, colisores, largura_mapa):

        if not self.ativo:
            return

        movimento = VELOCIDADE_BOLA * self.direcao

        # Move o projetil
        self.rect.x += movimento

        self.distancia += movimento

        # Verifica colisao com os blocos
        for bloco in colisores:

            if self.rect.colliderect(bloco):

                self.ativo = False
                break

        # Remove a bola se sair do mapa
        if (
            self.rect.right < 0
            or self.rect.left > largura_mapa
        ):

            self.ativo = False

    def desenhar(self, tela, camera_x):

        if not self.ativo:
            return

        # Animacao de rotacao
        indice = (
            abs(self.distancia) // 12
        ) % len(self.frames)

        imagem = self.frames[indice]

        # Inverte a imagem quando vai para a esquerda
        if self.direcao < 0:

            imagem = pygame.transform.flip(
                imagem,
                True,
                False
            )

        tela.blit(
            imagem,
            (
                int(self.rect.x - camera_x),
                self.rect.y
            )
        )
