#!/usr/bin/env python

import os
import sys
import time

import pygame

import bulletml
import bulletml.bulletyaml
from bulletml.collision import collides_all

try:
    import yaml
except ImportError:
    yaml = None

try:
    import psyco
except ImportError:
    pass
else:
    psyco.full()

def main(argv):
    if not argv:
        raise SystemExit("Usage: %s filename ..." % sys.argv[0])

    pygame.display.init()
    screen = pygame.display.set_mode([600, 600], pygame.DOUBLEBUF)
    red = pygame.Surface([3, 3])
    red.fill([255, 0, 0])
    green = pygame.Surface([3, 3])
    green.fill([0, 255, 0])
    blue = pygame.Surface([3, 3])
    blue.fill([0, 0, 255])
    clock = pygame.time.Clock()
    target = bulletml.Bullet()

    bullets = dict(red=red, green=green, blue=blue)

    file_idx = 0

    while True:
        filename = argv[file_idx % len(argv)]
        doc = bulletml.BulletML.FromDocument(open(filename, "rU"))
        source = bulletml.Bullet.FromDocument(
            doc, x=150, y=150, target=target, rank=0.5)
                                         
        active = set([source])
        source.vanished = True
        print(filename)
        print("  Loaded %d top-level actions." % len(source.actions))
        frames = 0
        total = 0
        paused = False
        newfile = False

        pygame.display.set_caption(os.path.basename(filename))

        while active and not newfile:
            go = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise SystemExit
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused ^= True
                    elif event.key == pygame.K_RIGHT:
                        go = True
                    elif event.key == pygame.K_PAGEUP:
                        file_idx -= 1
                        newfile = True
                    elif event.key == pygame.K_PAGEDOWN:
                        file_idx += 1
                        newfile = True
                    elif event.key == pygame.K_RETURN:
                        newfile = True
                    elif event.key == pygame.K_s:
                        source = bulletml.Bullet.FromDocument(
                            doc, x=150, y=150, target=target, rank=0.5)
                        source.vanished = True
                        active.add(source)
            target.x, target.y = pygame.mouse.get_pos()
            target.x /= 2
            target.y /= 2
            target.y = 300 - target.y
            target.px = target.x
            target.py = target.y

            collides = False
            if not paused or go:
                lactive = list(active)
                start = time.time()
                count = len(active)
                for obj in lactive:
                    new = obj.step()
                    total += len(new)
                    active.update(new)
                    if (obj.finished
                        or not (-50 < obj.x < 350)
                        or not (-50 < obj.y < 350)):
                        active.remove(obj)
                if lactive:
                    collides = collides_all(target, lactive)
                elapsed = time.time() - start

                frames += 1
                if frames % 100 == 0:
                    print("  Processing: %04d: %d bullets, %d active." % (
                        frames, total, count))
                    if elapsed:
                        seconds_per_bullet = elapsed / count
                        bullets_per_second = count / elapsed
                        print("  %g seconds per bullet (120Hz max: %g)." % (
                            seconds_per_bullet, bullets_per_second / 120))

            screen.fill([0, 0, 64] if collides else [0, 0, 0] )
            for obj in active:
                try:
                    x, y = obj.x, obj.y
                except AttributeError:
                    pass
                else:
                    if not obj.vanished:
                        x *= 2
                        y *= 2
                        x -= 1
                        y -= 1
                        bullet = bullets.get(obj.appearance, red)
                        screen.blit(bullet, [x, 600 - y])
            clock.tick(60)
            pygame.display.flip()

        print("  Finished: %04d: %d bullets." % (frames, total))

if __name__ == "__main__":
    main(sys.argv[1:])
