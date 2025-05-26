import os
import random
import math
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 0
ataris = []
bomb2s = []
zakos = []
explosion_list = []
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect, x=0,y=0) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    引数ｘｙ：はみ出し許容値
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left+x < 0 or WIDTH < obj_rct.right-x:
        yoko = False
    if obj_rct.top+y < 0 or HEIGHT < obj_rct.bottom-y:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -7),
        pg.K_DOWN: (0, +7),
        pg.K_LEFT: (-7, 0),
        pg.K_RIGHT: (+7, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0) # 初期方向（右向き）

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if sum_mv[0] != 0 and sum_mv[1] != 0: # 斜めスピードを調整
            self.rct.move_ip(int(sum_mv[0]/math.sqrt(2)), int(sum_mv[1]/math.sqrt(2)))
        else:
            self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True) and (sum_mv[0] != 0 and sum_mv[1] != 0):
            self.rct.move_ip(int(-sum_mv[0]/math.sqrt(2)), int(-sum_mv[1]/math.sqrt(2)))
        elif check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        # if not (sum_mv[0] == 0 and sum_mv[1] == 0):
        #     self.dire = tuple(sum_mv)
        #     self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")  # こうかとんSurface
        self.rct = self.img.get_rect()  # こうかとんRect
        self.rct.left = bird.rct.right  # ビームの左座標 = こうかとんの右座標
        self.vx, self.vy = bird.dire  # こうかとんの向きを速度ベクトルに代入
        tan = math.atan2(-self.vy, self.vx) 
        angle = math.degrees(tan)
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        self.rct.centerx = bird.rct.centerx + (bird.rct.width * (self.vx / 5))
        self.rct.centery = bird.rct.centery + (bird.rct.height * (self.vy / 5))
        
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx,  self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx*3, self.vy*3)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Zako:
    """
    雑魚敵実装：かまとぅ
    """
    def __init__(self):
        """
        初期化
        """
        global bomb2s
        self.img = pg.image.load("fig/kamato.png")
        self.rct = self.img.get_rect()
        self.rct.center = WIDTH, random.randint(50, HEIGHT-300)
        self.vx, self.vy = -3, 0
        self.interval = random.randint(50,300)
        self.life = 0
        self.hp = 5
        self.count = 0

    def update(self, screen: pg.Surface, bird: pg.Surface, pat: pg.Surface):
        """
        引数１：スクリーン
        引数２：プレイヤー１
        引数３：プレイヤー２
        戻り値：インスタンス削除
        """
        if self.life == self.interval:
            bomb2s.append(Bomb2((255, 255, 0), [20, 20], [self.rct.centerx, self.rct.centery], bird, pat, 0, 10, 1, 30, 0, 2))
            bomb2s.append(Bomb2((255, 255, 0), [20, 20], [self.rct.centerx, self.rct.centery], bird, pat, 0, 8, 1, 37, 0, 2))
            bomb2s.append(Bomb2((255, 255, 0), [20, 20], [self.rct.centerx, self.rct.centery], bird, pat, 0, 7, 1, 45, 0, 2))
        if self.hp <= 0:
            return True
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        self.life += 1
        if self.count >= 1:
            self.count += 1
            if self.count >= 3:
                self.img = pg.image.load("fig/kamato.png")
                self.count = 0
    
    def hidan(self):
        self.hp -= 1
        if self.count == 0:
            self.img = pg.transform.laplacian(self.img)
            self.count = 1


class Zako2:
    """
    雑魚敵実装：UFO
    """
    def __init__(self, x = WIDTH, y = random.randint(50, HEIGHT-50), idou = True):
        """
        初期化
        引数１、２：ｘ座標、ｙ座標
        引数３：移動するか
        """
        global bomb2s
        self.idou = idou
        self.img = pg.image.load("fig/alien1.png")
        self.rct = self.img.get_rect()
        self.rct.center = x, y
        self.vx, self.vy = -3, 0
        self.interval = random.randint(100,300)
        self.life = 0
        self.hp = 7
        self.count = 0

    def update(self, screen: pg.Surface, bird: pg.Surface, pat: pg.Surface):
        """
        引数１：スクリーン
        引数２：プレイヤー１
        引数３：プレイヤー２
        戻り値：インスタンス削除
        """
        if self.life == self.interval:
            self.vx, self.vy = 0,0
        elif self.life >= self.interval +25:
            bomb2s.append(Bomb2((255, 255, 255), [WIDTH*2, 30], [self.rct.centerx, self.rct.centery], bird, pat, 2, 0, 1, 0, 0, 0, 10))
            bomb2s.append(Bomb2((255, 255, 255), [30, HEIGHT*2], [self.rct.centerx, self.rct.centery], bird, pat, 2, 0, 1, 90, 0, 0, 10))
            explosion_list.append(Explosion((self.rct.centerx,self.rct.centery),15))
            return True
        if self.hp <= 0:
            return True
        if self.idou:
            self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        self.life += 1
        if self.count >= 1:
            self.count += 1
            if self.count >= 3:
                self.img = pg.image.load("fig/alien1.png")
                self.count = 0

    def hidan(self):
        self.hp -= 1
        if self.count == 0:
            self.img = pg.transform.laplacian(self.img)
            self.count = 1


class Boss:
    """
    ボス実装
    """
    def __init__(self):
        """
        ボス本体と顔パーツを生成
        """
        global ataris
        global bomb2s
        self.hp = 200
        self.hidan_count = 0
        self.vx = 0
        self.vz = 0
        self.motions = ["normal", "nobi", "oti"]
        self.motion = "normal"
        self.motion_life = -150 # モーションフレーム
        self.nobis = [] # 伸びるモーションのリスト
        self.count = 0
        self.centerx = 780 # 眉間座標ｘ
        self.centery = 210 # 眉間座標ｙ
        self.nobix = self.centerx # 伸びるモーションのｘ座標
        self.nobiy = 0 # 伸びるモーションの-ｙ座標
        self.eye_rad = 60 # 眉間半径
        self.eye_theta = math.radians(15) # 目の傾き
        # 目１の相対座標
        self.eye1 = [100-self.eye_rad*math.cos(self.eye_theta), 100+self.eye_rad*math.sin(self.eye_theta)]
        print(self.eye1)
        # 目２の
        self.eye2 = [100+self.eye_rad*math.cos(self.eye_theta), 100-self.eye_rad*math.sin(self.eye_theta)]
        print(self.eye2)
        self.eye_size = 20 # 目の半径
        
        # 本体
        self.img = pg.image.load("fig/kamacan.jpg")
        self.img = pg.transform.rotozoom(self.img, 0, 0.5)
        self.img.set_colorkey("#FFFFFF")
        self.rct = self.img.get_rect()
        self.rct.center = 850, 350
        ataris.append(Atari(500,200,[850,475]))
        ataris.append(Atari(350,300,[850,300]))

        # ぎょろ目
        self.eye_img = pg.Surface((200, 200))
        self.eye_img.fill("#00FF00")
        pg.draw.circle(self.eye_img, "#000000", self.eye1, self.eye_size+3)
        pg.draw.circle(self.eye_img, "#000000", self.eye2, self.eye_size+3)
        pg.draw.circle(self.eye_img, "#FFFFFF", self.eye1, self.eye_size)
        pg.draw.circle(self.eye_img, "#FFFFFF", self.eye2, self.eye_size)
        self.eye_img.set_colorkey("#00FF00")
        self.eye_rct = self.eye_img.get_rect()
        self.eye_rct.center = self.centerx, self.centery

        self.hitomi1_img = pg.Surface((200, 200))
        pg.draw.circle(self.hitomi1_img, "#FF0000", self.eye1, self.eye_size/2)
        self.hitomi1_rct = self.hitomi1_img.get_rect()
        self.hitomi1_rct.center = self.centerx, self.centery
        self.hitomi1_img.set_colorkey("#000000")
        self.hitomi2_img = pg.Surface((200, 200))
        pg.draw.circle(self.hitomi2_img, "#FF0000", self.eye2, self.eye_size/2)    
        self.hitomi2_rct = self.hitomi2_img.get_rect()
        self.hitomi2_rct.center = self.centerx, self.centery 
        self.hitomi2_img.set_colorkey("#000000")

        # 閉じた目
        self.eye_toji_img = pg.Surface((200, 200))
        self.eye_toji_img.fill("#00FF00")
        pg.draw.lines(self.eye_toji_img, "#000000", False, [(self.eye1[0]-self.eye_size, self.eye1[1]-self.eye_size),(self.eye1[0]+self.eye_size*math.cos(self.eye_theta), self.eye1[1]-self.eye_size*math.sin(self.eye_theta)),(self.eye1[0]-self.eye_size, self.eye1[1]+self.eye_size)], 5)
        pg.draw.line(self.eye_toji_img, "#000000", (self.eye1[0]-self.eye_size, self.eye1[1]), (self.eye1[0]+self.eye_size*math.cos(self.eye_theta), self.eye1[1]-self.eye_size*math.sin(self.eye_theta)), 5)
        pg.draw.lines(self.eye_toji_img, "#000000", False, [(self.eye2[0]+self.eye_size, self.eye2[1]-self.eye_size),(self.eye2[0]-self.eye_size*math.cos(self.eye_theta), self.eye2[1]+self.eye_size*math.sin(self.eye_theta)),(self.eye2[0]+self.eye_size, self.eye2[1]+self.eye_size)], 5)
        pg.draw.line(self.eye_toji_img, "#000000", (self.eye2[0]+self.eye_size, self.eye2[1]), (self.eye2[0]-self.eye_size*math.cos(self.eye_theta), self.eye2[1]+self.eye_size*math.sin(self.eye_theta)), 5)
        self.eye_toji_img.set_colorkey(("#00FF00"))
        self.eye_toji_rct = self.eye_toji_img.get_rect()
        self.eye_toji_rct.center = self.centerx, self.centery

        # 口
        self.kuti_img = pg.Surface((150,20))
        pg.draw.ellipse(self.kuti_img, "#0F0000", (0,0,150,20))
        pg.draw.ellipse(self.kuti_img, "#FF0000", (0,0,150,20),5)
        self.kuti_img = pg.transform.rotozoom(self.kuti_img, 15, 1)
        self.kuti_img.set_colorkey("#000000")
        self.kuti_rct = self.kuti_img.get_rect()
        self.kuti_rct.center = self.centerx, self.centery + 50

        # 開き口
        self.kuti2_img = pg.Surface((150,40))
        pg.draw.ellipse(self.kuti2_img, "#0F0000", (0,0,150,40))
        pg.draw.ellipse(self.kuti2_img, "#FF0000", (0,0,150,40),5)
        self.kuti2_img = pg.transform.rotozoom(self.kuti2_img, 15, 1)
        self.kuti2_img.set_colorkey("#000000")
        self.kuti2_rct = self.kuti2_img.get_rect()
        self.kuti2_rct.center = self.centerx, self.centery + 50

        # 閉じ口
        self.kuti3_img = pg.Surface((150,40))
        pg.draw.arc(self.kuti3_img, "#FF0000", (0,0,150,100),0,180,5)
        self.kuti3_img = pg.transform.rotozoom(self.kuti3_img, 15, 1)
        self.kuti3_img.set_colorkey("#000000")
        self.kuti3_rct = self.kuti3_img.get_rect()
        self.kuti3_rct.center = self.centerx, self.centery + 50


    def update(self, screen: pg.Surface, bird:"Bird", pat:"Bird"):
        """
        ボス本体と顔パーツを表示
        モーションをランダムに選択し、描画
        引数１：スクリーン
        引数２：プレイヤー１
        引数３：プレイヤー２
        """
        if self.hp <= 0:
            return True
        screen.blit(self.img, self.rct)
        # モーション選択
        if self.motion_life < 0:
            self.motion = "normal"
        if self.motion_life == 0:
            self.motion = self.motions[random.randint(0,len(self.motions)-1)]
        self.motion_life += 1
        # 通常モーション
        if self.motion == "normal":
            if self.motion_life % 50 == 20:
                bomb2s.append(Bomb2((0, 255, 255), [60, 60], [780, 250], bird, bird, 1, 5, 0, 0))
                bomb2s.append(Bomb2((0, 255, 255), [60, 60], [780, 250], bird, bird, 1, 5, 0, 30))
                bomb2s.append(Bomb2((0, 255, 255), [60, 60], [780, 250], bird, bird, 1, 5, 0, -30))
                bomb2s.append(Bomb2((0, 255, 255), [60, 60], [780, 250], bird, bird, 1, 5, 0, 60))
                bomb2s.append(Bomb2((0, 255, 255), [60, 60], [780, 250], bird, bird, 1, 5, 0, -60))
                self.kao_part(0,1,[self.centerx, self.centery], screen, bird, pat)
            elif self.motion_life % 50 >= 15 and self.motion_life % 50 <= 25:
                self.kao_part(0,1,[self.centerx, self.centery], screen, bird, pat)
            else:
                self.kao_part(0,0,[self.centerx, self.centery], screen, bird, pat)
            if self.motion_life > 50:
                self.motion_life = 0
        # 伸びるモーション
        elif self.motion == "nobi": 
            # 以下スパゲッティコード
            if self.count == 0:
                self.nerai = bird.rct.centerx
                self.count = 1
            # 前半
            if self.motion_life > 30 and self.motion_life < 60:
                if self.motion_life < 40:
                    self.nobiy += 5
                elif self.motion_life < 45:
                    self.nobiy += 15
                else:
                    self.nobiy += 25
                if self.nobiy % 10 == 0:
                    self.nobis.append(Nobi(self.rct.center, self.nobiy))
                    ataris.clear()
                    ataris.append(Atari(500,200+self.nobiy,[850,475-self.nobiy/2]))
                    ataris.append(Atari(350,300+self.nobiy,[850,300-self.nobiy/2]))
                for nobi in self.nobis:
                    nobi.update(screen)
                self.kao_part(1,2,[self.nobix, self.centery - self.nobiy], screen, bird, pat)
            # 後半
            elif self.motion_life > 100 and self.motion_life < 108:
                if self.count == 1:
                    self.nobix = self.nerai
                    self.nobiy = 400
                    self.count = 2
                self.nobiy -= 25
                if self.nobiy % 10 == 0:
                    self.nobis.append(Nobi([self.nobix, self.rct.centery], self.nobiy, True))
                    ataris.clear()
                    ataris.append(Atari(500,600,[850,300]))
                    ataris.append(Atari(500,200,[self.nobix,HEIGHT-self.nobiy-310]))
                    ataris.append(Atari(350,300,[self.nobix,HEIGHT-self.nobiy-170]))
                for nobi in self.nobis:
                    nobi.update(screen)
                self.kao_part(1,2,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, pat, True)
            # 止まる
            elif self.motion_life >= 108 and self.motion_life <= 400:
                for nobi in self.nobis:
                    nobi.update(screen)
                if self.motion_life % 50 == 20:
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, 0))
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, 45))
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, -45))
                    self.kao_part(0,1,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, pat, True)
                elif self.motion_life % 50 >= 15 and self.motion_life % 50 <= 25:
                    self.kao_part(0,1,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, pat, True)
                else:
                    self.kao_part(0,0,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, pat, True)
            # 縮まる
            elif self.motion_life > 400:
                ataris.clear()
                ataris.append(Atari(500,200,[850,475]))
                ataris.append(Atari(350,300,[850,300]))
                if len(self.nobis) != 0 and self.motion_life%2:
                    self.nobis.pop(-1)
                if len(self.nobis) == 0:
                    self.count += 1
                    # リセット処理
                    if self.count >= 50:
                        self.motion_life = -150
                        self.nobix = self.centerx
                        self.nobiy = 0
                        self.count = 0
                    self.kao_part(1,2,[self.centerx, self.centery], screen, bird, pat)
                else:
                    for nobi in self.nobis:
                        nobi.update(screen)
                    if self.nobis[-1].hanten == True:
                        self.kao_part(1,2,[self.nobis[-1].rct.centerx + 70, self.nobis[-1].rct.centery + 50], screen, bird, pat, True)
                    else:
                        self.kao_part(1,2,[self.centerx, self.nobis[-1].rct.centery-30], screen, bird, pat)
            else:
                for nobi in self.nobis:
                    nobi.update(screen)
                self.kao_part(1,2,[self.nobix, self.centery - self.nobiy], screen, bird, pat)
        elif self.motion == "oti":
            if self.motion_life <= 10:
                self.vy = -10
            elif self.motion_life > 100:
                self.motion_life = -150
                self.count = 0
                self.vz = 0
            elif self.motion_life < 20 or self.motion_life >= 70:
                self.vy = 0
            elif self.motion_life % 20 < 10:
                self.count += 1
                self.vy = 10
                if self.count % 10 == 0:
                    if self.count == 10:
                        for i in range(int(WIDTH/150)):
                            bomb2s.append(Bomb2((0,0,0), [20,200], [i*150,-50],bird,bird,3,8,1,-90))
                            bomb2s.append(Bomb2((0,0,0), [20,500], [i*150+ 75,-400],bird,bird,3,8,1,-90))
                            bomb2s.append(Bomb2((0,0,0), [20,1000], [i*150,-750],bird,bird,3,8,1,-90))
                    for i in range(5):
                        explosion_list.append(Explosion((600 + i*100 + random.randint(0,100),random.randint(575, 600)), 5))
            else:
                self.vy = -10
            self.kao_part(1,2,[self.centerx,self.centery+self.vz], screen, bird, pat)
            self.vz += self.vy
            self.rct.move_ip(0, self.vy)
            for atari in ataris:
                atari.rct.move_ip(self.vx, self.vy)

        if self.hidan_count >= 1:
            self.hidan_count += 1
            for atari in ataris:
                atari.update(screen)
            if self.hidan_count >= 3:
                self.hidan_count = 0

    def kao_part(self, eyes:int, kuti:int, zahyou:list, screen: pg.Surface, bird:"Bird", pat:"Bird", hanten=False):
        """
        顔パーツを描写
        引数１：目のパターン
        引数２：口のパターン
        引数３：パーツセンター座標
        引数４：スクリーン
        引数５：プレイヤー１
        引数６：プレイやー２
        """
        if eyes == 0: # ぎょろ目
            self.eye_rct.center = zahyou
            screen.blit(self.eye_img, self.eye_rct)
            if zahyou[0]-bird.rct.centerx != 0:
                self.hitomi1_theta = math.atan2((zahyou[1]-bird.rct.centery),(zahyou[0]-bird.rct.centerx))
            self.hitomi1_rct.center = zahyou[0] - (self.eye_size/2)*math.cos(self.hitomi1_theta), zahyou[1] - (self.eye_size/2)*math.sin(self.hitomi1_theta)
            screen.blit(self.hitomi1_img, self.hitomi1_rct)
            if zahyou[0]-pat.rct.centerx != 0:
                self.hitomi2_theta = math.atan2((zahyou[1]-pat.rct.centery),(zahyou[0]-pat.rct.centerx))
            self.hitomi2_rct.center = zahyou[0] - (self.eye_size/2)*math.cos(self.hitomi2_theta), zahyou[1] - (self.eye_size/2)*math.sin(self.hitomi2_theta)
            screen.blit(self.hitomi2_img, self.hitomi2_rct)
        elif eyes == 1: # 閉じた目
            self.eye_toji_rct.center = zahyou
            screen.blit(self.eye_toji_img, self.eye_toji_rct)
        if hanten:
            puramai = -50
        else:
            puramai = 50
        if kuti == 0:
            self.kuti_rct.center = zahyou[0], zahyou[1]+puramai
            screen.blit(self.kuti_img, self.kuti_rct)
        elif kuti == 1:
            self.kuti2_rct.center = zahyou[0], zahyou[1]+puramai
            screen.blit(self.kuti2_img, self.kuti2_rct)
        elif kuti == 2:
            self.kuti3_rct.center = zahyou[0], zahyou[1]+puramai
            screen.blit(self.kuti3_img, self.kuti3_rct)

    def hidan(self):
        self.hp -= 1
        if self.hidan_count == 0:
            self.hidan_count = 1


class Nobi:
    def __init__(self, zahyou:list, y:int, hanten=False):
        self.hanten = hanten
        if hanten:
            self.img = pg.image.load("fig/kamacan2.jpg")
            self.img = pg.transform.rotozoom(self.img, 180, 0.5)
            self.rct = self.img.get_rect()
            self.rct.center = zahyou[0] , HEIGHT -110 - y
        else:
            self.img = pg.image.load("fig/kamacan2.jpg")
            self.img = pg.transform.rotozoom(self.img, 0, 0.5)
            self.rct = self.img.get_rect()
            self.rct.center = zahyou[0] , zahyou[1] -110 - y
        self.img.set_colorkey("#FFFFFF")

    def update(self, screen: pg.Surface):
        screen.blit(self.img, self.rct)


class Boss2:
    """
    ボス実装
    """
    def __init__(self):
        """
        ボス本体と顔パーツを生成
        """
        global ataris
        self.hp = 200
        self.hidan_count = 0
        global bomb2s
        global zakos
        self.vx = 0
        self.vy = 1
        self.motions = ["normal", "syoukan"]
        self.motion = "toujyou"
        self.motion_life = -500


        self.img = pg.image.load("fig/alien1.png")
        self.img = pg.transform.rotozoom(self.img, 0, 4)
        self.rct = self.img.get_rect()
        self.rct.center = 850, 0
        self.fusi_img = pg.image.load("fig/fusimi.jpg")
        self.fusi_img = pg.transform.rotozoom(self.fusi_img, 0, 0.5)
        self.fusi_img.set_colorkey("#FFFFFF")
        self.fusi_rct = self.fusi_img.get_rect()
        self.fusi_rct.center = 850, -100
        ataris.append(Atari(300,200,[850,25]))
        ataris.append(Atari(150,300,[850,-50]))

    def update(self, screen: pg.Surface, bird, pat):
        if self.hp <= 0:
            return True
        for atari in ataris:
            atari.rct.move_ip(self.vx, self.vy)
        self.rct.move_ip(self.vx, self.vy)
        self.fusi_rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        screen.blit(self.fusi_img, self.fusi_rct)
        if self.motion_life < -150:
            self.motion = "toujyou"
        elif self.motion_life < 0:
            self.vx = 0
            self.vy = 0 
            self.motion = "normal"
        elif self.motion_life == 0:
            self.motion = self.motions[random.randint(0,len(self.motions)-1)]
        self.motion_life += 1
        if self.motion_life > 0:
            self.vx = 2*math.cos(math.radians(self.motion_life-90))
            self.vy = 3*math.sin(math.radians(self.motion_life-90))
        if self.motion == "normal":
            if self.motion_life % 50 == 20:
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 0))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 30))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -30))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 60))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -60))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 90))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -90))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 120))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -120))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 150))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -150))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 180))
            if self.motion_life % 50 == 45:
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 15))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -15))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -45))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 45))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -75))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 75))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -105))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 105))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -135))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 135))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, -165))
                bomb2s.append(Bomb2((0, 255, 0), [60, 60], [self.rct.centerx, self.rct.centery], bird, bird, 0, 5, 1, 165))
            if self.motion_life % 360 == 300:
                bomb2s.append(Bomb2((255, 255, 255), [500, 100], [self.fusi_rct.centerx, self.fusi_rct.centery-50], bird, bird, 4, 10, 1, 0))
                if self.motion_life > 360:
                    self.motion_life = 0
        if self.motion == "syoukan":
            if self.motion_life % 360 == 100:
                for i in range(WIDTH // 150):
                    zakos.append(Zako2(i*150, 30, False))
                for i in range(HEIGHT // 150):
                    zakos.append(Zako2(WIDTH-30, i*150+100, False))
            if self.motion_life > 360:
                self.motion_life = 0
        if self.hidan_count >= 1:
            self.hidan_count += 1
            for atari in ataris:
                atari.update(screen)
            if self.hidan_count >= 3:
                self.hidan_count = 0
    
    def hidan(self):
        self.hp -= 1
        if self.hidan_count == 0:
            self.hidan_count = 1


class Atari:
    """
    ボスの当たり判定に関するクラス
    """
    def __init__(self, xsize, ysize, center : list):
        self.img = pg.Surface((xsize, ysize))
        pg.draw.rect(self.img, "#FF0000", (0,0,xsize,ysize))
        self.img.set_alpha(50)
        self.rct = self.img.get_rect()
        self.rct.center = center
    def update(self, screen: pg.Surface):
        screen.blit(self.img, self.rct)


class Bomb2:
    """
    弾幕のクラス
    """
    def __init__(self, color: tuple[int, int, int], size: list, zahyou: list, bird: pg.Surface, pat: pg.Surface, zukei=0, speed=5, ugoki=0, kakudo=0, ax=0, ay=0, time=500):
        """
        引数に基づき爆弾Surfaceを生成する
        引数1 color：爆弾の色タプル
        引数2 size:[x,y]
        引数3 zahyou：発射点
        引数4 bird：こうかとん
        引数5 pat：パッチ
        引数6 zukei:0,楕円 1,ドーナツ円 2,長方形 3,星
        引数7 speed:速さ
        引数8 ugoki:動くパターン 0,プレイヤー*角度に真っすぐ 1,横*角度に真っすぐ
        引数9 kakudo:角度
        引数10 ax:ｘ方向加速度
        引数11 ay:y方向
        引数12 time:効果時間
        """
        self.size = size
        self.zukei = zukei
        self.speed = speed
        self.kakudo = kakudo
        self.ax = ax
        self.ay = ay
        self.time = time
        self.theta = 1
        self.life = 0
        self.count = random.randint(0, 3)
        self.img = pg.Surface((size[0], size[1]))
        if zukei == 0:
            pg.draw.ellipse(self.img, color, (0, 0, size[0], size[1]))
            self.img.set_colorkey((0, 0, 0))
            self.rct = self.img.get_rect()
            self.rct.center = zahyou
        elif zukei == 1:
            pg.draw.ellipse(self.img, color, (0, 0, size[0], size[1]),int(size[0]/5))
            self.img.set_colorkey((0, 0, 0))
            self.rct = self.img.get_rect()
            self.rct.center = zahyou
        elif zukei == 2:
            pg.draw.rect(self.img, color, (0,0,size[0],size[1]))
            self.rct = self.img.get_rect()
            self.rct.center = zahyou
        elif zukei == 3:
            self.img = pg.Surface((50, 48))
            self.img = pg.image.load("fig/star.png")
            self.img = pg.transform.rotozoom(self.img, 0, 1)
            self.rct = self.img.get_rect()
            self.rct.center = zahyou
            self.img2 = pg.Surface((50, 48))
            self.img2 = pg.image.load("fig/star.png")
            self.img2 = pg.transform.rotozoom(self.img2, 45, 1)
            self.rct2 = self.img2.get_rect()
            self.rct2.center = zahyou
        elif zukei == 4:
            self.img = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", size[1])
            if self.count == 0:
                self.img = self.img.render(f"SA働け！！！！！", 0, color)
            elif self.count == 1:
                self.img = self.img.render(f"減給するぞ！！！", 0, color)
            elif self.count == 2:
                self.img = self.img.render(f"手挙がってま～す", 0, color)
            elif self.count == 3:
                self.img = self.img.render(f"出典：大学公式hp", 0, color)
            self.count += 1
            self.rct = self.img.get_rect( )
            self.rct.center = zahyou

        if ugoki == 0:
            if zahyou[0]-bird.rct.centerx != 0:
                self.theta = math.atan2((zahyou[1]-bird.rct.centery),(zahyou[0]-bird.rct.centerx))
            self.vx = -speed * math.cos(self.theta + math.radians(kakudo))
            self.vy = -speed * math.sin(self.theta + math.radians(kakudo))
        if ugoki == 1:
            self.theta = 0
            self.vx = -speed * math.cos(self.theta + math.radians(kakudo))
            self.vy = -speed * math.sin(self.theta + math.radians(kakudo))

        

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        戻り値：インスタンス削除
        """
        if self.time <= 0:
            return True
        yoko, tate = check_bound(self.rct,self.size[0],self.size[1])
        if not yoko:
            return True
        if not tate:
            return True
        self.life += 1
        if self.life % 10 == 0:
            self.vx += self.ax
            self.vy += self.ay
        self.rct.move_ip(self.vx, self.vy)
        if self.zukei == 3:
            self.rct2.move_ip(self.vx, self.vy)
            if self.life % 10 >= 5:
                screen.blit(self.img2, self.rct2)
            else:
                screen.blit(self.img, self.rct)
        else:
            screen.blit(self.img, self.rct)
        self.time -= 1


class Score:
    """
    スコアを表示させるクラス
    """
    def __init__(self):
        """
        スコアのフォントや色の設定．文字列Surfaceの生成を行う
        引数 score：点数
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        score = 0
        self.img = self.font.render(f"スコア：{score}", 0, (0, 0, 255))
        self.rct = self.img.get_rect()
        self.score = score
        self.rct.center = (100, HEIGHT-50)

    def update(self, num: int, screen: pg.Surface):
        """
        現在のスコアを表示させる文字列Surfaceの生成
        スクリーンにblit
        """
        self.score = num
        self.img = self.font.render(f"スコア：{num}", 0, (0, 0, 255))
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトを表示させるクラス
    """
    def __init__(self, xy: tuple[int, int], time: int):
        self.img0 = pg.image.load("fig/explosion.gif")
        self.img_flip = pg.transform.flip(self.img0, True, True) # 上下左右反転
        self.imgs = [self.img0, self.img_flip]
        self.index = 0
        self.img = self.imgs[self.index]
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.life = time

    def update(self, screen: pg.Surface):
        """
        爆発経過時間lifeを１減算
        爆発経過時間lifeが正なら，Surfaceリストを交互に切り替えて爆発を演出
        """
        self.life -= 1
        if self.life > 0:
            self.img = self.imgs[self.index % len(self.imgs)]  # あまりを計算
            screen.blit(self.img, self.rct)
            self.index += 1


class Gekiha:
    """
    撃破演出
    """
    def __init__(self, n:int):
        """
        引数：0,ボス１ 1,ボス２
        """
        self.n = n
        global explosion_list
        self.life = 0

        if self.n == 0:
            self.centerx = 780 # 眉間座標ｘ
            self.centery = 210 # 眉間座標ｙ
            self.eye_rad = 60 # 眉間半径
            self.eye_theta = math.radians(15) # 目の傾き
            # 目１の相対座標
            self.eye1 = [100-self.eye_rad*math.cos(self.eye_theta), 100+self.eye_rad*math.sin(self.eye_theta)]
            # 目２の
            self.eye2 = [100+self.eye_rad*math.cos(self.eye_theta), 100-self.eye_rad*math.sin(self.eye_theta)]
            self.eye_size = 20 # 目の半径
            self.img = pg.image.load("fig/kamacan.jpg")
            self.img = pg.transform.rotozoom(self.img, 0, 0.5)
            self.img.set_colorkey("#FFFFFF")
            self.rct = self.img.get_rect()
            self.rct.center = 850, 350

            self.eye_toji_img = pg.Surface((200, 200))
            self.eye_toji_img.fill("#00FF00")
            pg.draw.lines(self.eye_toji_img, "#000000", False, [(self.eye1[0]-self.eye_size, self.eye1[1]-self.eye_size),(self.eye1[0]+self.eye_size*math.cos(self.eye_theta), self.eye1[1]-self.eye_size*math.sin(self.eye_theta)),(self.eye1[0]-self.eye_size, self.eye1[1]+self.eye_size)], 5)
            pg.draw.line(self.eye_toji_img, "#000000", (self.eye1[0]-self.eye_size, self.eye1[1]), (self.eye1[0]+self.eye_size*math.cos(self.eye_theta), self.eye1[1]-self.eye_size*math.sin(self.eye_theta)), 5)
            pg.draw.lines(self.eye_toji_img, "#000000", False, [(self.eye2[0]+self.eye_size, self.eye2[1]-self.eye_size),(self.eye2[0]-self.eye_size*math.cos(self.eye_theta), self.eye2[1]+self.eye_size*math.sin(self.eye_theta)),(self.eye2[0]+self.eye_size, self.eye2[1]+self.eye_size)], 5)
            pg.draw.line(self.eye_toji_img, "#000000", (self.eye2[0]+self.eye_size, self.eye2[1]), (self.eye2[0]-self.eye_size*math.cos(self.eye_theta), self.eye2[1]+self.eye_size*math.sin(self.eye_theta)), 5)
            self.eye_toji_img.set_colorkey(("#00FF00"))
            self.eye_toji_rct = self.eye_toji_img.get_rect()
            self.eye_toji_rct.center = self.centerx, self.centery

            self.kuti2_img = pg.Surface((150,40))
            pg.draw.ellipse(self.kuti2_img, "#0F0000", (0,0,150,40))
            pg.draw.ellipse(self.kuti2_img, "#FF0000", (0,0,150,40),5)
            self.kuti2_img = pg.transform.rotozoom(self.kuti2_img, 15, 1)
            self.kuti2_img.set_colorkey("#000000")
            self.kuti2_rct = self.kuti2_img.get_rect()
            self.kuti2_rct.center = self.centerx, self.centery + 50

        if self.n == 1:
            self.fusi_img = pg.image.load("fig/fusimi.jpg")
            self.fusi_img = pg.transform.rotozoom(self.fusi_img, 0, 0.5)
            self.fusi_rct = self.fusi_img.get_rect()
            self.fusi_rct.center = 850, 350
            self.kakudai = 0.5
            self.kakudo = 0
            self.y = 0

    def update(self,screen: pg.Surface):
        self.life += 1
        if self.n == 0:
            self.rct.move_ip(0,2)
            self.eye_toji_rct.move_ip(0,2)
            self.kuti2_rct.move_ip(0,2)
            if self.life % 5 == 0:
                for i in range(10):
                    x = random.randint(self.rct.centerx-300, self.rct.centerx+300)
                    y = random.randint(self.rct.centery-300, self.rct.centery+200)
                    explosion_list.append(Explosion((x,y), 5))
            screen.blit(self.img, self.rct)
            screen.blit(self.eye_toji_img, self.eye_toji_rct)
            screen.blit(self.kuti2_img, self.kuti2_rct)
            if self.life > 200:
                return True
        elif self.n == 1:
            if self.life < 10:
                for i in range(20):
                    x = random.randint(int(WIDTH/2),WIDTH)
                    y = random.randint(0, HEIGHT)
                    explosion_list.append(Explosion((x,y), 5))
            if self.kakudai < 0.01:
                self.kakudai -= 0.002
                if self.kakudai < -0.01:
                    self.star_img = pg.image.load("fig/star.png")
                    self.star_img = pg.transform.rotozoom(self.star_img, 0, 1)
                    self.star_rct = self.star_img.get_rect()
                    self.star_rct.center = 850, 350-self.y
                    screen.blit(self.star_img, self.star_rct)
                if self.kakudai < -0.02:   
                    return True
            elif self.life > 5:
                self.fusi_img = pg.image.load("fig/fusimi.jpg")
                self.fusi_img = pg.transform.rotozoom(self.fusi_img, -self.kakudo, self.kakudai)
                self.fusi_rct = self.fusi_img.get_rect()
                self.fusi_rct.center = 850, 350-self.y
                self.y += 1
                self.kakudo += 10
                self.kakudai -= 0.002
                screen.blit(self.fusi_img, self.fusi_rct)


class Gameclear:
    """
    独自の機能：ゲームクリアを表示させるクラス
    """
    def __init__(self):
        self.gameover_sur = pg.Surface((WIDTH, HEIGHT))
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 60)
        self.cry = pg.image.load("fig/2.png") 
        self.cry2 = pg.image.load("fig/5.png") 
        self.gameover_txt = self.font.render("GAME CLEAR !!!",True,(255, 255, 0))
        self.gameover_sur.set_alpha(130)
        pg.draw.rect(self.gameover_sur, (0, 0, 0), pg.Rect(0, 0, WIDTH, HEIGHT))
    
    def update(self, screen: pg.Surface):
        """
        ゲームクリアの文字とこうかとんを表示
        """
        screen.blit(self.gameover_sur, [0, 0])
        screen.blit(self.gameover_txt, [330, 300])
        screen.blit(self.cry, [261, 290])
        screen.blit(self.cry2, [763, 292])


def main():
    pg.display.set_caption("蒲田の逆襲")
    screen = pg.display.set_mode((WIDTH, HEIGHT))   
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    boss = None
    global zakos
    zako_interval = random.randint(20, 60)
    zako_count = 0
    global bomb2s
    global ataris
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 不要な変数を使うときは_で表す
    score = Score()
    game_score = 0
    beam_list = []
    global explosion_list
    game_clear = Gameclear()
    clock = pg.time.Clock()
    beam = None         
    gekiha = None
    phase = 1
    phase_count = 0              
    tmr = 0
    while True:
        # 雑魚フェーズ
        if tmr % 50 == zako_interval and phase == 1:
            if random.randint(0,3) < 3:
                zakos.append(Zako())
            else:
                zakos.append(Zako2(WIDTH, random.randint(50, HEIGHT-50)))
        elif tmr % 50 + 50 == zako_interval and phase == 1: 
            zako_interval = random.randint(0, 49)
        # カマキャンフェーズ
        if phase == 3 and tmr % 200 == zako_interval:
            if random.randint(0,1):
                zakos.append(Zako())
            else:  
                zakos.append(Zako2(WIDTH, random.randint(50, HEIGHT-50)))
        elif tmr % 150 + 50 == zako_interval and phase == 1: 
            zako_interval = random.randint(0, 49)


        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
                beam_list.append(beam)            
        screen.blit(bg_img, [0, 0])
        if beam_list is not None:
            for bomb in bombs:
                if bird.rct.colliderect(bomb.rct):
                    # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                    bird.change_img(8, screen)
                    fonto = pg.font.Font(None, 80)
                    txt = fonto.render("Game Over", True, (255, 0, 0))
                    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                    pg.display.update()
                    time.sleep(1)
                    return

            for i, bomb in enumerate(bombs):
                for b, beam_obj in enumerate(beam_list):
                    if beam_obj.rct.colliderect(bomb.rct):
                        # 爆弾とビームが衝突した際にBeamインスタンス，Bombインスタンスを消滅
                        explosion = Explosion(bomb.rct.center, 15)
                        explosion_list.append(explosion)
                        beam_list[b] = None
                        bombs[i] = None
                        bird.change_img(6, screen)  # よろこびエフェクト
                        bombs = [bomb for bomb in bombs if bomb is not None]
                        beam_list = [beam_obj for beam_obj in beam_list if beam_obj is not None]
                        game_score += 1
                        pg.display.update()
                        break 
            # 雑魚ダメージ判定
            for zako in zakos:
                for b, beam_obj in enumerate(beam_list):
                    if beam_obj.rct.colliderect(zako.rct): 
                        zako.hidan()
                        beam_list[b] = None
                        beam_list = [beam_obj for beam_obj in beam_list if beam_obj is not None]
            # ボスダメージ判定
            for atari in ataris:
                for b, beam_obj in enumerate(beam_list):
                    if beam_obj.rct.colliderect(atari.rct): 
                        boss.hidan()
                        beam_list[b] = None
                        beam_list = [beam_obj for beam_obj in beam_list if beam_obj is not None]


        # 被弾判定
        for bomb2 in bomb2s:
            if bird.rct.colliderect(bomb2.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        # ボス衝突
        for atari in ataris:
            if bird.rct.colliderect(atari.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        # 雑魚衝突    
        for zako in zakos:
            if bird.rct.colliderect(zako.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        
        if boss != None: # ボス
            if boss.update(screen, bird, bird):
                if phase == 3:
                # カマキャン撃破
                    boss = None
                    ataris = []
                    zakos = []
                    beam.list = []
                    bomb2s = []
                    gekiha = Gekiha(0)
                    phase = 4
                    maku_img = pg.Surface((WIDTH,HEIGHT))
                    pg.draw.rect(maku_img, "#000000", (0,0,WIDTH,HEIGHT))
                    font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
                    txt = font.render(f"蒲田キャンパス消滅！！！", 0, (255, 255, 255))
                else:
                # 不死身の伏見撃破
                    boss = None
                    ataris = []
                    zakos = []
                    beam.list = []
                    bomb2s = []
                    gekiha = Gekiha(1)
                    phase = 9

        # 画面の範囲外に出たらリストから削除する
        for beam_obj in beam_list:
            beam_obj.update(screen)
            if check_bound(beam_obj.rct) != (True, True):
                beam_list.remove(beam_obj)
        
        if gekiha is not None:
            if gekiha.update(screen):
                gekiha = None 
                phase += 1

        new_explosion_list = []
        for explosion in explosion_list:
            if explosion.life > 0:
                new_explosion_list.append(explosion)
            explosion.update(screen)
        explosion_list = new_explosion_list

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        score.update(game_score, screen)
        for bomb in bombs:
            bomb.update(screen)
        for bomb2 in bomb2s:
            if bomb2.update(screen):
                bomb2s.remove(bomb2)
        for zako in zakos:
            if zako.update(screen, bird, bird):
                explosion = Explosion(zako.rct.center, 15)
                explosion_list.append(explosion)
                zako_count += 1
                zakos.remove(zako)
            if check_bound(zako.rct, 50, 50) != (True, True):
                zakos.remove(zako)
                    
        # 当たり判定視覚化
        # for atari in ataris:
        #     atari.update(screen)

        #  独自の機能：ゲームクリアを表示
        # if game_score == NUM_OF_BOMBS:
        #     game_clear.update(screen)
        #     pg.display.update()
        #     time.sleep(3)
        #     return
        
        if phase == 1 and zako_count >= 5:
            zakos = []
            beam.list = []
            bomb2s = []
            maku_img = pg.Surface((WIDTH,HEIGHT))
            pg.draw.rect(maku_img, "#000000", (0,0,WIDTH,HEIGHT))
            font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
            txt = font.render(f"蒲田キャンパスにカチコミだ！！！", 0, (255, 255, 255))
            bird.rct.center = (200, 200) # 工科トン座標変更
            phase = 2
        if phase == 2:
            screen.blit(maku_img, (0,0))
            screen.blit(txt, [WIDTH//2-300, HEIGHT//2-20])
            pg.display.update()
            phase_count += 1
            if phase_count > 200:
                phase_count = 0
                boss = Boss()
                phase = 3
        if phase == 5:
            screen.blit(maku_img, (0,0))
            screen.blit(txt, [WIDTH//2-220, HEIGHT//2-20])
            pg.display.update()
            phase_count += 1
            if phase_count > 200:
                phase_count = 0
                maku_img = pg.Surface((WIDTH,HEIGHT))
                pg.draw.rect(maku_img, "#000000", (0,0,WIDTH,HEIGHT))
                font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
                txt = font.render(f"黒幕???「あなた達は本当によく働いてくれました」", 0, (255, 255, 255))
                phase = 6
        if phase == 6:
            screen.blit(maku_img, (0,0))
            screen.blit(txt, [WIDTH//2-450, HEIGHT//2-20])
            pg.display.update()
            phase_count += 1
            if phase_count > 400:
                phase_count = 0
                beam_list = []
                boss = Boss2()
                phase = 7
        if phase == 7:
            phase_count += 1
            beam_list = []
            if phase_count > 350:
                phase_count = 0
                phase = 8

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
