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


class Background:
    def __init__(self,image_paths:str,scale:int) ->list[str,str,str,str]:
        """
        引数1 背景画像のリスト
        引数2 画像の拡大、縮小の値
        for文でpathを指定して、空リストに加える
        """
        self.bg_imgs=[]
        for path in image_paths:
            self.img = pg.transform.rotozoom(pg.image.load(f"fig/{path}.jpg"), 0, scale)#パスを指定して画像surfaceを生成する
            self.bg_imgs.append(self.img)#空リストに追加
        self.bg_width=self.bg_imgs[0].get_width()#画像の横幅のピクセル数を求めている
        # self.x=0
    def update(self,tmr:int) -> int:
        """
        引数1 tmr(int型)
        画像の大きさを求めて、ｘ座標を求める
        """
        total_width = self.bg_width*len(self.bg_imgs)#背景画像を横に連続で表示したときの合計の横幅を示している。
        self.x = tmr%total_width
        
    def draw(self,screen:pg.Surface):
        """
        引数1 screen (pg.Surface型)
        背景を描画する
        """
        for i in range(len(self.bg_imgs) + 1):  
            img = self.bg_imgs[i % len(self.bg_imgs)]
            screen.blit(img, (-self.x + i * self.bg_width, 0))
            
      
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
        if bird is None:
            bird = pat
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
                self.kao_part(0,1,[self.centerx, self.centery], screen, bird, bird)
            elif self.motion_life % 50 >= 15 and self.motion_life % 50 <= 25:
                self.kao_part(0,1,[self.centerx, self.centery], screen, bird, bird)
            else:
                self.kao_part(0,0,[self.centerx, self.centery], screen, bird, bird)
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
                self.kao_part(1,2,[self.nobix, self.centery - self.nobiy], screen, bird, bird)
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
                self.kao_part(1,2,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, bird, True)
            # 止まる
            elif self.motion_life >= 108 and self.motion_life <= 400:
                for nobi in self.nobis:
                    nobi.update(screen)
                if self.motion_life % 50 == 20:
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, 0))
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, 45))
                    bomb2s.append(Bomb2((0, 255, 255), [60, 60], [self.nobix + 70, self.nobis[-1].rct.centery], bird, bird, 1, 5, 0, -45))
                    self.kao_part(0,1,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, bird, True)
                elif self.motion_life % 50 >= 15 and self.motion_life % 50 <= 25:
                    self.kao_part(0,1,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, bird, True)
                else:
                    self.kao_part(0,0,[self.nobix + 70, self.nobis[-1].rct.centery + 50], screen, bird, bird, True)
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
                    self.kao_part(1,2,[self.centerx, self.centery], screen, bird, bird)
                else:
                    for nobi in self.nobis:
                        nobi.update(screen)
                    if self.nobis[-1].hanten == True:
                        self.kao_part(1,2,[self.nobis[-1].rct.centerx + 70, self.nobis[-1].rct.centery + 50], screen, bird, bird, True)
                    else:
                        self.kao_part(1,2,[self.centerx, self.nobis[-1].rct.centery-30], screen, bird, bird)
            else:
                for nobi in self.nobis:
                    nobi.update(screen)
                self.kao_part(1,2,[self.nobix, self.centery - self.nobiy], screen, bird, bird)
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
            self.kao_part(1,2,[self.centerx,self.centery+self.vz], screen, bird, bird)
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
        if bird == None:
            bird = pat
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
        self.img = self.font.render(f"Score：{score}", 0, (0, 0, 255))
        self.rct = self.img.get_rect()
        self.score = score
        self.rct.center = (100, HEIGHT-50)

    def update(self, num: int, screen: pg.Surface):
        """
        現在のスコアを表示させる文字列Surfaceの生成
        スクリーンにblit
        """
        self.score = num
        self.img = self.font.render(f"Score：{num}", 0, (0, 0, 255))
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
        self.gameclear_sur = pg.Surface((WIDTH, HEIGHT))
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 60)
        self.koukaton = pg.image.load("fig/2.png") 
        self.koukaton2 = pg.image.load("fig/5.png") 
        self.gameclear_txt = self.font.render("GAME CLEAR !!!",True,(255, 255, 0))
        self.gameclear_sur.set_alpha(130)
        pg.draw.rect(self.gameclear_sur, (0, 0, 0), pg.Rect(0, 0, WIDTH, HEIGHT))
    
    def update(self, screen: pg.Surface):
        """
        ゲームクリアの文字とこうかとんを表示
        """
        screen.blit(self.gameclear_sur, [0, 0])
        screen.blit(self.gameclear_txt, [330, 300])
        screen.blit(self.koukaton, [261, 290])
        screen.blit(self.koukaton2, [763, 292])

class Startmenu:
    """
    スタート画面を表示
    """
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.startmenu = pg.image.load("fig/pg_bg.jpg")
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 60)
        self.kamata = pg.image.load("fig/kamato_0.png") 
        self.patchy = pg.image.load("fig/patti_0.png")
        self.title_text = self.font.render("蒲田の逆襲",True,(0, 0, 255))
        self.startmenu.set_alpha(130)
        self.title_text.set_alpha(150)
        self.start_text = self.font.render("Press SPACE to Start", True, (0, 0, 255))
        self.title_rect = self.title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))
        self.start_rect = self.start_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        pg.mixer.init()
        pg.mixer.music.load("fig/title.mp3") #  BGM
        pg.mixer.music.play(-1) #  ループ再生
        pg.mixer.music.set_volume(0.25) #  音量調整

    
    def run(self, screen: pg.Surface) -> bool:  # Trueを返したらゲーム開始
        """
        ゲームクリアの文字とこうかとんを表示
        """
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False  # ゲーム終了
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        return True  # ゲーム開始

            screen.blit(self.startmenu, [0, 0])
            screen.blit(self.title_text, self.title_rect)
            screen.blit(self.kamata, [100, 290])
            screen.blit(self.patchy, [763, 292]) 
            screen.blit(self.start_text, self.start_rect) 
            pg.display.update()
            time.sleep(0.01)
        return False
    

class Recovery:
    """
    回復アイテムに関するクラス
    """
    imgs = [pg.image.load("fig/food_oden_tamago_0.png"), pg.image.load("fig/sweets_manjyu_0.png")]

    def __init__(self):
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.1)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.interval = random.randint(50, 300)  # インターバル

    def update(self, screen: pg.Surface):
        if self.rect.centery > self.bound:
            self.vy = 0
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)


class Life:
    """
    ライフを表示させるクラス
    """
    def __init__(self):
        """
        ライフのフォントや色の設定．文字列Surfaceの生成を行う
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.life = 5
        self.img = pg.transform.rotozoom(pg.image.load("fig/heart.png"), 0, 0.04)
        self.heart_width = self.img.get_width()
        self.heart_height = self.img.get_height()

        self.max_life = 5 # 最大ライフ数を定義（ゲーム内で増える可能性があれば変更）
        self.padding_right = 20 # 画面右端からの余白
        self.heart_spacing = 3 # ハート間のスペース
        self.base_start_x = WIDTH - (self.heart_width * self.max_life + self.heart_spacing * (self.max_life - 1)) - self.padding_right
        self.start_y = HEIGHT - 50
        self.start_x = self.base_start_x - 5 
        self.start_y = self.start_y - 5

    def update(self, num: int, screen: pg.Surface):
        """
        現在のライフを表示させる文字列Surfaceの生成
        スクリーンにblit
        """
        self.life = num
        clear_rect = pg.Rect(self.start_x, self.start_y, self.heart_width * 3 + 20, self.heart_height) # 最大ライフ数分の幅
        screen.blit(pg.image.load("fig/pg_bg.jpg"), clear_rect, area=clear_rect) # 背景画像で上書き
        for i in range(self.life):
            # 各ハートの表示位置を計算
            x = (WIDTH - self.padding_right) - ((self.life - i) * (self.heart_width + self.heart_spacing)) + self.heart_spacing # 右端から逆算
            y = self.start_y
            screen.blit(self.img, (x, y))    

class Pachi:
    """
    二人目のキャラクター “pachi” クラス
    W: ジャンプ, A: 左移動, D: 右移動
    ジャンプ: スーパーマリオ風の重力処理付き
    Space: ビーム攻撃用の PachiBeam クラスを利用
    """
    def __init__(self, xy: tuple[int,int]):
        # 画像の読み込み: 立ちポーズと歩きポーズ2種
        self.img_stand_right = pg.transform.rotozoom(pg.image.load("fig/pachi_stand.png"), 0, 0.9)
        self.img_walk1_right = pg.transform.rotozoom(pg.image.load("fig/pachi_walk1.png"), 0, 0.9)
        self.img_walk2_right = pg.transform.rotozoom(pg.image.load("fig/pachi_walk2.png"), 0, 0.9)
        # 左向きイメージを生成
        self.img_stand_left  = pg.transform.flip(self.img_stand_right, True, False)
        self.img_walk1_left  = pg.transform.flip(self.img_walk1_right, True, False)
        self.img_walk2_left  = pg.transform.flip(self.img_walk2_right, True, False)
        # 初期状態
        self.img           = self.img_stand_right
        self.walk_toggle   = False  # 歩行アニメ切替フラグ
        self.walk_timer    = 0      # フレームカウンタ
        self.facing_right  = True
        self.dire          = (5, 0)
        # 位置・重力関連
        self.rct           = self.img.get_rect(center=xy)
        self.vy            = 0
        self.on_ground     = True

    def update(self, key_lst: list[bool], screen: pg.Surface):
        dx = 0
        # 左右移動
        if key_lst[pg.K_a]:
            dx = -5
            self.facing_right = False
        elif key_lst[pg.K_d]:
            dx = +5
            self.facing_right = True
        # 歩行アニメ: 1秒ごとに切り替え (50fps想定)
        if dx != 0 and self.on_ground:
            self.walk_timer += 1
            if self.walk_timer >= 10:
                self.walk_toggle = not self.walk_toggle
                self.walk_timer = 0
            if self.facing_right:
                self.img = self.img_walk1_right if self.walk_toggle else self.img_walk2_right
            else:
                self.img = self.img_walk1_left  if self.walk_toggle else self.img_walk2_left
        # 停止中の立ちポーズ
        elif self.on_ground:
            self.img = self.img_stand_right if self.facing_right else self.img_stand_left
        # ジャンプ開始
        if key_lst[pg.K_w] and self.on_ground:
            self.vy        = -15
            self.on_ground = False
        # 重力適用・移動
        self.vy += 1
        self.rct.y += self.vy
        self.rct.x += dx
        # 地面(底辺)でリセット
        if self.rct.bottom >= 480:
            self.rct.bottom = 480
            self.vy          = 0
            self.on_ground   = True
        # 画面端制限
        self.rct.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))
        # 方向ベクトル更新
        if dx != 0:
            self.dire = (dx, 0)
        # 描画
        screen.blit(self.img, self.rct)

class PachiBeam(Beam):
    """
    Pachi用ビーム: 生成位置をPachiの向きに合わせる
    """
    def __init__(self, pachi: Pachi):
        # 画像・向き
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        # 速度ベクトルはPachi.dire
        self.vx, self.vy = pachi.dire
        # 回転角度計算
        tan = math.atan2(-self.vy, self.vx)
        angle = math.degrees(tan)
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)
        # 発射位置: キャラ中心から向きに応じてオフセット
        offset_x = (pachi.rct.width  * (self.vx / 5))
        offset_y = (pachi.rct.height * (self.vy / 5))
        self.rct.centerx = pachi.rct.centerx + offset_x
        self.rct.centery = pachi.rct.centery + offset_y

    def update(self, screen: pg.Surface):
        # 画面内なら移動と描画
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("蒲田の逆襲")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    imgs_path=["honbu2","kenkyu2","kataken2","kougiD"]#背景画像の名前のリスト
    scroller=Background(imgs_path,0.75)#バックグラウンド関数にリストと縮小値の0.75を入れている
    start_menu = Startmenu(WIDTH, HEIGHT)
    if not start_menu.run(screen):
        return
    bird = None
    bombs = []
    score = None
    life = None
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    pachi = Pachi((300, 480))
    screen = pg.display.set_mode((WIDTH, HEIGHT))   
    # bg_img = pg.image.load("fig/pg_bg.jpg")
    # bird = Bird((300, 200))
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
    explosion_list = []
    recovery_items = []
    tmr = 0
    invincible = False
    invincible_timer = 0

    # リスタート処理
    def reset_game():
        nonlocal bird, bombs, score, life, game_score, beam_list, explosion_list, recovery_items, tmr, invincible, invincible_timer
        bird = Bird((300, 200))
        bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 不要な変数を使うときは_で表す
        score = Score()
        life = Life()
        game_score = 0
        beam_list = []
        explosion_list = []
        recovery_items = [] 
        invincible = False  # 無敵状態かどうか
        invincible_timer = 0  # 無敵時間のカウント
    reset_game()
    
    # global explosion_list
    game_clear = Gameclear()
    clock = pg.time.Clock()
    beam = None         
    gekiha = None
    phase = 1
    phase_count = 0              
    tmr = 0
    
    
    pg.mixer.init()
    pg.mixer.music.load("fig/bgm.mp3")
    pg.mixer.music.play(-1)
    shot = pg.mixer.Sound("fig/shot.mp3")
    clear = pg.mixer.Sound("fig/clear.mp3")
    gameover = pg.mixer.Sound("fig/gameover.mp3")
    crash = pg.mixer.Sound("fig/crash.mp3")
    
    
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
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                # RETURNキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
                beam_list.append(beam)
                shot.play()        
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = PachiBeam(pachi)
                beam_list.append(PachiBeam(pachi))
                beam_list.append(beam)
                shot.play()
        scroller.update(tmr)
        scroller.draw(screen)    
        # screen.blit(bg_img, [0, 0])
        if beam_list is not None:
            for bomb in bombs:
                if beam_list is not None:
                    if not invincible and (bird.rct.colliderect(bomb.rct) or pachi.rct.colliderect(bomb.rct)):  # 爆弾とこうかとん/ぱっちぃの衝突判定
                        life.life -= 1
                        invincible = True
                        invincible_timer = 50  # 無敵時間
                        
            if life.life <= 0:
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                base = pachi.img_stand_right if pachi.facing_right else pachi.img_stand_left  # Pachi倒れ絵: 立ちポーズを90度回転
                fallen = pg.transform.rotozoom(base, 90, 1.0)
                screen.blit(fallen, pachi.rct)
                gameover_surface = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
                gameover_surface.fill((0, 0, 0, 150))
                fonto = pg.font.Font(None, 120)
                txt = fonto.render("GAME OVER", True, (255, 255, 255))
                
                pg.mixer.music.pause() #  BGM止める
                gameover.play() #  ゲームオーバー音
                
                # リトライボタンのテキストと矩形を作成
                retry_font = pg.font.Font(None, 60) # ボタン用のフォントサイズ
                retry_text = retry_font.render("RETRY", True, (255, 255, 255)) # 白い文字
                retry_rect = retry_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)) # Game Overの下に配置
                screen.blit(gameover_surface, (0, 0)) # 半透明の黒い背景を画面全体に描画
                screen.blit(txt, [WIDTH//2 - txt.get_width()//2, HEIGHT//2 - txt.get_height()//2])
                screen.blit(retry_text, retry_rect)
                pg.display.update()
                while True: # 新しいループに入る
                    for event in pg.event.get():
                        if event.type == pg.QUIT:
                            return
                        if event.type == pg.MOUSEBUTTONDOWN: # マウスクリックイベント
                            if retry_rect.collidepoint(event.pos): # クリック位置がリトライボタン内か判定
                                reset_game() # ゲームをリセット
                                return
                    time.sleep(0.01)

            for i, bomb in enumerate(bombs):
                for b, beam_obj in enumerate(beam_list):
                    if beam_obj.rct.colliderect(bomb.rct):
                        # 爆弾とビームが衝突した際にBeamインスタンス，Bombインスタンスを消滅
                        crash.play() #  爆発音
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
            if beam_list !=[]:
                for atari in ataris:
                    for b, beam_obj in enumerate(beam_list):
                        if beam_obj.rct.colliderect(atari.rct): 
                            boss.hidan()
                            beam_list[b] = None
                            beam_list = [beam_obj for beam_obj in beam_list if beam_obj is not None]


        # 被弾判定
        for bomb2 in bomb2s:
            if bird.rct.colliderect(bomb2.rct):
                # # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                # bird.change_img(8, screen)
                # fonto = pg.font.Font(None, 80)
                # txt = fonto.render("Game Over", True, (255, 0, 0))
                # screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                # pg.display.update()
                # time.sleep(1)
                # return
                life.life -= 1
                invincible = True
                invincible_timer = 400  # 無敵時間
        # ボス衝突
        for atari in ataris:
            if bird.rct.colliderect(atari.rct):
                # # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                # bird.change_img(8, screen)
                # fonto = pg.font.Font(None, 80)
                # txt = fonto.render("Game Over", True, (255, 0, 0))
                # screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                # pg.display.update()
                # time.sleep(1)
                # return
                life.life -= 1
                invincible = True
                invincible_timer = 400  # 無敵時間
        # 雑魚衝突    
        for zako in zakos:
            if bird.rct.colliderect(zako.rct):
                # # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                # bird.change_img(8, screen)
                # fonto = pg.font.Font(None, 80)
                # txt = fonto.render("Game Over", True, (255, 0, 0))
                # screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                # pg.display.update()
                # time.sleep(1)
                # return
                life.life -= 1
                invincible = True
                invincible_timer = 400  # 無敵時間
        
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
        pachi.update(key_lst, screen)
        score.update(game_score, screen)
        life.update(life.life, screen)
        for bomb in bombs:
            bomb.update(screen)
        
        #  ゲームクリアを表示
        if phase == 9:
            pg.mixer.music.pause() #  BGM止める
            clear.play() #  クリア音
            game_clear.update(screen)
            pg.display.update()
            time.sleep(3)
            return
        
        # 回復アイテム
        if tmr % 400 == 0: 
            recovery_items.append(Recovery())

        new_recovery_items = []
        for recovery in recovery_items:
            recovery.update(screen) # 描画のためにscreenを渡す
            if bird.rct.colliderect(recovery.rect):
                life.life += 1
            else:
                new_recovery_items.append(recovery) # 衝突がない場合は保持
        recovery_items = new_recovery_items    

        if invincible:
            invincible_timer -= 1
            if invincible_timer <= 0:
                invincible = False
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
            # beam.list = []
            bomb2s = []
            maku_img = pg.Surface((WIDTH,HEIGHT))
            pg.draw.rect(maku_img, "#000000", (0,0,WIDTH,HEIGHT))
            font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 40)
            txt = font.render(f"蒲田キャンパスにカチコミだ！！！", 0, (255, 255, 255))
            if bird != None:    
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
        bird.update(key_lst,screen)
        
        

if __name__ == "__main__":
    pg.init()
    # while True:
    main()
    pg.quit()
    sys.exit()
