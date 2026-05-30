from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.graphics import Rectangle, Color, RoundedRectangle
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from random import randint

# ---------------- PLAYER ----------------
class Player(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (60, 100)
        self.pos = (Window.width / 2 - self.width / 2, 50)
        with self.canvas:
            self.rect = Rectangle(source="car.png", pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ---------------- OBSTACLE ----------------
class Obstacle(Widget):
    def __init__(self, pos, size=(50, 80), **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.pos = pos
        with self.canvas:
            self.rect = Rectangle(source="cone.png", pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ---------------- GAME ----------------
class Game(Widget):
    score = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_started = False
        self.paused = False  # ✅ PAUSE FLAG

        # ---------- BACKGROUND ----------
        with self.canvas.before:
            self.bg1 = Rectangle(source="backgroundd.png", pos=(0, 0), size=Window.size)
            self.bg2 = Rectangle(source="backgroundd.png", pos=(0, Window.height), size=Window.size)

        # ---------- ROAD ----------
        self.road_width = 200
        self.lanes = 3
        self.update_road_dimensions()

        # ---------- PLAYER ----------
        self.player = Player()
        self.add_widget(self.player)

        # ---------- OBSTACLES ----------
        self.obstacles = []

        # ---------- SCORE ----------
        self.score_label = Label(
            text="[color=000000]Score: 0[/color]",
            font_size=25,
            size_hint=(None, None),
            center_x=Window.width / 2,
            y=Window.height - 60,
            markup=True
        )

        # ---------- MUSIC ----------
        self.bg_music = SoundLoader.load("music.mp3")
        if self.bg_music:
            self.bg_music.loop = True
            self.bg_music.volume = 0.5

        # ---------- START BUTTON ----------
        self.start_btn = Button(
            text="START",
            size=(200, 80),
            pos=(Window.width / 2 - 100, Window.height / 2 - 120),
            font_size=30,
            background_normal="",
            background_color=(0, 0, 0, 0)
        )
        with self.start_btn.canvas.before:
            Color(0.3, 0.9, 0.3, 1)
            self.start_rect = RoundedRectangle(pos=self.start_btn.pos, size=self.start_btn.size, radius=[25])
        self.start_btn.bind(pos=self.update_start_rect, size=self.update_start_rect)
        self.start_btn.bind(on_press=self.start_game)
        self.add_widget(self.start_btn)

        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_resize=self.update_layout)

    # ---------- HELPERS ----------
    def update_road_dimensions(self):
        self.road_left = Window.width / 2 - self.road_width / 2
        self.road_right = Window.width / 2 + self.road_width / 2
        self.lane_width = self.road_width / self.lanes

    def update_start_rect(self, *args):
        self.start_rect.pos = self.start_btn.pos
        self.start_rect.size = self.start_btn.size

    def update_layout(self, window, width, height):
        if hasattr(self, 'bg1') and hasattr(self, 'bg2'):
            self.bg1.size = (width, height)
            self.bg2.size = (width, height)
            if self.bg1.pos[1] <= self.bg2.pos[1]:
                self.bg2.pos = (0, self.bg1.pos[1] + height)
            else:
                self.bg1.pos = (0, self.bg2.pos[1] + height)

        self.update_road_dimensions()
        self.player.x = max(self.road_left, min(self.road_right - self.player.width, self.player.x))
        self.score_label.center_x = width / 2
        self.score_label.y = height - 45

    # ---------- START GAME ----------
    def start_game(self, instance):
        self.reset_game()
        self.game_started = True
        self.paused = False  # reset pause
        self.remove_widget(self.start_btn)
        self.add_widget(self.score_label)
        if self.bg_music:
            self.bg_music.play()
        Clock.schedule_interval(self.update, 1 / 60)

    # ---------- RESET ----------
    def reset_game(self):
        Clock.unschedule(self.update)
        self.clear_widgets()
        self.canvas.before.clear()
        with self.canvas.before:
            self.bg1 = Rectangle(source="backgroundd.png", pos=(0, 0), size=Window.size)
            self.bg2 = Rectangle(source="backgroundd.png", pos=(0, Window.height), size=Window.size)
        self.add_widget(self.player)
        self.player.pos = (Window.width / 2 - self.player.width / 2, 50)
        self.obstacles.clear()
        self.score = 0

    # ---------- PAUSE FUNCTION ----------
    def toggle_pause(self):
        if not self.game_started:
            return

        self.paused = not self.paused

        if self.paused:
            if self.bg_music:
                self.bg_music.stop()
        else:
            if self.bg_music:
                self.bg_music.play()

    # ---------- BACKGROUND ----------
    def scroll_background(self):
        speed = 4
        self.bg1.pos = (0, self.bg1.pos[1] - speed)
        self.bg2.pos = (0, self.bg2.pos[1] - speed)
        if self.bg1.pos[1] <= -Window.height:
            self.bg1.pos = (0, self.bg2.pos[1] + Window.height)
        if self.bg2.pos[1] <= -Window.height:
            self.bg2.pos = (0, self.bg1.pos[1] + Window.height)

    # ---------- PLAYER ----------
    def move_player_left(self):
        self.player.x -= self.lane_width
        self.keep_player_inside()

    def move_player_right(self):
        self.player.x += self.lane_width
        self.keep_player_inside()

    # ---------- OBSTACLES ----------
    def spawn_obstacles(self):
        safe_lane = randint(0, self.lanes - 1)
        for lane in range(self.lanes):
            if lane == safe_lane:
                continue
            x = self.road_left + lane * self.lane_width + (self.lane_width - 50) / 2
            y = Window.height + 600
            obs = Obstacle(pos=(x, y))
            self.obstacles.append(obs)
            self.add_widget(obs)

    # ---------- UPDATE ----------
    def update(self, dt):
        if not self.game_started or self.paused:
            return

        self.scroll_background()

        for obs in self.obstacles[:]:
            obs.y -= 4
            if obs.y + obs.height < 0:
                self.remove_widget(obs)
                self.obstacles.remove(obs)

        if not self.obstacles or max(o.y for o in self.obstacles) < Window.height - 300:
            self.spawn_obstacles()

        for obs in self.obstacles:
            if self.player.collide_widget(obs):
                self.game_over()

        self.score += dt
        self.score_label.text = f"[color=000000]Score: {int(self.score)}[/color]"

    # ---------- CONTROLS ----------
    def on_key_down(self, window, key, *args):
        if key == 32:  # SPACE = pause
            self.toggle_pause()
            return

        if not self.game_started or self.paused:
            return

        if key == 276:
            self.move_player_left()
        elif key == 275:
            self.move_player_right()

    def on_touch_down(self, touch):
        if self.game_started and not self.paused:
            if touch.x < Window.width / 2:
                self.move_player_left()
            else:
                self.move_player_right()
        return super().on_touch_down(touch)

    def keep_player_inside(self):
        self.player.x = max(self.road_left, min(self.road_right - self.player.width, self.player.x))

    # ---------- GAME OVER ----------
    def game_over(self):
        Clock.unschedule(self.update)
        self.game_started = False
        if self.bg_music:
            self.bg_music.stop()
        self.clear_widgets()
        self.add_widget(Label(
            text=f"[color=000000]GAME OVER\nScore: {int(self.score)}[/color]",
            font_size=32,
            center=(Window.width / 2, Window.height / 2 + 40),
            size_hint=(None, None),
            markup=True
        ))
        restart_btn = Button(
            text="RESTART",
            size=(220, 80),
            pos=(Window.width / 2 - 110, Window.height / 2 - 140),
            font_size=26
        )
        restart_btn.bind(on_press=self.start_game)
        self.add_widget(restart_btn)


# ---------------- APP ----------------
class EndlessRunnerApp(App):
    def build(self):
        return Game()


if __name__ == "__main__":
    EndlessRunnerApp().run()