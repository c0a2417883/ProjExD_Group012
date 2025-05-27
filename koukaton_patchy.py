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
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    pachi = Pachi((300, 480))
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
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)
                beam_list.append(beam)        
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beam_list.append(PachiBeam(pachi))

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
                if pachi.rct.colliderect(bomb.rct):
                # Pachi倒れ絵: 立ちポーズを90度回転
                    base = pachi.img_stand_right if pachi.facing_right else pachi.img_stand_left
                    fallen = pg.transform.rotozoom(base, 90, 1.0)
                    screen.blit(fallen, pachi.rct)
                    fonto = pg.font.Font(None,80)
                    txt   = fonto.render("Game Over",True,(255,0,0))
                    screen.blit(txt,[WIDTH//2-150,HEIGHT//2])
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
        pachi.update(key_lst, screen)
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
