import threading
import requests
import base64
import io

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
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

# Codes couleurs (R, G, B, A)
COL_DARK = (0.1, 0.1, 0.1, 1)
COL_BTN_PLAY = (0, 0.8, 0, 1)      # Vert
COL_BTN_NAV = (0, 0.6, 0.8, 1)     # Bleu
COL_BTN_OPT = (0.9, 0.5, 0, 1)     # Orange
COL_BTN_VOL = (0.3, 0.3, 0.3, 1)   # Gris
COL_TEXT = (1, 1, 1, 1)

class RemoteApp(App):
    def build(self):
        # Fond général
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        with self.root.canvas.before:
            Color(*COL_DARK)
            self.rect = Rectangle(size=(800, 1600), pos=self.root.pos)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        # 1. Zone IP (Grosse case)
        ip_layout = BoxLayout(size_hint_y=0.08, spacing=10)
        self.ip_input = TextInput(
            text=DEFAULT_IP, multiline=False, 
            font_size='22sp', halign='center', padding_y=[15,0],
            background_color=(0.9, 0.9, 0.9, 1)
        )
        btn_connect = Button(text="RELIER", font_size='18sp', bold=True, 
                             size_hint_x=0.4, background_color=COL_BTN_NAV)
        btn_connect.bind(on_press=self.check_connection)
        ip_layout.add_widget(self.ip_input)
        ip_layout.add_widget(btn_connect)
        self.root.add_widget(ip_layout)

        # 2. Pochette (Prend de la place)
        self.cover_container = BoxLayout(size_hint_y=0.35, padding=[40, 10])
        self.cover_image = KivyImage(source="", allow_stretch=True, keep_ratio=True)
        # Fond gris pour la pochette
        with self.cover_image.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.cover_image.pos, size=self.cover_image.size)
        self.cover_container.add_widget(self.cover_image)
        self.root.add_widget(self.cover_container)

        # 3. Infos Titre (Gros texte)
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.15)
        self.lbl_title = Label(text="En attente...", font_size='28sp', bold=True, color=(1,1,1,1), halign='center', valign='middle')
        self.lbl_title.bind(size=self.lbl_title.setter('text_size')) # Pour centrer si trop long
        self.lbl_artist = Label(text="OnlyAudio Remote", font_size='22sp', color=(0, 0.8, 0.8, 1))
        info_layout.add_widget(self.lbl_title)
        info_layout.add_widget(self.lbl_artist)
        self.root.add_widget(info_layout)

        # 4. Progression
        prog_layout = BoxLayout(orientation='vertical', size_hint_y=0.1, spacing=5)
        self.progress = ProgressBar(max=100, value=0)
        self.lbl_time = Label(text="0:00 / 0:00", font_size='18sp', bold=True, color=(0.8, 0.8, 0.8, 1))
        prog_layout.add_widget(self.progress)
        prog_layout.add_widget(self.lbl_time)
        self.root.add_widget(prog_layout)

        # 5. Contrôles Principaux (Ligne 1)
        # Ordre : Shuffle | Précédent | PLAY | Suivant | Repeat
        ctrl_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        
        btn_shuff = Button(text="SHUF", font_size='14sp', background_color=COL_BTN_OPT, size_hint_x=0.5)
        btn_shuff.bind(on_press=lambda x: self.send_cmd("shuffle"))
        
        btn_prev = Button(text="<<", font_size='30sp', bold=True, background_color=COL_BTN_NAV)
        btn_prev.bind(on_press=lambda x: self.send_cmd("prev"))

        btn_play = Button(text="PLAY", font_size='24sp', bold=True, background_color=COL_BTN_PLAY, size_hint_x=1.3)
        btn_play.bind(on_press=lambda x: self.send_cmd("play_pause"))

        btn_next = Button(text=">>", font_size='30sp', bold=True, background_color=COL_BTN_NAV)
        btn_next.bind(on_press=lambda x: self.send_cmd("next"))

        btn_rep = Button(text="RPT", font_size='14sp', background_color=COL_BTN_OPT, size_hint_x=0.5)
        btn_rep.bind(on_press=lambda x: self.send_cmd("repeat"))

        ctrl_layout.add_widget(btn_shuff)
        ctrl_layout.add_widget(btn_prev)
        ctrl_layout.add_widget(btn_play)
        ctrl_layout.add_widget(btn_next)
        ctrl_layout.add_widget(btn_rep)
        self.root.add_widget(ctrl_layout)

        # 6. Volume (Gros boutons en bas)
        vol_layout = BoxLayout(size_hint_y=0.12, spacing=20)
        btn_vdown = Button(text="VOLUME -", font_size='20sp', bold=True, background_color=COL_BTN_VOL)
        btn_vdown.bind(on_press=lambda x: self.send_cmd("vol_down"))
        
        btn_vup = Button(text="VOLUME +", font_size='20sp', bold=True, background_color=COL_BTN_VOL)
        btn_vup.bind(on_press=lambda x: self.send_cmd("vol_up"))
        
        vol_layout.add_widget(btn_vdown)
        vol_layout.add_widget(btn_vup)
        self.root.add_widget(vol_layout)

        # Lancement boucle
        Clock.schedule_interval(self.update_status, 1)
        return self.root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def send_cmd(self, cmd):
        ip = self.ip_input.text.strip()
        threading.Thread(target=self._req, args=(f"http://{ip}:{PORT}/{cmd}",)).start()

    def _req(self, url):
        try: requests.get(url, timeout=0.5)
        except: pass

    def check_connection(self, instance):
        self.update_status(0)

    def update_status(self, dt):
        ip = self.ip_input.text.strip()
        if not ip: return
        threading.Thread(target=self._fetch, args=(f"http://{ip}:{PORT}/status",)).start()

    def _fetch(self, url):
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                data = r.json()
                Clock.schedule_once(lambda d: self.apply_data(data), 0)
        except: pass

    def apply_data(self, data):
        # Textes
        self.lbl_title.text = str(data.get('title', "Inconnu"))
        self.lbl_artist.text = str(data.get('artist', "OnlyAudio"))
        
        # Gestion propre des temps (Conversion en entier obligatoire)
        try:
            dur = int(float(data.get('dur', 1)))
            pos = int(float(data.get('pos', 0)))
        except:
            dur, pos = 1, 0

        # Mise à jour barre
        if dur > 0: 
            pct = (pos / dur) * 100
            self.progress.value = pct
        else:
            self.progress.value = 0
        
        # Mise à jour compteur texte (mm:ss)
        t_curr = f"{int(pos/1000)//60}:{int(pos/1000)%60:02d}"
        t_dur = f"{int(dur/1000)//60}:{int(dur/1000)%60:02d}"
        self.lbl_time.text = f"{t_curr} / {t_dur}"

        # Image
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                self.cover_image.texture = im.texture
            except: pass

if __name__ == "__main__":
    RemoteApp().run()
