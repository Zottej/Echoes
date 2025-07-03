"""
Metroidvania procedural infinito – Pygame 2.x
Autor: ChatGPT · 2025-07-03
Requisitos: pygame>=2.0  (pip install pygame)
"""

import sys, random, pygame

# ──────────────────────────────────── CONSTANTES ─────────────────────────────────── 
WIDTH, HEIGHT         = 1920, 1080
TILE                  = 32
GRAVITY               = 0.35

PLAYER_WALK_SPEED     = 7
RUN_MULT              = 1.5
JUMP_SPEED            = 11
RUN_JUMP_BONUS        = 3
RELOAD_MS             = 1000

ENEMY_SPEED           = 2
BULLET_SPEED          = 12
MAG_CAPACITY          = 12
FPS                   = 60

H_TILES               = 40
CHUNK_W               = 120
PLATFORM_DENSITY      = 0.35
ENEMY_CHANCE          = 0.03

LOAD_TIME_MS          = 1000

COLOR_BG              = (18, 18, 24)
COLOR_PLATFORM        = (95, 95, 120)
COLOR_PLAYER          = (255, 230, 50)
COLOR_ENEMY           = (220, 50, 50)
COLOR_BULLET          = (255, 245, 200)
COLOR_UI              = (240, 240, 240)
COLOR_BTN             = (70, 70, 90)
COLOR_BTN_HOVER       = (100, 100, 130)
COLOR_RELOAD_BORDER   = (50, 50, 65)
COLOR_RELOAD_FILL     = (220, 220, 80)

pygame.init()
screen  = pygame.display.set_mode((WIDTH, HEIGHT))
clock   = pygame.time.Clock()
font    = pygame.font.SysFont(None, 28)
bigfont = pygame.font.SysFont(None, 120, bold=True)
pygame.display.set_caption("Metroidvania procedural")

# ──────────────────── ICONOS HUD (auto-generados) ─────────────────── 
def heart_icon(size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r = size // 4
    pygame.draw.circle(surf, (220, 60, 80), (r, r), r)
    pygame.draw.circle(surf, (220, 60, 80), (size - r, r), r)
    points = [(0, r), (size, r), (size//2, size)]
    pygame.draw.polygon(surf, (220, 60, 80), points)
    return surf


def bullet_icon(size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    w, h = size//3, size-8
    rect = pygame.Rect((size-w)//2, 4, w, h)
    pygame.draw.rect(surf, (200, 200, 200), rect, border_radius=3)
    return surf


def skull_icon(size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (235, 235, 235), (size//2, size//2), size//2)
    eye_r = size//6
    pygame.draw.circle(surf, (20,20,20), (size//3, size//3), eye_r)
    pygame.draw.circle(surf, (20,20,20), (2*size//3, size//3), eye_r)
    pygame.draw.line(surf, (20,20,20), (size//3, 2*size//3),
                     (2*size//3, 2*size//3), 3)
    return surf


ICON_HEART  = heart_icon()
ICON_BULLET = bullet_icon()
ICON_SKULL  = skull_icon()

# ──────────────────── UTILIDADES MAPA ─────────────────── 

def rect_from_grid(x, y):
    return pygame.Rect(x*TILE, y*TILE, TILE, TILE)


def tiles_from_rect(rect):
    return (range(int(rect.left//TILE), int((rect.right-1)//TILE)+1),
            range(int(rect.top//TILE),  int((rect.bottom-1)//TILE)+1))


# ──────────────────── ENTIDADES BÁSICAS ─────────────────── 
class Entity(pygame.sprite.Sprite):
    def __init__(self,x,y,w,h,color):
        super().__init__()
        self.image=pygame.Surface((w,h));self.image.fill(color)
        self.rect=self.image.get_rect(topleft=(x,y));self.vel=pygame.Vector2()

    def collide_level(self,level):
        self.rect.x+=self.vel.x
        cols,rows=tiles_from_rect(self.rect)
        for gx in cols:
            for gy in rows:
                if level.is_solid(gx,gy):
                    tile=rect_from_grid(gx,gy)
                    if self.vel.x>0:self.rect.right=tile.left
                    elif self.vel.x<0:self.rect.left=tile.right
                    self.vel.x=0
        self.rect.y+=self.vel.y
        cols,rows=tiles_from_rect(self.rect)
        on_ground=False
        for gx in cols:
            for gy in rows:
                if level.is_solid(gx,gy):
                    tile=rect_from_grid(gx,gy)
                    if self.vel.y>0:self.rect.bottom=tile.top;on_ground=True
                    elif self.vel.y<0:self.rect.top=tile.bottom
                    self.vel.y=0
        return on_ground


class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y,dir_vec):
        super().__init__()
        self.image=pygame.Surface((6,3));self.image.fill(COLOR_BULLET)
        self.pos=pygame.Vector2(x,y)
        self.vel=dir_vec.normalize()*BULLET_SPEED
        self.rect=self.image.get_rect(center=self.pos)

    def update(self,level):
        self.pos+=self.vel;self.rect.center=(round(self.pos.x),round(self.pos.y))
        gx=int(self.rect.centerx//TILE);gy=int(self.rect.centery//TILE)
        if not (0<=gx<len(level.tiles)) or level.is_solid(gx,gy):self.kill()


class Enemy(Entity):
    def __init__(self,x,y):
        super().__init__(x,y,TILE,TILE,COLOR_ENEMY)
        self.direction=random.choice([-1,1])

    def update(self,level):
        self.vel.x=ENEMY_SPEED*self.direction
        ahead_gx=int((self.rect.centerx+self.direction*TILE//2)//TILE)
        if not level.is_solid(ahead_gx,int((self.rect.bottom+1)//TILE)):
            self.direction*=-1
        self.vel.y+=GRAVITY;self.collide_level(level)


# ──────────────────── LEVEL ─────────────────── 
class Level:
    def __init__(self,h_tiles):
        self.h_tiles=h_tiles;self.tiles=[];self.last_x=0
        self.enemies_buffer=[];self._gen_chunk();self._spawn()

    def _gen_chunk(self):
        sx=self.last_x
        for _ in range(CHUNK_W): self.tiles.append([0]*self.h_tiles)
        for _ in range(int(CHUNK_W*PLATFORM_DENSITY)):
            length=random.randint(4,8)
            gx=sx+random.randint(1,CHUNK_W-length-1)
            gy=random.randint(6,self.h_tiles-10)
            for i in range(length): self.tiles[gx+i][gy]=2
        buf=[]
        for gx in range(sx,sx+CHUNK_W):
            for gy in range(self.h_tiles):
                if self.tiles[gx][gy]==2 and self.tiles[gx][gy-1]==0:
                    if random.random()<ENEMY_CHANCE:
                        buf.append(Enemy(gx*TILE+TILE//4,(gy-1)*TILE))
                    break
        self.enemies_buffer=buf;self.last_x+=CHUNK_W

    def ensure_width(self,x_tiles):
        if x_tiles>self.last_x-40: self._gen_chunk();return self.enemies_buffer
        return []

    def _spawn(self):
        for y in range(6,26):
            for x in range(3,min(60,len(self.tiles))):
                if self.tiles[x][y]==2 and self.tiles[x][y-1]==0:
                    self.spawn=(x*TILE,y*TILE-int(TILE*1.5));return
        self.spawn=(TILE,TILE*5)

    def is_solid(self,gx,gy):
        return 0<=gx<len(self.tiles) and 0<=gy<self.h_tiles and self.tiles[gx][gy]==2

    def draw(self,surf,off):
        first=max(0,off//TILE);last=min(len(self.tiles),(off+WIDTH)//TILE+1)
        for gx in range(first,last):
            for gy,code in enumerate(self.tiles[gx]):
                if code==2:
                    pygame.draw.rect(surf,COLOR_PLATFORM,(gx*TILE-off,gy*TILE,TILE,TILE))


# ──────────────────── PLAYER ─────────────────── 
class Player(Entity):
    def __init__(self,x,y):
        super().__init__(x,y,TILE,int(TILE*1.5),COLOR_PLAYER)
        self.health=4;self.ammo=MAG_CAPACITY
        self.running=False;self.reloading=False;self.reload_start=0

    def handle_input(self,keys):
        self.running=keys[pygame.K_LSHIFT]or keys[pygame.K_RSHIFT]
        speed=PLAYER_WALK_SPEED*(RUN_MULT if self.running else 1)
        self.vel.x=0
        if keys[pygame.K_a]or keys[pygame.K_LEFT]:self.vel.x=-speed
        if keys[pygame.K_d]or keys[pygame.K_RIGHT]:self.vel.x= speed
        if (keys[pygame.K_SPACE]or keys[pygame.K_w]or keys[pygame.K_UP])and self.on_ground:
            self.vel.y=-(JUMP_SPEED+(RUN_JUMP_BONUS if self.running else 0))

    def try_reload(self):
        if self.reloading or self.ammo==MAG_CAPACITY:return
        self.reloading=True;self.reload_start=pygame.time.get_ticks()

    def shoot(self,tx,ty):
        if self.reloading or self.ammo<=0:return None
        self.ammo-=1;dir_v=pygame.Vector2(tx-self.rect.centerx,ty-self.rect.centery)
        return Bullet(self.rect.centerx,self.rect.centery,dir_v) if dir_v.length_squared() else None

    def update(self,lvl,keys):
        self.handle_input(keys)
        if self.reloading and pygame.time.get_ticks()-self.reload_start>=RELOAD_MS:
            self.ammo=MAG_CAPACITY;self.reloading=False
        self.vel.y+=GRAVITY;self.on_ground=self.collide_level(lvl)

    def draw_reload(self,surf,cam_x):
        if not self.reloading:return
        prog=(pygame.time.get_ticks()-self.reload_start)/RELOAD_MS
        bw,bh=TILE,6;bx=self.rect.centerx-bw//2-cam_x;by=self.rect.top-12
        pygame.draw.rect(surf,COLOR_RELOAD_BORDER,(bx,by,bw,bh),1)
        pygame.draw.rect(surf,COLOR_RELOAD_FILL,(bx+1,by+1,int((bw-2)*prog),bh-2))


# ──────────────────── JUEGO ─────────────────── 

def new_game():
    lvl=Level(H_TILES);ply=Player(*lvl.spawn)
    return {"lvl":lvl,"ply":ply,
            "enem":pygame.sprite.Group(lvl.enemies_buffer),
            "blt":pygame.sprite.Group(),"kills":0}


def hud(surf,ply,kills):
    x=12;y=12
    surf.blit(ICON_HEART,(x,y));surf.blit(font.render(f"{ply.health}",True,COLOR_UI),(x+30,y+4))
    x+=70
    surf.blit(ICON_BULLET,(x,y));surf.blit(font.render(f"{ply.ammo}/{MAG_CAPACITY}",True,COLOR_UI),(x+30,y+4))
    x+=120
    surf.blit(ICON_SKULL,(x,y));surf.blit(font.render(f"{kills}",True,COLOR_UI),(x+30,y+4))
    if ply.running:surf.blit(font.render("🏃",True,COLOR_UI),(x+80,y+4))


def loading(progress):
    screen.fill(COLOR_BG);w=int(WIDTH*0.6);h=30;x=(WIDTH-w)//2;y=(HEIGHT-h)//2
    pygame.draw.rect(screen,COLOR_PLATFORM,(x,y,w,h),2)
    pygame.draw.rect(screen,COLOR_PLATFORM,(x+2,y+2,int((w-4)*progress),h-4))
    screen.blit(font.render("Loading...",True,COLOR_UI),(x,y-40));pygame.display.flip()


def game_over(kills):
    screen.fill(COLOR_BG);sk=bigfont.render("☠",True,COLOR_UI)
    screen.blit(sk,(WIDTH//2-sk.get_width()//2,HEIGHT//3-60))
    screen.blit(font.render("GAME OVER",True,COLOR_UI),(WIDTH//2-80,HEIGHT//3+30))
    screen.blit(font.render(f"Kills: {kills}",True,COLOR_UI),(WIDTH//2-40,HEIGHT//3+70))
    btn=pygame.Rect(WIDTH//2-110,HEIGHT//2+40,220,60)
    pygame.draw.rect(screen,COLOR_BTN_HOVER if btn.collidepoint(pygame.mouse.get_pos())else COLOR_BTN,btn)
    screen.blit(font.render("New Game",True,COLOR_UI),(btn.centerx-48,btn.centery-12))
    pygame.display.flip();return btn


def main():
    state="loading";load_t=pygame.time.get_ticks();game=None;cam_x=0
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT:pygame.quit();sys.exit()
            if state=="playing":
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    b=game["ply"].shoot(e.pos[0]+cam_x,e.pos[1])
                    if b:game["blt"].add(b)
                if e.type==pygame.KEYDOWN and e.key==pygame.K_r:game["ply"].try_reload()
            if state=="game_over":
                if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_KP_ENTER):state="loading";load_t=pygame.time.get_ticks()
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and btn.collidepoint(e.pos):state="loading";load_t=pygame.time.get_ticks()
        if state=="loading":
            p=(pygame.time.get_ticks()-load_t)/LOAD_TIME_MS
            loading(min(p,1))
            if p>=1:game=new_game();state="playing";continue
        elif state=="playing":
            g=game;lvl,ply,en,blt=g["lvl"],g["ply"],g["enem"],g["blt"]
            en.add(lvl.ensure_width((ply.rect.right//TILE)+40))
            keys=pygame.key.get_pressed();ply.update(lvl,keys);en.update(lvl);blt.update(lvl)
            if ply.rect.top>HEIGHT:state="game_over"
            hits=pygame.sprite.groupcollide(blt,en,True,True)
            if hits:g["kills"]+=sum(len(v)for v in hits.values())
            for enemy in en:
                if ply.rect.colliderect(enemy.rect):
                    ply.health-=1;ply.rect.x+=(-TILE if ply.rect.centerx<enemy.rect.centerx else TILE)
                    if ply.health<=0:state="game_over";break
            cam_x=max(0,min(ply.rect.centerx-WIDTH//2,len(lvl.tiles)*TILE-WIDTH))
            screen.fill(COLOR_BG);lvl.draw(screen,cam_x)
            for s in en:screen.blit(s.image,(s.rect.x-cam_x,s.rect.y))
            for s in blt:screen.blit(s.image,(s.rect.x-cam_x,s.rect.y))
            screen.blit(ply.image,(ply.rect.x-cam_x,ply.rect.y));ply.draw_reload(screen,cam_x)
            hud(screen,ply,g["kills"]);pygame.display.flip()
        elif state=="game_over":
            btn=game_over(game["kills"])
        clock.tick(FPS)


if __name__=="__main__":
    main()
