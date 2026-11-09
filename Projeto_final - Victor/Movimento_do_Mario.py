from pygame import *
import os

LARGEUR, HAUTEUR = 800, 600
SOL = 500          # hauteur du sol (les pieds du mario)
CASE = 32          # chaque image de la planche fait 32x32
ECHELLE = 2        # on agrandit les images (32 x 2 = 64 pixels a l'ecran)
FORCE_SAUT = -18

DEBUT = 8
REPOS = DEBUT
COURSE = [DEBUT + 1, DEBUT + 2, DEBUT + 3, DEBUT + 2]
SAUT = DEBUT + 4
CHUTE = DEBUT + 5

init()
screen = display.set_mode((LARGEUR, HAUTEUR))
clock = time.Clock()


def charger_planche(nom):
    dossier = os.path.dirname(os.path.abspath(__file__))
    planche = image.load(os.path.join(dossier, nom)).convert_alpha()
    images = []
    for i in range(planche.get_width() // CASE):
        case = planche.subsurface(Rect(i * CASE, 0, CASE, CASE))
        images.append(transform.scale(case, (CASE * ECHELLE, CASE * ECHELLE)))
    return images

images = charger_planche("Perso.png")

mario = images[REPOS].get_rect(midbottom=(100, SOL))
vitesse_y = 0
au_sol = True
regarde_a_gauche = False
compteur = 0

running = True
while running:
    clock.tick(60)
    for ev in event.get():
        if ev.type == QUIT:
            running = False
    touches = key.get_pressed()

    en_mouvement = False
    if touches[K_LEFT]:
        mario.x -= 5
        regarde_a_gauche = True
        en_mouvement = True
    if touches[K_RIGHT]:
        mario.x += 5
        regarde_a_gauche = False
        en_mouvement = True
    mario.clamp_ip(Rect(0, -HAUTEUR, LARGEUR, 2 * HAUTEUR))

    # Saut
    if touches[K_UP] and au_sol:
        vitesse_y = FORCE_SAUT
        au_sol = False

    # Gravite et atterrissage
    vitesse_y += 1
    mario.y += vitesse_y
    if mario.bottom >= SOL:
        mario.bottom = SOL
        vitesse_y = 0
        au_sol = True

    # Choix de l'image
    if not au_sol:
        sprite = images[SAUT if vitesse_y < 0 else CHUTE]
    elif en_mouvement:
        compteur += 1
        sprite = images[COURSE[compteur // 6 % len(COURSE)]]
    else:
        compteur = 0
        sprite = images[REPOS]

    # Dessin
    screen.fill((120, 190, 255))
    draw.rect(screen, (90, 160, 70), (0, SOL, LARGEUR, HAUTEUR - SOL))
    screen.blit(transform.flip(sprite, regarde_a_gauche, False), mario)
    display.update()

quit()
