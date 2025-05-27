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
    
    game_clear = Gameclear()
    clock = pg.time.Clock()
    beam = None                                 
    tmr = 0
    
    
    pg.mixer.init()
    pg.mixer.music.load("fig/bgm.mp3")
    pg.mixer.music.play(-1)
    shot = pg.mixer.Sound("fig/shot.mp3")
    clear = pg.mixer.Sound("fig/clear.mp3")
    gameover = pg.mixer.Sound("fig/gameover.mp3")
    crash = pg.mixer.Sound("fig/crash.mp3")
    
    
    while True:
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
        life.update(life.life, screen)
        for bomb in bombs:
            bomb.update(screen)
        
        #  ゲームクリアを表示
        if game_score == NUM_OF_BOMBS:
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

        pg.display.update()
        tmr += 1
        clock.tick(50)
        bird.update(key_lst,screen)
        
        

if __name__ == "__main__":
    pg.init()
    while True:
        main()
    pg.quit()
    sys.exit()
