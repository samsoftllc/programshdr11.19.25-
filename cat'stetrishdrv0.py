import pygame
import random
import sys
import numpy as np

# ============================================================
# ULTRA!TETRIS 0.3HDR+ – KOROBEINIKI EDITION (TCRF BUILD)
# ============================================================

pygame.init()
pygame.mixer.init(44100, -16, 2, 512)

# ------------------------------------------------------------ 
# CONSTANTS & CONFIG
# ------------------------------------------------------------
SCALE = 3 # Size multiplier (Adjust if screen is too big/small)
GB_W, GB_H = 160, 144
SCREEN_WIDTH = GB_W * SCALE
SCREEN_HEIGHT = GB_H * SCALE
BLOCK_SIZE = 8 * SCALE

# Playfield dimensions
FIELD_W, FIELD_H = 10, 18
FIELD_PX_W = FIELD_W * BLOCK_SIZE
FIELD_PX_H = FIELD_H * BLOCK_SIZE
FIELD_X = (SCREEN_WIDTH - FIELD_PX_W) // 2 - (2 * SCALE) # Shifted slightly left for UI
FIELD_Y = (SCREEN_HEIGHT - FIELD_PX_H) // 2

# ------------------------------------------------------------ 
# PALETTE (GAME BOY ORIGINAL)
# ------------------------------------------------------------
# C0: Background/Lightest, C3: Text/Darkest
C0 = (155, 188, 15)  
C1 = (139, 172, 15)  
C2 = (48, 98, 48)    
C3 = (15, 56, 15)    

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ULTRA!TETRIS (Nintendo 1989 Style)")
CLOCK = pygame.time.Clock()

# ------------------------------------------------------------ 
# ASSETS (Procedural Generation - No External Files)
# ------------------------------------------------------------
try:
    # Attempt to use a retro font if available, else generic
    FONT_MAIN = pygame.font.SysFont("consolas", 10 * SCALE, bold=True)
    FONT_SMALL = pygame.font.SysFont("consolas", 8 * SCALE, bold=True)
    FONT_MINI = pygame.font.SysFont("consolas", 6 * SCALE, bold=True)
except:
    FONT_MAIN = pygame.font.SysFont("arial", 20)
    FONT_SMALL = pygame.font.SysFont("arial", 16)
    FONT_MINI = pygame.font.SysFont("arial", 12)

# ------------------------------------------------------------ 
# AUDIO ENGINE (Raw Square Wave Synthesis)
# ------------------------------------------------------------
class Synth:
    def __init__(self):
        self.cache = {}

    def gen(self, freq, dur, vol=0.3, duty=0.5):
        # Caching sounds to prevent lag
        key = (freq, dur, vol, duty)
        if key in self.cache: return self.cache[key]
        
        sr = 44100
        ns = int(sr * dur)
        if ns % 2 != 0: ns += 1
            
        # Generate Square Wave
        period = sr / max(1, freq)
        samples = np.arange(ns)
        wave = np.where((samples % period) < (period * duty), 1.0, -1.0)
        
        # Simple decay envelope
        envelope = np.linspace(1.0, 0.5, ns)
        
        audio_data = (wave * envelope * vol * 32767).astype(np.int16)
        stereo_data = np.repeat(audio_data.reshape(-1, 1), 2, axis=1)
        
        try:
            snd = pygame.sndarray.make_sound(stereo_data)
            self.cache[key] = snd
            return snd
        except: return None

synth = Synth()

# ------------------------------------------------------------ 
# MUSIC & SFX DATA
# ------------------------------------------------------------
NOTE = 0.07
E5, B4, C5, D5, A4, G4 = 659, 494, 523, 587, 440, 392
F5, G5, A5 = 698, 784, 880
E4, D4, F4, GS4 = 329, 293, 349, 415

SFX = {
    "move":   synth.gen(300, 0.05, 0.1),
    "rotate": synth.gen(400, 0.05, 0.1),
    "drop":   synth.gen(150, 0.08, 0.2),
    "line":   synth.gen(880, 0.2, 0.3),
    "tetris": synth.gen(1200, 0.4, 0.4, 0.25), # High duty cycle for "Tetris" sound
    "die":    synth.gen(80, 0.5, 0.4),
    "start":  synth.gen(600, 0.4, 0.3)
}

# TYPE A: Korobeiniki (The Classic)
track_a = [
    (E5,4),(B4,2),(C5,2),(D5,4),(C5,2),(B4,2),(A4,4),(A4,2),(C5,2),(E5,4),(D5,2),(C5,2),
    (B4,6),(C5,2),(D5,4),(E5,4),(C5,4),(A4,4),(A4,8),
    (D5,4),(F5,2),(A5,2),(G5,4),(E5,2),(C5,2),(E5,6),(C5,2),(E5,4),(D5,2),(C5,2),
    (B4,4),(B4,2),(C5,2),(D5,4),(E5,4),(C5,4),(A4,4),(A4,4)
]

# TYPE B: Troika
track_b = [
    (E5,4),(C5,2),(D5,2),(B4,4),(C5,2),(A4,2),(GS4,4),(B4,2),(E5,2),(D5,4),(C5,2),(B4,2),
    (C5,4),(E5,4),(A5,4),(G5,2),(F5,2),(E5,8),(C5,4),(E5,4),
    (D5,4),(B4,2),(C5,2),(D5,4),(C5,4),(B4,4),(A4,4),(GS4,4),(A4,8)
]

# TYPE C: Bach French Suite No. 3 (Minuet)
track_c = [
    (E5,2),(B4,2),(C5,2),(D5,2),(E5,2),(E5,2),(E5,4),
    (D5,2),(E5,2),(F5,2),(G5,2),(E5,4),(E5,4),
    (A4,2),(B4,2),(C5,2),(D5,2),(E5,2),(D5,2),(C5,2),(B4,2),(A4,8)
]

class MusicEngine:
    def __init__(self):
        self.tracks = [track_a, track_b, track_c, []]
        self.current = 0
        self.idx = 0
        self.next_tick = 0
        self.chan = pygame.mixer.Channel(0)
        self.playing = False

    def set_track(self, t_id):
        self.current = t_id
        self.idx = 0
        self.playing = True if t_id < 3 else False
        self.chan.stop()
        self.next_tick = pygame.time.get_ticks()

    def update(self):
        if not self.playing: return
        now = pygame.time.get_ticks()
        if now >= self.next_tick:
            notes = self.tracks[self.current]
            if not notes: return
            
            freq, dur = notes[self.idx]
            if freq > 0:
                s = synth.gen(freq, dur * NOTE * 0.95, 0.15)
                if s: self.chan.play(s)
            
            self.next_tick = now + int(dur * NOTE * 1000)
            self.idx = (self.idx + 1) % len(notes)

music = MusicEngine()

# ------------------------------------------------------------ 
# RENDERER (Classic Style)
# ------------------------------------------------------------
def draw_text(surf, text, x, y, font, color=C3, center=False):
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=(x, y))
        surf.blit(img, rect)
    else:
        surf.blit(img, (x, y))

def draw_block_sprite(surf, x, y, type_idx):
    """ Draws a Game Boy style block with bevels """
    rect = (x, y, BLOCK_SIZE, BLOCK_SIZE)
    
    # Type 0: Plain, Type 1: Dotted, Type 2: Hollow
    # Mapping shape index to visual style roughly
    style = type_idx % 3
    
    # Base background
    pygame.draw.rect(surf, C1, rect) # Light base
    
    # Bevels
    pygame.draw.line(surf, C0, (x, y), (x + BLOCK_SIZE, y), SCALE) # Top Light
    pygame.draw.line(surf, C0, (x, y), (x, y + BLOCK_SIZE), SCALE) # Left Light
    pygame.draw.line(surf, C3, (x, y + BLOCK_SIZE - SCALE), (x + BLOCK_SIZE, y + BLOCK_SIZE - SCALE), SCALE) # Bot Dark
    pygame.draw.line(surf, C3, (x + BLOCK_SIZE - SCALE, y), (x + BLOCK_SIZE - SCALE, y + BLOCK_SIZE), SCALE) # Right Dark
    
    # Inner Detail
    inset = 2 * SCALE
    inner_rect = (x + inset, y + inset, BLOCK_SIZE - 2*inset, BLOCK_SIZE - 2*inset)
    
    if style == 0:
        pygame.draw.rect(surf, C2, inner_rect) # Filled dark center
    elif style == 1:
        pygame.draw.rect(surf, C2, inner_rect, SCALE) # Hollow border
        # Dot in middle
        mid = BLOCK_SIZE // 2
        pygame.draw.rect(surf, C3, (x + mid - SCALE, y + mid - SCALE, SCALE*2, SCALE*2))
    elif style == 2:
        pygame.draw.line(surf, C2, (x+inset, y+inset), (x+BLOCK_SIZE-inset, y+BLOCK_SIZE-inset), SCALE)
        pygame.draw.line(surf, C2, (x+BLOCK_SIZE-inset, y+inset), (x+inset, y+BLOCK_SIZE-inset), SCALE)

    pygame.draw.rect(surf, C3, rect, 1) # 1px outline

def draw_handshake(surf, cx, cy):
    """ Draws the unused 'Handshake' sprite from TCRF data """
    # Simple pixel art approximation
    w, h = 40 * SCALE, 20 * SCALE
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (cx, cy)
    pygame.draw.rect(surf, C1, rect)
    pygame.draw.rect(surf, C3, rect, SCALE)
    draw_text(surf, "2-PLAYER", cx, cy - 5*SCALE, FONT_MINI, C3, True)
    draw_text(surf, "LINK", cx, cy + 5*SCALE, FONT_MINI, C3, True)

# ------------------------------------------------------------ 
# GAME LOGIC
# ------------------------------------------------------------
SHAPES = [
    [[1, 1, 1, 1]],             # I
    [[1, 1], [1, 1]],           # O
    [[0, 1, 0], [1, 1, 1]],     # T
    [[0, 1, 1], [1, 1, 0]],     # S
    [[1, 1, 0], [0, 1, 1]],     # Z
    [[1, 0, 0], [1, 1, 1]],     # J
    [[0, 0, 1], [1, 1, 1]]      # L
]

class Piece:
    def __init__(self, idx):
        self.idx = idx
        self.shape = SHAPES[idx]
        self.x = FIELD_W // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class Game:
    def __init__(self):
        self.state = "TITLE" # TITLE, MENU, PLAY, OVER
        self.field = [[0]*FIELD_W for _ in range(FIELD_H)]
        self.bag = []
        self.level = 0
        self.start_level = 0
        self.lines = 0
        self.score = 0
        self.music_choice = 0
        
        self.cur_piece = None
        self.next_piece = None
        
        self.drop_timer = 0
        self.drop_speed = 800
        self.flash_timer = 0

    def reset(self):
        self.field = [[0]*FIELD_W for _ in range(FIELD_H)]
        self.score = 0
        self.lines = 0
        self.level = self.start_level
        self.drop_speed = max(50, 800 - (self.level * 70))
        self.fill_bag()
        self.cur_piece = self.get_piece()
        self.next_piece = self.get_piece()
        music.set_track(self.music_choice)

    def fill_bag(self):
        self.bag = list(range(7))
        random.shuffle(self.bag)
    
    def get_piece(self):
        if not self.bag: self.fill_bag()
        return Piece(self.bag.pop())

    def check(self, p, dx=0, dy=0):
        for r, row in enumerate(p.shape):
            for c, val in enumerate(row):
                if val:
                    nx, ny = p.x + c + dx, p.y + r + dy
                    if nx < 0 or nx >= FIELD_W or ny >= FIELD_H: return True
                    if ny >= 0 and self.field[ny][nx]: return True
        return False

    def lock(self):
        SFX["drop"].play()
        for r, row in enumerate(self.cur_piece.shape):
            for c, val in enumerate(row):
                if val:
                    if self.cur_piece.y + r < 0:
                        self.state = "OVER"
                        music.playing = False
                        SFX["die"].play()
                        return
                    self.field[self.cur_piece.y + r][self.cur_piece.x + c] = self.cur_piece.idx + 1
        
        # Check lines
        full_rows = [i for i, row in enumerate(self.field) if all(row)]
        if full_rows:
            if len(full_rows) == 4: SFX["tetris"].play()
            else: SFX["line"].play()
            
            for i in full_rows:
                del self.field[i]
                self.field.insert(0, [0]*FIELD_W)
            
            pts = [0, 40, 100, 300, 1200][len(full_rows)] * (self.level + 1)
            self.score += pts
            self.lines += len(full_rows)
            self.level = max(self.level, self.lines // 10)
            self.drop_speed = max(50, 800 - (self.level * 70))

        self.cur_piece = self.next_piece
        self.next_piece = self.get_piece()
        if self.check(self.cur_piece):
            self.state = "OVER"
            music.playing = False
            SFX["die"].play()

    def input(self, key):
        if self.state == "PLAY":
            if key == pygame.K_LEFT and not self.check(self.cur_piece, -1, 0):
                self.cur_piece.x -= 1
                SFX["move"].play()
            elif key == pygame.K_RIGHT and not self.check(self.cur_piece, 1, 0):
                self.cur_piece.x += 1
                SFX["move"].play()
            elif key == pygame.K_DOWN and not self.check(self.cur_piece, 0, 1):
                self.cur_piece.y += 1
                self.score += 1
            elif key == pygame.K_UP: # Rotate
                orig = self.cur_piece.shape
                self.cur_piece.rotate()
                if self.check(self.cur_piece):
                    self.cur_piece.shape = orig # Kick failed, revert
                else:
                    SFX["rotate"].play()
            elif key == pygame.K_RETURN: # Pause
                self.state = "PAUSE"
                music.playing = False

        elif self.state == "PAUSE":
            if key == pygame.K_RETURN:
                self.state = "PLAY"
                music.playing = True

        elif self.state == "TITLE":
            if key == pygame.K_RETURN:
                self.state = "MENU"
                SFX["start"].play()

        elif self.state == "MENU":
            # Menu Navigation
            if key == pygame.K_UP:
                self.start_level = (self.start_level + 1) % 10
                SFX["move"].play()
            elif key == pygame.K_DOWN:
                self.start_level = (self.start_level - 1) % 10
                SFX["move"].play()
            elif key == pygame.K_RIGHT:
                self.music_choice = (self.music_choice + 1) % 4
                SFX["move"].play()
            elif key == pygame.K_LEFT:
                self.music_choice = (self.music_choice - 1) % 4
                SFX["move"].play()
            elif key == pygame.K_RETURN:
                self.reset()
                self.state = "PLAY"
                SFX["start"].play()
        
        elif self.state == "OVER":
            if key == pygame.K_RETURN:
                self.state = "TITLE"

    def run(self):
        while True:
            dt = CLOCK.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.KEYDOWN: self.input(event.key)

            music.update()
            SCREEN.fill(C0) # Base GB Color

            if self.state == "PLAY":
                self.drop_timer += dt
                if self.drop_timer > self.drop_speed:
                    self.drop_timer = 0
                    if not self.check(self.cur_piece, 0, 1):
                        self.cur_piece.y += 1
                    else:
                        self.lock()

                # Draw Frame
                border_rect = (FIELD_X - SCALE*2, FIELD_Y - SCALE*2, FIELD_PX_W + SCALE*4, FIELD_PX_H + SCALE*4)
                pygame.draw.rect(SCREEN, C3, border_rect, SCALE*2)
                pygame.draw.rect(SCREEN, C0, (FIELD_X, FIELD_Y, FIELD_PX_W, FIELD_PX_H)) # Clear field area

                # Draw Field
                for r in range(FIELD_H):
                    for c in range(FIELD_W):
                        val = self.field[r][c]
                        if val:
                            draw_block_sprite(SCREEN, FIELD_X + c*BLOCK_SIZE, FIELD_Y + r*BLOCK_SIZE, val-1)
                
                # Draw Ghost (Optional modernization)
                # ... skipped for retro authenticity ...

                # Draw Active Piece
                if self.cur_piece:
                    for r, row in enumerate(self.cur_piece.shape):
                        for c, val in enumerate(row):
                            if val and self.cur_piece.y + r >= 0:
                                draw_block_sprite(SCREEN, 
                                                  FIELD_X + (self.cur_piece.x + c)*BLOCK_SIZE, 
                                                  FIELD_Y + (self.cur_piece.y + r)*BLOCK_SIZE, 
                                                  self.cur_piece.idx)
                
                # UI Right Side
                ui_x = FIELD_X + FIELD_PX_W + 10 * SCALE
                draw_text(SCREEN, "SCORE", ui_x, FIELD_Y, FONT_SMALL)
                draw_text(SCREEN, str(self.score), ui_x, FIELD_Y + 15*SCALE, FONT_MAIN)
                
                draw_text(SCREEN, "LEVEL", ui_x, FIELD_Y + 40*SCALE, FONT_SMALL)
                draw_text(SCREEN, str(self.level), ui_x, FIELD_Y + 55*SCALE, FONT_MAIN)
                
                draw_text(SCREEN, "NEXT", ui_x, FIELD_Y + 80*SCALE, FONT_SMALL)
                if self.next_piece:
                    # Center next piece roughly
                    nx = ui_x
                    ny = FIELD_Y + 95 * SCALE
                    for r, row in enumerate(self.next_piece.shape):
                        for c, val in enumerate(row):
                            if val:
                                draw_block_sprite(SCREEN, nx + c*BLOCK_SIZE, ny + r*BLOCK_SIZE, self.next_piece.idx)

            elif self.state == "TITLE":
                # Title Art
                draw_text(SCREEN, "TETRIS", SCREEN_WIDTH//2, 30*SCALE, FONT_MAIN, C3, True)
                
                # TCRF / Unused Assets Box
                box_rect = (SCREEN_WIDTH//2 - 30*SCALE, 60*SCALE, 60*SCALE, 30*SCALE)
                pygame.draw.rect(SCREEN, C3, box_rect, SCALE)
                draw_handshake(SCREEN, SCREEN_WIDTH//2, 75*SCALE)
                
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    draw_text(SCREEN, "PRESS START", SCREEN_WIDTH//2, 110*SCALE, FONT_SMALL, C3, True)
                
                # Nintendo Footer (Requested)
                draw_text(SCREEN, "TM AND (C) 1989", SCREEN_WIDTH//2, SCREEN_HEIGHT - 20*SCALE, FONT_MINI, C3, True)
                draw_text(SCREEN, "NINTENDO", SCREEN_WIDTH//2, SCREEN_HEIGHT - 12*SCALE, FONT_MINI, C3, True)

            elif self.state == "MENU":
                draw_text(SCREEN, "- OPTIONS -", SCREEN_WIDTH//2, 20*SCALE, FONT_MAIN, C3, True)
                
                # Level Select
                draw_text(SCREEN, f"LEVEL: < {self.start_level} >", SCREEN_WIDTH//2, 50*SCALE, FONT_SMALL, C3, True)
                
                # Music Select
                m_names = ["A-TYPE", "B-TYPE", "C-TYPE", "OFF"]
                draw_text(SCREEN, f"MUSIC: < {m_names[self.music_choice]} >", SCREEN_WIDTH//2, 70*SCALE, FONT_SMALL, C3, True)
                
                draw_text(SCREEN, "CONTROLS:", SCREEN_WIDTH//2, 100*SCALE, FONT_MINI, C3, True)
                draw_text(SCREEN, "ARROWS + ENTER", SCREEN_WIDTH//2, 110*SCALE, FONT_MINI, C3, True)

            elif self.state == "OVER":
                # Game Over overlay
                pygame.draw.rect(SCREEN, C0, (SCREEN_WIDTH//4, SCREEN_HEIGHT//3, SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
                pygame.draw.rect(SCREEN, C3, (SCREEN_WIDTH//4, SCREEN_HEIGHT//3, SCREEN_WIDTH//2, SCREEN_HEIGHT//3), SCALE)
                
                draw_text(SCREEN, "GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10*SCALE, FONT_MAIN, C3, True)
                draw_text(SCREEN, f"SCORE: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10*SCALE, FONT_SMALL, C3, True)

            pygame.display.flip()

if __name__ == "__main__":
    g = Game()
    g.run()
