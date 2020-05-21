import DNALogic as l
import pygame as pg
import time, math
from random import randrange, choice
import matplotlib.pyplot as plt
import sys
args = sys.argv[1:]
pg.font.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (125, 125, 125)
DARK_GREEN = (22, 97, 42)
YELLOW = (252, 207, 3)

#DIM X, DIM Y, WIN X, WIN Y

DIM = [int(args[0]) if len(args) >= 1 else 1600, int(args[1]) if len(args) >= 2 else 1200]
WIN_SIZE = [int(args[2]) if len(args) >= 3 else 800, int(args[3]) if len(args) >= 4 else 600]

window = pg.display.set_mode(WIN_SIZE)

WAIT = 180

FPS = 60
MAXFPS = 500

mutationrate = 0.05

REPR = 1
SHOW = 1


def angle_between(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return math.degrees(math.atan2(yDiff, xDiff))+90


def next(curr, angle, speed):
    angleB = angle
    angleY = abs(90 - angle)
    angle = math.radians(angle)
    angleY = math.radians(angleY)
    dx = math.sin(angle) * speed
    dy = math.sin(angleY) * speed

    if angleB < 90:
        dy = -dy

    return curr[0] + dx, curr[1] + dy


def distance(pos1, pos2):
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]

    return math.sqrt((dx*dx + dy*dy))


def closest(entity, entities, food):
    hit = {}

    for e in entities:
        if e.id == entity.id:
            continue

        if not e in [x[0] for x in entity.friendly]:
            hit[e] = round(distance([e.x+e.width/2, e.y+e.height/2], [entity.x+entity.width/2, entity.y+entity.height/2]))

    for f in food:
        hit[f] = round(distance([f.x + f.width / 2, f.y + f.height / 2], [entity.x + entity.width / 2, entity.y + entity.height / 2]))

    he = None
    hv = 10000000000000000
    for key, val in hit.items():
        if val < hv:
            he = key
            hv = val

    angle = -1
    if he and hv <= entity.stats['radius']:
        angle = angle_between((entity.x+entity.width/2, entity.y+entity.height/2), (he.x+he.width/2, he.y+he.height/2))

    return he, hv, angle


def spawn(entities):
    dont = []
    for e in entities:
        dont.append([e.x, e.y, e.x+e.width, e.y+e.height])

    for _ in range(100):
        x, y = randrange(DIM[0]), randrange(DIM[1])

        if len(dont) == 0:
            return x, y

        for d in dont:
            if not (d[2] >= x >= d[0] and d[3] >= y >= d[1]):
                return x, y
    return None


class Food(pg.sprite.Sprite):
    def __init__(self, entities):
        self.x, self.y = spawn(entities)
        self.width, self.height = 25, 25
        if self.x + self.width > DIM[0]:
            self.x = DIM[0] - self.width
        if self.y + self.height > DIM[1]:
            self.y = DIM[1] - self.height
        self.power = 10 + randrange(10)

    def draw(self, win, offset):
        x = self.x + offset[0]
        y = self.y + offset[1]
        if x >= WIN_SIZE[0] or y >= WIN_SIZE[1]:
            return
        elif x < -self.width or y < -self.height:
            return
        pg.draw.rect(win, BLACK, (x, y, self.width, self.height))

    def __repr__(self):
        return '({}, {})'.format(self.x, self.y)


class Entity(pg.sprite.Sprite):
    def __init__(self, id, entities, parent=None, pos=None):
        self.pause = True
        self.id = id
        self.can = False
        if not pos:
            s = spawn(entities)
            if s:
                self.x, self.y = spawn(entities)
                self.ready = True
            else:
                print("Field is full")
                self.x = -100
                self.y = -100
                self.ready = False
        else:
            self.x = pos[0]
            self.y = pos[1]

        if parent:
            self.dna = l.generate(parent, mutationrate)
            self.x = parent.x
            self.y = parent.y + 50
            self.friendly = [[parent, WAIT]]
        else:
            self.dna = l.rand()
            self.friendly = []

        self.stats = l.stats(self.dna)

        self.width = 2 * self.stats['size']
        self.height = 2 * self.stats['size']

        self.health = self.stats['health']
        self.maxenergy = 100-self.stats['size']
        self.startat = self.maxenergy*0.6
        self.energy = self.maxenergy
        self.stats['radius'] += 2 * self.stats['size']
        self.angle = randrange(360)
        self.searching = True
        self.wall = False

    def draw(self, win, offset):
        x = self.x + offset[0]
        y = self.y + offset[1]
        if x >= WIN_SIZE[0] or y >= WIN_SIZE[1]:
            return
        elif x < -self.width or y < -self.height:
            return
        perc = self.health / self.stats['health']
        color = BLUE if self.can else RED if perc < 0.25 else YELLOW if perc < 0.60 else GREEN
        pg.draw.rect(win, color, (x, y, self.width, self.height))
        pg.draw.circle(win, RED if not self.searching else GREEN, (round(x+self.width/2), round(y+self.height/2)), self.stats['radius'], 1)
        pg.draw.line(win, RED if not self.searching else GREEN, (round(x+self.width/2), round(y+self.height/2)), (next((round(x+self.width/2), round(y+self.height/2)), self.angle, self.stats['radius'])))
        if self.health < 100:
            color = RED if perc < 0.25 else YELLOW if perc < 0.60 else GREEN
            pg.draw.rect(win, color, (x, y, self.width, self.height), 2)

    def move(self, e, f):
        enemy, distance, angle = closest(self, e, f)

        towards = False
        if enemy.__class__ == Food:
            towards = True
        elif self.health / self.stats['health'] >= 0.8:
            towards = True

        if enemy and distance <= self.stats['radius']:
            self.searching = 0
            if towards:
                if not self.wall:
                    self.angle = angle
            else:
                self.angle = 360 - angle
            if self.energy > 0.2*self.maxenergy:
                self.x, self.y = next([self.x, self.y], self.angle, self.stats['speed']*(self.energy / self.maxenergy))
                self.energy -= 1
            else:
                self.pause = True
        else:
            self.searching = 1
            if self.energy > 0.2*self.maxenergy:
                self.angle += choice([-15, -10, 10, 15])
                self.x, self.y = next([self.x, self.y], self.angle, self.stats['speed']*(self.energy / self.maxenergy))
                self.energy -= 1
            else:
                self.pause = True
        if self.pause:
            self.energy += 2
            if self.energy > self.startat:
                self.pause = False

        self.x = round(self.x)
        self.y = round(self.y)

    def update(self, e, f):
        self.move(e, f)
        if self.x > DIM[0]-self.width:
            self.x = DIM[0]-self.width
            self.angle = 270
            self.wall = True
        elif self.x < 0:
            self.x = 0
            self.angle = 90
            self.wall = True
        if self.y > DIM[1]-self.height:
            self.y = DIM[1]-self.height
            self.angle = 0
            self.wall = True
        elif self.y < 0:
            self.y = 0
            self.angle = 180
            self.wall = True
        else:
            self.wall = False

        for e in self.friendly:
            e[1] -= 1
            if e[1] <= 0:
                self.friendly.remove(e)

    def __repr__(self):
        return '{} @ ({}, {})'.format(self.id, self.x, self.y)


def entity_collided(entities):
    for first in entities:
        for second in entities:
            if not first.id == second.id:
                if collided(first, second):
                    if not second in [x[0] for x in first.friendly] and not first in [x[0] for x in second.friendly]:
                        first.health -= second.stats['strength']
                        if first.health > 0:
                            second.health -= first.stats['strength']
                        else:
                            second.health += 10 * (second.health / second.stats['health'])
                        if second.health <= 0:
                            first.health += 10 * (first.health / first.stats['health'])


def collided(e1, e2):
    if (e2.x+e2.width >= e1.x >= e2.x and e2.y+e2.height >= e1.y >= e2.y) or (e2.x+e2.width >= e1.x+e1.width/2 >= e2.x and e2.y+e2.height >= e1.y+e1.height/2 >= e2.y):
        return True
    return False


def draw(objects, alive, avg, pos, i):
    global FPS
    window.fill(WHITE)

    for o in objects:
        o.draw(window, pos)

    font = pg.font.SysFont('comicsans', 25)
    fpstext = font.render(str(FPS), 0, BLACK)
    fpstextrect = fpstext.get_rect(topleft=(0, 0))
    window.blit(fpstext, fpstextrect)

    avg['alive'] = alive
    avg['iteration'] = i
    for x, [key, val] in enumerate(avg.items()):
        t = font.render('{}: {:>5}'.format(key.capitalize(), val), 0, BLACK)
        tr = t.get_rect(topright=(WIN_SIZE[0], x*15))
        window.blit(t, tr)

    pg.display.update()


def run():
    global FPS, WAIT, REPR, MAXFPS

    id = 0

    pos = [0, 0]
    maxpos = [[-(DIM[0]-WIN_SIZE[0])/2, (DIM[0]-WIN_SIZE[0])/2], [-(DIM[1]-WIN_SIZE[1])/2, (DIM[1]-WIN_SIZE[1])/2]]
    off = 200

    spawnrate = 0.5
    maxspawn = 50
    minspawn = 10

    entities = []
    entities.append(Entity(id, entities))
    id += 1
    entities.append(Entity(id, entities))
    id += 1

    food = []
    food.append(Food(entities))

    clock = pg.time.Clock()

    standards = {}
    standards['health'] = round(sum([x.stats['health'] for x in entities]) / len(entities))
    standards['speed'] = round(sum([x.stats['speed'] for x in entities]) / len(entities))
    standards['strength'] = round(sum([x.stats['strength'] for x in entities]) / len(entities))
    standards['size'] = round(sum([x.stats['size'] for x in entities]) / len(entities))
    standards['radius'] = round(sum([x.stats['radius'] for x in entities]) / len(entities))

    gens = [['Health'], ['Speed'], ['Strength'], ['Size'], ['Radius'], ['Alive']]

    iteration = 0
    start = time.time()
    i = 0
    isquit = False
    do = True
    while do:
        clock.tick(FPS)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                isquit = True
                do = False

        if not do:
            break

        if pg.mouse.get_focused():
            mpos = pg.mouse.get_pos()
            if mpos[0] >= WIN_SIZE[0]-off:
                pos[0] -= 5
            elif mpos[0] <= off:
                pos[0] += 5
            if mpos[1] >= WIN_SIZE[1]-off:
                pos[1] -= 5
            elif mpos[1] <= off:
                pos[1] += 5

        if pos[0] >= maxpos[0][1]:
            pos[0] = maxpos[0][1]
        elif pos[0] <= maxpos[0][0]:
            pos[0] = maxpos[0][0]
        if pos[1] >= maxpos[1][1]:
            pos[1] = maxpos[1][1]
        elif pos[1] <= maxpos[1][0]:
            pos[1] = maxpos[1][0]

        keys = pg.key.get_pressed()

        if keys[pg.K_UP]:
            if FPS < MAXFPS:
                FPS += 1
        elif keys[pg.K_DOWN]:
            if FPS > 20:
                FPS -= 1

        draw(entities+food, len(entities), standards, pos, iteration)

        for entity in entities:
            entity.update(entities, food)

        entity_collided(entities)

        for en in entities:
            for f in food:
                if collided(en, f):
                    if en.health == en.stats['health']:
                        if not en.can:
                            en.can = True
                        else:
                            if REPR:
                                en.energy -= 0.1*en.maxenergy
                                new = Entity(id, entities, parent=en)
                                en.friendly.append([new, WAIT])
                                entities.append(new)
                                en.can = False
                                id += 1
                    else:
                        if en.health + f.power >= en.stats['health']:
                            en.health = en.stats['health']
                        else:
                            en.health += f.power
                    food.remove(f)

        if len(food) < maxspawn:
            if l.gamble(spawnrate):
                food.append(Food(entities))

        for e in entities:
            if e.health <= 0:
                entities.remove(e)

        if len(entities) == 0:
            print('Error 0 entities')
            do = False

        i += 1
        if i == FPS:
            i = 0
            print('Time: {}s'.format(round(time.time() - start, 3)))
            standards = {}
            standards['health'] = round(sum([x.stats['health'] for x in entities]) / len(entities))
            standards['speed'] = round(sum([x.stats['speed'] for x in entities]) / len(entities))
            standards['strength'] = round(sum([x.stats['strength'] for x in entities]) / len(entities))
            standards['size'] = round(sum([x.stats['size'] for x in entities]) / len(entities))
            standards['radius'] = round(sum([x.stats['radius'] for x in entities]) / len(entities))
            gens[0].append(standards['health'])
            gens[1].append(standards['speed'])
            gens[2].append(standards['strength'])
            gens[3].append(standards['size'])
            gens[4].append(standards['radius'])
            gens[5].append(len(entities))
            if maxspawn > minspawn:
                maxspawn -= 1
            iteration += 1
            start = time.time()

    if not isquit:
        pg.quit()
    return gens


def avg(data):
    out = []
    for x, _ in enumerate(data, start=1):
        out.append(sum(data[:x]) / x)
    return out


if __name__ == '__main__':
    a = time.time()
    data = run()
    print('Simulation took {}s'.format(round(time.time()-a, 2)))

    if SHOW:
        i = 1
        for d in data:
            d2 = avg(d[1:])
            plt.figure(i)
            plt.plot(d[1:], color='blue', label='Raw')
            plt.plot(d2, color='red', label='Averaged')
            plt.legend(['Natural Simulation'], loc='upper right')
            plt.title('Natural Simulation')
            plt.ylabel(d[0])
            plt.xlabel('Iteration by FPS')
            i += 1
        plt.show()

    quit()

