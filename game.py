# -*- coding: utf-8 -*-
import pgzrun
import random
from pygame import Rect

# Tamanho da janela do jogo
WIDTH, HEIGHT = 800, 600

# Definição dos estados do jogo
STATE_MENU, STATE_PLAYING, STATE_GAMEOVER, STATE_WIN = "menu", "playing", "gameover", "win"
game_state = STATE_MENU  # Estado inicial

# Controle do som
sound_on = True

# --- Funções do Menu ---
def start_game():
    """Inicia o jogo, reseta o nível e troca o estado para 'jogando'."""
    global game_state
    reset_level()
    game_state = STATE_PLAYING
    if sound_on:
        try:
            sounds.music.play(-1)  # Toca música em loop
        except:
            pass

def toggle_sound():
    """Liga ou desliga o som."""
    global sound_on
    sound_on = not sound_on
    try:
        if sound_on:
            sounds.music.play(-1)
        else:
            sounds.music.stop()
    except:
        pass

def exit_game():
    """Fecha o jogo."""
    raise SystemExit

# Botões do menu principal
menu_buttons = [
    {"text": "INICIAR",    "rect": Rect(300, 200, 200, 50), "action": start_game},
    {"text": "SOM ON/OFF", "rect": Rect(300, 280, 200, 50), "action": toggle_sound},
    {"text": "SAÍDA",      "rect": Rect(300, 360, 200, 50), "action": exit_game},
]

# --- Configuração de plataformas ---
PLATFORM_W, PLATFORM_H = 128, 48  # Tamanho das plataformas
platforms = []  # Lista de plataformas no cenário

# Tamanho do sprite do jogador
PLAYER_W = images.player_idle_right1.get_width()
PLAYER_H = images.player_idle_right1.get_height()

# Ajuste para evitar que o jogador "treme" sobre a plataforma
LAND_GAP = -5

# Pontuação e altura da última plataforma tocada
score = 0
last_land_y = None

# --- Bandeira (objetivo final) ---
flag_rect = None  # Retângulo de colisão da bandeira

# --- Classe do Jogador ---
class Player:
    def __init__(self, pos):
        """Inicializa o jogador com posição, física e animações."""
        self.x, self.y = pos
        self.vx, self.vy = 0, 0
        self.last_dir = "right"  # Última direção (para animação)
        self.frame = 0.0  # Controle de animação

        # Animações
        self.anim_idle_r = ["player_idle_right1", "player_idle_right2"]
        self.anim_idle_l = ["player_idle_left1",  "player_idle_left2"]
        self.anim_run_r  = ["player_run_right1", "player_run_right2", "player_run_right3", "player_run_right4"]
        self.anim_run_l  = ["player_run_left1",  "player_run_left2",  "player_run_left3",  "player_run_left4"]
        self.image = self.anim_idle_r[0]

        # Hitbox (menor que a imagem para evitar colisões falsas)
        self.hb_dx, self.hb_dy = 6, 2
        self.hb_w, self.hb_h = PLAYER_W - 2*self.hb_dx, PLAYER_H - self.hb_dy - 2
        self.hitbox = Rect(self.x + self.hb_dx, self.y + self.hb_dy, self.hb_w, self.hb_h)

        # Controle de pulo duplo
        self.max_jumps = 2
        self.jumps_left = self.max_jumps
        self.space_held = False  # Evita pulo contínuo

    def _jump(self):
        """Executa um pulo se ainda houver pulos disponíveis."""
        if self.jumps_left > 0:
            self.vy = -8
            self.jumps_left -= 1
            try:
                if sound_on:
                    sounds.jump.play()
            except:
                pass

    def handle_input(self):
        """Lê o teclado e ajusta a movimentação do jogador."""
        self.vx = 0
        if keyboard.left:
            self.vx = -3
            self.last_dir = "left"
        if keyboard.right:
            self.vx = 3
            self.last_dir = "right"

        # Pulo com detecção de "borda" da tecla
        if keyboard.space and not self.space_held:
            self._jump()
            self.space_held = True
        elif not keyboard.space:
            self.space_held = False

    def physics(self):
        """Atualiza a física do jogador (gravidade, colisões e objetivos)."""
        global score, last_land_y, game_state

        # Movimento horizontal e vertical
        self.x += self.vx
        self.vy += 0.35  # Gravidade
        self.y += self.vy

        # Atualiza posição da hitbox
        self.hitbox.topleft = (self.x + self.hb_dx, self.y + self.hb_dy)

        # Colisão com plataformas (apenas por cima)
        landed = False
        landed_top = None
        if self.vy >= 0:
            for p in platforms:
                if self.hitbox.colliderect(p):
                    pen = self.hitbox.bottom - p.top
                    if 0 <= pen < 20:
                        self.y = p.top - PLAYER_H - LAND_GAP
                        self.vy = 0
                        landed = True
                        landed_top = p.top
                        self.jumps_left = self.max_jumps
                        self.hitbox.topleft = (self.x + self.hb_dx, self.y + self.hb_dy)
                        break

        # Pontuação por subir mais alto
        if landed:
            if (last_land_y is None) or (landed_top < last_land_y - 5):
                score += 1
                last_land_y = landed_top

        # Colisão com bandeira → vitória
        if flag_rect and self.hitbox.colliderect(flag_rect):
            game_win()

        # Caiu fora da tela → game over
        if self.y > HEIGHT + 60:
            game_over()

    def animate(self):
        """Controla a animação do jogador."""
        self.frame += 0.15
        moving = self.vx != 0
        if moving:
            if self.vx > 0:
                self.image = self.anim_run_r[int(self.frame) % len(self.anim_run_r)]
            else:
                self.image = self.anim_run_l[int(self.frame) % len(self.anim_run_l)]
        else:
            if self.last_dir == "right":
                self.image = self.anim_idle_r[int(self.frame) % len(self.anim_idle_r)]
            else:
                self.image = self.anim_idle_l[int(self.frame) % len(self.anim_idle_l)]

    def update(self):
        """Atualiza o jogador (entrada + física + animação)."""
        self.handle_input()
        self.physics()
        self.animate()

    def draw(self):
        """Desenha o jogador na tela."""
        screen.blit(self.image, (self.x, self.y))

# --- Classe dos inimigos ---
class Enemy:
    def __init__(self, platform, speed=1):
        """Inimigo que patrulha sobre uma plataforma."""
        self.platform = platform
        self.w, self.h = 36, 36
        self.x = random.randint(platform.left, platform.right - self.w)
        self.y = platform.top - self.h
        self.dir = random.choice([-1, 1])
        self.speed = speed
        self.frame = 0.0
        self.walk_r = ["enemy_walk_right1", "enemy_walk_right2"]
        self.walk_l = ["enemy_walk_left1",  "enemy_walk_left2"]
        self.image = self.walk_r[0]
        self.hitbox = Rect(self.x, self.y, self.w, self.h)

    def update(self):
        """Movimento e animação do inimigo."""
        self.x += self.dir * self.speed
        if self.x < self.platform.left:
            self.x = self.platform.left; self.dir = 1
        if self.x > self.platform.right - self.w:
            self.x = self.platform.right - self.w; self.dir = -1
        self.y = self.platform.top - self.h

        self.frame += 0.12
        anim = self.walk_r if self.dir >= 0 else self.walk_l
        self.image = anim[int(self.frame) % len(anim)]

        self.hitbox.topleft = (self.x, self.y)

    def draw(self):
        """Desenha o inimigo."""
        screen.blit(self.image, (self.x, self.y))

# Entidades globais
player = None
enemies = []

# --- Reset do nível ---
def reset_level():
    """Cria plataformas, jogador, inimigos e a bandeira final."""
    global platforms, player, enemies, score, last_land_y, flag_rect
    score, last_land_y = 0, None

    # Plataformas fixas
    platforms = [
        Rect(60,  HEIGHT - 64, PLATFORM_W, PLATFORM_H),
        Rect(260, HEIGHT - 140, PLATFORM_W, PLATFORM_H),
        Rect(470, HEIGHT - 220, PLATFORM_W, PLATFORM_H),
        Rect(120, HEIGHT - 300, PLATFORM_W, PLATFORM_H),
        Rect(350, HEIGHT - 380, PLATFORM_W, PLATFORM_H),  # Última plataforma
    ]

    # Jogador na primeira plataforma
    player = Player((platforms[0].left + 30, platforms[0].top - PLAYER_H - LAND_GAP))

    # Inimigos (não colocamos na primeira plataforma)
    enemies = [
        Enemy(platforms[1], speed=1),
        Enemy(platforms[2], speed=1),
        Enemy(platforms[3], speed=1),
    ]

    # Bandeira na última plataforma
    flag_img = images.flag
    fw, fh = flag_img.get_width(), flag_img.get_height()
    flag_x = platforms[-1].centerx - fw // 2
    flag_y = platforms[-1].top - fh
    flag_rect = Rect(flag_x, flag_y, fw, fh)

# --- Fim de jogo ---
def game_over():
    """Troca o estado para 'game over'."""
    global game_state
    game_state = STATE_GAMEOVER
    try:
        sounds.music.stop()
    except:
        pass
    try:
        sounds.coin.play()
    except:
        pass

# --- Vitória ---
def game_win():
    """Troca o estado para 'vitória'."""
    global game_state
    game_state = STATE_WIN
    try:
        sounds.music.stop()
    except:
        pass
    try:
        sounds.coin.play()
    except:
        pass

# --- Loop de atualização ---
def update():
    """Atualiza todos os elementos do jogo."""
    if game_state == STATE_PLAYING:
        player.update()
        for e in enemies:
            e.update()
        # Colisão jogador ↔ inimigos
        for e in enemies:
            if player.hitbox.colliderect(e.hitbox):
                game_over()
                break

# --- Desenho na tela ---
def draw():
    """Desenha todos os elementos conforme o estado do jogo."""
    screen.clear()
    
    if game_state == STATE_MENU:
        # Fundo e título
        screen.blit("background", (0, 0))
        for p in platforms or []:
            screen.blit("platform", (p.left, p.top))
        screen.draw.text("JUNGLE RUNNER", center=(WIDTH//2, 120), fontsize=56, color="yellow", owidth=1, ocolor="black")
        # Botões do menu
        for btn in menu_buttons:
            screen.draw.filled_rect(btn["rect"], (90, 50, 0))
            screen.draw.text(btn["text"], center=btn["rect"].center, fontsize=28, color="white")

    elif game_state == STATE_PLAYING:
        # Cenário, bandeira, jogador e inimigos
        screen.blit("background", (0, 0))
        for p in platforms:
            screen.blit("platform", (p.left, p.top))
        if flag_rect:
            screen.blit("flag", flag_rect.topleft)
        player.draw()
        for e in enemies:
            e.draw()
        # Placar
        screen.draw.text(f"Score: {score}", topleft=(10, 10), fontsize=32, color="white", owidth=1, ocolor="black")

    elif game_state == STATE_GAMEOVER:
        # Mostra cenário congelado e tela de "Game Over"
        screen.blit("background", (0, 0))
        for p in platforms:
            screen.blit("platform", (p.left, p.top))
        if flag_rect:
            screen.blit("flag", flag_rect.topleft)
        player.draw()
        for e in enemies:
            e.draw()
        # Tela preta translúcida
        screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0, 150))
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 50), fontsize=60, color="red")
        screen.draw.text("Press R to Restart", center=(WIDTH//2, HEIGHT//2 + 10), fontsize=36, color="white")
        screen.draw.text("Press M for Menu", center=(WIDTH//2, HEIGHT//2 + 50), fontsize=36, color="white")
        screen.draw.text(f"Final Score: {score}", center=(WIDTH//2, HEIGHT//2 + 90), fontsize=36, color="yellow")

    elif game_state == STATE_WIN:
        # Mostra cenário congelado e tela de "Vitória"
        screen.blit("background", (0, 0))
        for p in platforms:
            screen.blit("platform", (p.left, p.top))
        if flag_rect:
            screen.blit("flag", flag_rect.topleft)
        player.draw()
        for e in enemies:
            e.draw()
        # Tela preta translúcida
        screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0, 150))
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH//2, HEIGHT//2 - 50), fontsize=60, color="green")
        screen.draw.text("Press R to Restart", center=(WIDTH//2, HEIGHT//2 + 10), fontsize=36, color="white")
        screen.draw.text("Press M for Menu", center=(WIDTH//2, HEIGHT//2 + 50), fontsize=36, color="white")
        screen.draw.text(f"Final Score: {score}", center=(WIDTH//2, HEIGHT//2 + 90), fontsize=36, color="yellow")

# --- Controles do mouse ---
def on_mouse_down(pos):
    """Detecta cliques nos botões do menu."""
    if game_state == STATE_MENU:
        for btn in menu_buttons:
            if btn["rect"].collidepoint(pos):
                btn["action"]()

# --- Controles do teclado ---
def on_key_down(key):
    """Detecta teclas para reiniciar ou voltar ao menu."""
    global game_state
    if game_state in (STATE_GAMEOVER, STATE_WIN):
        if key == keys.R:
            start_game()
        elif key == keys.M:
            game_state = STATE_MENU

# Inicia o jogo
pgzrun.go()
