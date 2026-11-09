from pygame import *

init()
screen = display.set_mode((800,600))

clock = time.Clock()
centre = [100, 100]

running = True
while running:
    clock.tick(60)
    touches = key.get_pressed()

    for ev in event.get():
        if ev.type == QUIT:
            running = False
        if ev.type == MOUSEMOTION:
             centre[0], centre[1] = ev.pos
    if touches[K_LEFT]:
        centre[0]-=5
    if touches[K_RIGHT]:
        centre[0]+=5
    if touches[K_UP]:
        centre[1]-=5
    if touches[K_DOWN]:
        centre[1]+=5
    if centre[0]<= 100:
        centre[0] = 100
    if centre[0]>= 700:
        centre[0] = 700
    if centre[1]<= 100:
        centre[1] = 100
    if centre[1]>= 500:
        centre[1] = 500

    display.update()