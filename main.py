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

# Couleurs (Haute Visibilité)
COL_BG = (0.1, 0.1, 0.1, 1)
COL_INPUT = (0.9, 0.9, 0.9, 1)
COL_BTN_PLAY = (0, 0.7, 0, 1)    # Vert
COL_BTN_NAV = (0, 0.5, 0.8, 1)   # Bleu
COL_BTN_OPT = (0.8, 0.4, 0, 1)   # Orange
COL_GRAY = (0.3, 0.3, 0.3, 1)

class RemoteApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Fond sombre
        with self.root.canvas.before:
            Color(*COL_BG)
            self.rect = Rectangle(size=(800, 1600), pos=self.root.pos)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        # 1. Connexion (IP)
        ip_layout = BoxLayout(size_hint_y=0.08, spacing=10)
        self.ip_input = TextInput(
            text=DEFAULT_IP, multiline=False, 
            font_size='22sp', halign='center', padding_y=[10,0],
            background_color=COL_INPUT
        )
        btn_connect = Button(text="RELIER", size_hint_x=0.4, background_color=COL_BTN_NAV, bold=True)
        btn_connect.bind(on_press=self.check_connection)
        ip_layout.add_widget(self.ip_input)
        ip_layout.add_widget(btn_connect)
        self.root.add_widget(ip_layout)

        # 2. Pochette
        self.cover_image = KivyImage(source="", allow_stretch=True, keep_ratio=True, size_hint_y=0.35)
        # Un fond gris derrière l'image pour faire propre si vide
        with self.cover_image.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.cover_image.pos, size=self.cover_image.size)
        self.root.add_widget(self.cover_image)

        # 3. Infos Titre (Statique mais sur 2 lignes max)
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.15)
        
        self.lbl_title = Label(
            text="En attente...", 
            font_size='26sp', 
            bold=True, 
            color=(1,1,1,1),
            halign='center', valign='middle'
        )
        # Astuce pour centrer le texte et permettre le retour à la ligne
        self.lbl_title.bind(size=self.lbl_title.setter('text_size')) 
        
        self.lbl_artist = Label(text="OnlyAudio", font_size='20sp', color=(0, 0.8, 0.8, 1))
        
        info_layout.add_widget(self.lbl_title)
        info_layout.add_widget(self.lbl_artist)
        self.root.add_widget(info_layout)

        # 4. Barre de progression (Calculs corrigés)
        prog_layout = BoxLayout(orientation='vertical', size_hint_y=0.1, spacing=5)
        self.progress = ProgressBar(max=1000, value=0) 
        self.lbl_time = Label(text="0:00 / 0:00", font_size='18sp', bold=True)
        prog_layout.add_widget(self.progress)
        prog_layout.add_widget(self.lbl_time)
        self.root.add_widget(prog_layout)

        # 5. Contrôles (Gros Boutons)
        ctrl_layout = BoxLayout(size_hint_y=0.15, spacing=8)
        
        btn_shuff = Button(text="SHUF", background_color=COL_BTN_OPT, size_hint_x=0.6, bold=True)
        btn_shuff.bind(on_press=lambda x: self.send_cmd("shuffle"))

        btn_prev = Button(text="<<", font_size='30sp', background_color=COL_BTN_NAV, bold=True)
        btn_prev.bind(on_press=lambda x: self.send_cmd("prev"))

        btn_play = Button(text="PLAY", font_size='24sp', background_color=COL_BTN_PLAY, bold=True, size_hint_x=1.4)
        btn_play.bind(on_press=lambda x: self.send_cmd("play_pause"))

        btn_next = Button(text=">>", font_size='30sp', background_color=COL_BTN_NAV, bold=True)
        btn_next.bind(on_press=lambda x: self.send_cmd("next"))

        btn_rep = Button(text="RPT", background_color=COL_BTN_OPT, size_hint_x=0.6, bold=True)
        btn_rep.bind(on_press=lambda x: self.send_cmd("repeat"))

        ctrl_layout.add_widget(btn_shuff)
        ctrl_layout.add_widget(btn_prev)
        ctrl_layout.add_widget(btn_play)
        ctrl_layout.add_widget(btn_next)
        ctrl_layout.add_widget(btn_rep)
        self.root.add_widget(ctrl_layout)

        # 6. Volume
        vol_layout = BoxLayout(size_hint_y=0.12, spacing=15)
        btn_vm = Button(text="VOL -", font_size='20sp', bold=True, background_color=COL_GRAY)
        btn_vm.bind(on_press=lambda x: self.send_cmd("vol_down"))
        btn_vp = Button(text="VOL +", font_size='20sp', bold=True, background_color=COL_GRAY)
        btn_vp.bind(on_press=lambda x: self.send_cmd("vol_up"))
        vol_layout.add_widget(btn_vm)
        vol_layout.add_widget(btn_vp)
        self.root.add_widget(vol_layout)

        Clock.schedule_interval(self.update_status, 1)
        return self.root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def send_cmd(self, cmd):
        ip = self.ip_input.text.strip()
        if ip: threading.Thread(target=self._req, args=(f"http://{ip}:{PORT}/{cmd}",)).start()

    def _req(self, url):
        try: requests.get(url, timeout=0.5)
        except: pass

    def check_connection(self, instance):
        self.update_status(0)

    def update_status(self, dt):
        ip = self.ip_input.text.strip()
        if ip: threading.Thread(target=self._fetch, args=(f"http://{ip}:{PORT}/status",)).start()

    def _fetch(self, url):
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                Clock.schedule_once(lambda d: self.apply_data(r.json()), 0)
        except: pass

    def apply_data(self, data):
        # 1. Textes
        self.lbl_title.text = str(data.get('title', "OnlyAudio"))
        self.lbl_artist.text = str(data.get('artist', "Remote"))

        # 2. Barre de temps (Le calcul qui répare tout)
        try:
            # Conversion forcée en nombre décimal
            dur = float(data.get('dur', 1))
            pos = float(data.get('pos', 0))
            
            # Mise à jour barre (0 à 1000)
            if dur > 0:
                self.progress.value = (pos / dur) * 1000
            else:
                self.progress.value = 0
            
            # Formatage mm:ss
            def fmt(ms):
                seconds = int(ms / 1000)
                return f"{seconds//60}:{seconds%60:02d}"
            
            self.lbl_time.text = f"{fmt(pos)} / {fmt(dur)}"
        except:
            self.lbl_time.text = "-:-- / -:--"

        # 3. Pochette
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                # On ne met à jour que si l'image change pour économiser le CPU
                if self.cover_image.texture != im.texture:
                    self.cover_image.texture = im.texture
            except: pass

if __name__ == "__main__":
    RemoteApp().run()
