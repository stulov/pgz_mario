import pgzrun
from pgzero.builtins import *
import pgzero.screen
from models import Animation, vec2

screen: pgzero.screen.Screen

tile_size = 16
tilemap = list(map(list, [
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "B                                B                                                   B",
    "B                                B                                                   B",
    "B                                B                                                   B",
    "B                                B                                                   B",
    "B                             BBBB                                                   B",
    "B                                B                                                   B",
    "BBB             c                Bc                                                  w",
    "B              BB                BB                                                  w",
    "B              BB                               e                                    w",
    "B    B  p      BB     e   BB                BccccccB              e e e     B        w",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
]))
H = len(tilemap)
W = len(tilemap[0])

HEIGHT = H*tile_size
WIDTH = 512


class Entity:
    def __init__(self, actor: Actor, velocity=vec2(0, 0)):
        self.actor = actor
        self.velocity = velocity

    def did_collide(self, wth=["B"]) -> bool:
        left_tile = int(self.actor.left/tile_size)
        right_tile = int(self.actor.right/tile_size)
        top_tile = int(self.actor.top/tile_size)
        bottom_tile = int(self.actor.bottom/tile_size)

        if left_tile < 0:
            left_tile = 0
        if right_tile > W-1:
            right_tile = W-1
        if top_tile < 0:
            top_tile = 0
        if bottom_tile > H-1:
            bottom_tile = H-1

        for i in range(top_tile, bottom_tile+1):
            for j in range(left_tile, right_tile+1):
                if tilemap[i][j] in wth:
                    return True
        return False

    def update(self, dt: float):
        old_pos = self.actor.pos
        self.actor.left += self.velocity.x*dt
        if self.did_collide():
            self.handle_x_collision(old_pos)

        g = 1000
        self.velocity.y += g*dt
        old_pos = self.actor.pos
        self.actor.top += self.velocity.y*dt
        if self.did_collide():
            self.handle_y_collision(old_pos)

    def handle_x_collision(self, old):
        self.actor.pos = old
        self.on_hit_side()

    def handle_y_collision(self, old):
        self.actor.pos = old
        if self.velocity.y > 0:
            self.on_landed()
        else:
            self.on_hit_head()

    def on_landed(self):
        self.velocity.y = 0

    def on_hit_head(self):
        self.velocity.y *= -1

    def on_hit_side(self):
        pass


class Player(Entity):

    idle = Animation(["mario/idle"], ["mario/idle-left"], fps=0)
    jump_anim = Animation(["mario/jump"], ["mario/jump-left"], fps=0)
    run = Animation([f"mario/run_{i+1}" for i in range(3)],
                    [f"mario/run_{i+1}-left" for i in range(3)], fps=12)

    def __init__(self, xy: tuple[float, float], speed: tuple[float, float]):
        super().__init__(actor=Actor(Player.idle.current, xy))
        self.alive = True
        self.speed = vec2(*speed)
        self.left = False
        self.is_jumping = False

    def run_right(self):
        self.velocity.x = self.speed.x

    def run_left(self):
        self.velocity.x = -self.speed.x

    def jump(self):
        if not self.is_jumping:
            self.velocity.y = -self.speed.y
            self.is_jumping = True
            if menu.sound_on:
                sounds.jump.play()

    def on_landed(self):
        super().on_landed()
        self.is_jumping = False

    def update(self, dt: float):
        super().update(dt)

        if self.velocity.x != 0:
            self.left = self.velocity.x < 0

        if self.is_jumping:
            self.actor.image = Player.jump_anim.flip(self.left).run(dt)
        elif self.velocity.x != 0:
            self.actor.image = Player.run.flip(self.left).run(dt)
        else:
            self.actor.image = Player.idle.flip(self.left).run(dt)

        self.velocity.x = 0


class Enemy(Entity):
    dead = "mario/enemy_dead"

    def __init__(self, xy: tuple[float, float]):
        self.walk = Animation(["mario/enemy_1", "mario/enemy_2"], None, fps=6)
        super().__init__(actor=Actor(self.walk.current, xy),
                         velocity=vec2(50, 0))
        self.alive = True

    def on_hit_side(self):
        self.velocity.x *= -1

    def update(self, dt: float):
        super().update(dt)

        if self.alive:
            self.actor.image = self.walk.run(dt)
        else:
            self.actor.image = Enemy.dead


class Coin(Entity):
    def __init__(self, xy: tuple[float, float]):
        self.anim = Animation([f"mario/coin_{i+1}" for i in range(4)],
                              None, fps=12)
        super().__init__(Actor(self.anim.current, xy,
                               anchor=("center", "top")))

    def update(self, dt):
        # super().update(dt)
        self.actor.image = self.anim.run(dt)


class Loop:
    def update(dt: float):
        pass

    def draw():
        pass


class Game(Loop):
    def __init__(self):
        self.player: Player = None
        self.enemies: list[Enemy] = []
        self.coins: set[Coin] = set()
        self.offset = vec2(0, 0)
        self.score = 0
        self.is_over = False

        for i in range(H):
            for j in range(W):
                xy = (j*tile_size, i*tile_size)
                tile = tilemap[i][j]
                if tile == "p":
                    self.player = Player(xy, speed=(100, 350))
                if tile == "e":
                    self.enemies.append(Enemy(xy))
                if tile == "c":
                    x, y = xy
                    self.coins.add(Coin((x+tile_size/2, y)))

    def update(self, dt):
        if keyboard.d:
            self.player.run_right()
        if keyboard.a:
            self.player.run_left()
        if keyboard.space:
            self.player.jump()

        did_kill = False
        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.alive and overlap(self.player.actor, enemy.actor):
                if self.player.velocity.y > 0:
                    enemy.velocity.x = 0
                    enemy.alive = False
                    did_kill = True
                    if menu.sound_on:
                        sounds.kick.play()
                else:
                    self.player.alive = False

        if did_kill:
            self.player.velocity.y = -150

        collected = set()
        for coin in self.coins:
            coin.update(dt)
            if overlap(self.player.actor, coin.actor):
                self.score += 1
                collected.add(coin)
                if menu.sound_on:
                    sounds.coin.play()
        self.coins -= collected

        self.player.update(dt)

        if self.player.actor.left > WIDTH/2:
            self.offset.x = self.player.actor.left - WIDTH/2
        if self.offset.x > W*tile_size - WIDTH:
            self.offset.x = W*tile_size - WIDTH

        if not self.player.alive or self.player.did_collide(["w"]):
            global state
            state = State.MENU
            self.is_over = True

    def draw(self):
        ox, oy = self.offset.xy
        ts = tile_size
        screen.fill((92, 148, 252))

        for i in range(H):
            for j in range(W):
                if tilemap[i][j] == "B":
                    screen.blit("mario/block", (j*ts - ox, i*ts - oy))

        for enemy in self.enemies:
            left = enemy.actor.left
            top = enemy.actor.top
            screen.blit(enemy.actor.image, (left - ox, top - oy))

        for coin in self.coins:
            left = coin.actor.left
            top = coin.actor.top
            screen.blit(coin.actor.image, (left - ox, top - oy))

        left = self.player.actor.left
        top = self.player.actor.top
        screen.blit(self.player.actor.image, (left - ox, top - oy))

        screen.draw.text(
            str(self.score),
            color='white',
            topleft=(tile_size*1.5, tile_size*1.5),
            fontsize=32
        )


class Menu(Loop):
    def __init__(self):
        btn_size = 128
        self.sound_on = True
        self.play = Actor('buttons/play', (WIDTH/2 - (btn_size), HEIGHT/2))
        self.sound = Actor('buttons/sound-on', (WIDTH/2, HEIGHT/2))
        self.exit = Actor('buttons/eject', (WIDTH/2 + btn_size, HEIGHT/2))

    def update(ts):
        pass

    def draw(self):

        screen.fill((92, 148, 252))
        self.play.draw()
        self.sound.draw()
        self.exit.draw()

        if game.is_over:
            screen.draw.text(
                str("You win!" if game.player.alive else "You lose!"),
                color='white',
                center=(WIDTH//2, tile_size*2),
                fontsize=32
            )

    def on_mouse_down(self, pos, button):
        if button == mouse.LEFT and self.play.collidepoint(pos):
            global game, state
            game = Game()
            state = State.GAME
        elif button == mouse.LEFT and self.sound.collidepoint(pos):
            if self.sound_on:
                music.pause()
                self.sound.image = "buttons/sound-off"
            else:
                music.unpause()
                self.sound.image = "buttons/sound-on"
            self.sound_on = not self.sound_on
        elif button == mouse.LEFT and self.exit.collidepoint(pos):
            exit()


def overlap(a: Actor, b: Actor):
    x_overlaps = (a.left < b.right) and (a.right > b.left)
    y_overlaps = (a.top < b.bottom) and (a.bottom > b.top)
    if x_overlaps and y_overlaps:
        return True
    return False


class State:
    MENU = 0
    GAME = 1


state = State.MENU

game = Game()
menu = Menu()


def update(ts):
    if state == State.GAME:
        game.update(ts)
    elif state == State.MENU:
        menu.update()


def draw():
    if state == State.GAME:
        game.draw()
    elif state == State.MENU:
        menu.draw()


def on_mouse_down(pos, button):
    if state == State.GAME:
        pass
    elif state == State.MENU:
        menu.on_mouse_down(pos, button)


music.play("mario_theme.ogg")
pgzrun.go()
