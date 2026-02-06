import threading
import requests
import base64
import io

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle

# --- CONFIGURATION ---
DEFAULT_IP = "192.168.1.15"
PORT = "5000"

class RemoteApp(App):
    def build(self):
        # 1. Structure principale (Verticale)
        self.root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Fond gris foncé
        with self.root.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.rect = Rectangle(size=(800, 1600), pos=self.root.pos)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        # 2. Zone IP
        ip_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.ip_input = TextInput(
            text=DEFAULT_IP, 
            multiline=False, 
            background_color=(0.2, 0.2, 0.2, 1), 
            foreground_color=(1, 1, 1, 1),
            hint_text="IP du PC"
        )
        btn_refresh = Button(text="Connexion", size_hint_x=0.3, background_color=(0, 0.7, 0.7, 1))
        btn_refresh.bind(on_press=self.check_connection)
        ip_layout.add_widget(self.ip_input)
        ip_layout.add_widget(btn_refresh)
        self.root.add_widget(ip_layout)

        # 3. Pochette Album
        self.cover_image = KivyImage(source="", size_hint=(None, None), size=(250, 250), pos_hint={'center_x': 0.5})
        # Image vide par défaut (carré gris)
        with self.cover_image.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.cover_image.pos, size=self.cover_image.size)
        self.root.add_widget(self.cover_image)

        # 4. Infos Titre
        self.lbl_title = Label(text="En attente...", font_size='20sp', bold=True, color=(1,1,1,1), size_hint_y=None, height=40)
        self.lbl_artist = Label(text="OnlyAudio", font_size='16sp', color=(0, 0.8, 0.8, 1), size_hint_y=None, height=30)
        self.root.add_widget(self.lbl_title)
        self.root.add_widget(self.lbl_artist)

        # 5. Barre de progression
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        self.root.add_widget(self.progress)
        
        self.lbl_time = Label(text="0:00 / 0:00", font_size='12sp', color=(0.7, 0.7, 0.7, 1), size_hint_y=None, height=20)
        self.root.add_widget(self.lbl_time)

        # 6. Boutons de contrôle (Gros boutons)
        controls = BoxLayout(size_hint_y=None, height=80, spacing=10)
        btn_prev = Button(text="<", font_size=30, background_color=(0.3, 0.3, 0.3, 1))
        btn_prev.bind(on_press=lambda x: self.send_cmd("prev"))
        
        btn_play = Button(text="PLAY", font_size=20, background_color=(0, 0.8, 0, 1))
        btn_play.bind(on_press=lambda x: self.send_cmd("play_pause"))
        
        btn_next = Button(text=">", font_size=30, background_color=(0.3, 0.3, 0.3, 1))
        btn_next.bind(on_press=lambda x: self.send_cmd("next"))
        
        controls.add_widget(btn_prev)
        controls.add_widget(btn_play)
        controls.add_widget(btn_next)
        self.root.add_widget(controls)

        # 7. Volume
        vol_layout = BoxLayout(size_hint_y=None, height=60, spacing=20)
        btn_vdown = Button(text="Vol -", background_color=(0.4, 0.4, 0.4, 1))
        btn_vdown.bind(on_press=lambda x: self.send_cmd("vol_down"))
        
        btn_vup = Button(text="Vol +", background_color=(0.4, 0.4, 0.4, 1))
        btn_vup.bind(on_press=lambda x: self.send_cmd("vol_up"))
        
        vol_layout.add_widget(btn_vdown)
        vol_layout.add_widget(btn_vup)
        self.root.add_widget(vol_layout)

        # Espace vide pour combler le bas
        self.root.add_widget(Label())

        # Timer pour mise à jour
        Clock.schedule_interval(self.update_status, 1)
        return self.root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def send_cmd(self, cmd):
        ip = self.ip_input.text
        threading.Thread(target=self._req, args=(f"http://{ip}:{PORT}/{cmd}",)).start()

    def _req(self, url):
        try: requests.get(url, timeout=0.5)
        except: pass

    def check_connection(self, instance):
        self.update_status(0)

    def update_status(self, dt):
        ip = self.ip_input.text
        threading.Thread(target=self._fetch, args=(f"http://{ip}:{PORT}/status",)).start()

    def _fetch(self, url):
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                Clock.schedule_once(lambda d: self.apply_data(r.json()), 0)
        except: pass

    def apply_data(self, data):
        self.lbl_title.text = data.get('title', "...")
        self.lbl_artist.text = data.get('artist', "")
        
        dur = data.get('dur', 1); pos = data.get('pos', 0)
        if dur > 0: self.progress.value = (pos / dur) * 100
        
        t_curr = f"{int(pos/1000)//60}:{int(pos/1000)%60:02d}"
        t_dur = f"{int(dur/1000)//60}:{int(dur/1000)%60:02d}"
        self.lbl_time.text = f"{t_curr} / {t_dur}"

        b64 = data.get('cover_b64', "")
        if b64:
            try:
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                self.cover_image.texture = im.texture
            except: pass

if __name__ == "__main__":
    RemoteApp().run()
