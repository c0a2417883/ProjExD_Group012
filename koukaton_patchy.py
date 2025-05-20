import os
import random
import math
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
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
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.img = __class__.imgs[tuple(sum_mv)]
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
            self.rct.move_ip(self.vx, self.vy)
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
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 不要な変数を使うときは_で表す
    score = Score()
    game_score = 0
    beam_list = []
    explosion_list = []
    game_clear = Gameclear()
    clock = pg.time.Clock()
    beam = None                                 
    tmr = 0
    while True:
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
                    
        
        # 画面の範囲外に出たらリストから削除する
        for beam_obj in beam_list:
            beam_obj.update(screen)
            if check_bound(beam_obj.rct) != (True, True):
                beam_list.remove(beam_obj)
        
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

        #  独自の機能：ゲームクリアを表示
        if game_score == NUM_OF_BOMBS:
            game_clear.update(screen)
            pg.display.update()
            time.sleep(3)
            return

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
