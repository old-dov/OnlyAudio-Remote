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
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle

# --- CONFIGURATION ---
DEFAULT_IP = "192.168.1.15"
PORT = "5000"

# Couleurs (Haute Visibilité)
COL_BG = (0.1, 0.1, 0.1, 1)        # Fond Noir/Gris
COL_ZONE_TOP = (0.2, 0.2, 0.2, 1)  # Fond zone connexion
COL_INPUT = (0.9, 0.9, 0.9, 1)     # Fond champ texte
COL_BTN_PLAY = (0, 0.7, 0, 1)      # Vert
COL_BTN_NAV = (0, 0.5, 0.8, 1)     # Bleu
COL_BTN_OPT = (0.8, 0.4, 0, 1)     # Orange
COL_GRAY = (0.3, 0.3, 0.3, 1)      # Gris pour Volume

class RemoteApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        # Fond sombre général
        with self.root.canvas.before:
            Color(*COL_BG)
            self.rect = Rectangle(size=(800, 1600), pos=self.root.pos)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        # 1. ZONE DE CONNEXION (Refaite proprement)
        # Un fond légèrement plus clair pour distinguer cette zone
        conn_layout = BoxLayout(size_hint_y=0.1, spacing=10, padding=5)
        with conn_layout.canvas.before:
            Color(*COL_ZONE_TOP)
            self.rect_conn = Rectangle(size=conn_layout.size, pos=conn_layout.pos)
        conn_layout.bind(pos=self._update_conn_rect, size=self._update_conn_rect)

        self.ip_input = TextInput(
            text=DEFAULT_IP, multiline=False, 
            font_size='20sp', halign='center', padding_y=[12,0],
            background_color=COL_INPUT, hint_text="IP DU PC"
        )
        
        btn_connect = Button(text="CONNECTER", size_hint_x=0.5, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        btn_connect.bind(on_press=self.check_connection)
        
        conn_layout.add_widget(self.ip_input)
        conn_layout.add_widget(btn_connect)
        self.root.add_widget(conn_layout)

        # 2. POCHETTE (Grande)
        self.cover_image = KivyImage(source="", allow_stretch=True, keep_ratio=True, size_hint_y=0.4)
        with self.cover_image.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=self.cover_image.pos, size=self.cover_image.size)
        self.root.add_widget(self.cover_image)

        # 3. INFOS TITRE (Gros et lisible)
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.15)
        self.lbl_title = Label(
            text="Non connecté", 
            font_size='26sp', bold=True, color=(1,1,1,1),
            halign='center', valign='middle'
        )
        self.lbl_title.bind(size=self.lbl_title.setter('text_size'))
        
        self.lbl_artist = Label(text="...", font_size='20sp', color=(0, 0.8, 0.8, 1))
        
        info_layout.add_widget(self.lbl_title)
        info_layout.add_widget(self.lbl_artist)
        self.root.add_widget(info_layout)

        # 4. TEMPS (Juste le texte, plus de barre)
        # On le met bien gros pour que ce soit visible de loin
        self.lbl_time = Label(text="--:-- / --:--", font_size='28sp', bold=True, color=(0.8, 0.8, 0.8, 1), size_hint_y=0.08)
        self.root.add_widget(self.lbl_time)

        # 5. CONTRÔLES (Boutons Colorés)
        ctrl_layout = BoxLayout(size_hint_y=0.15, spacing=8)
        
        # Shuffle (Orange)
        btn_shuff = Button(text="ALEA", background_color=COL_BTN_OPT, size_hint_x=0.6, bold=True)
        btn_shuff.bind(on_press=lambda x: self.send_cmd("shuffle"))

        # Prev (Bleu)
        btn_prev = Button(text="<<", font_size='30sp', background_color=COL_BTN_NAV, bold=True)
        btn_prev.bind(on_press=lambda x: self.send_cmd("prev"))

        # PLAY (Vert, très large)
        btn_play = Button(text="LECTURE", font_size='22sp', background_color=COL_BTN_PLAY, bold=True, size_hint_x=1.4)
        btn_play.bind(on_press=lambda x: self.send_cmd("play_pause"))

        # Next (Bleu)
        btn_next = Button(text=">>", font_size='30sp', background_color=COL_BTN_NAV, bold=True)
        btn_next.bind(on_press=lambda x: self.send_cmd("next"))

        # Repeat (Orange)
        btn_rep = Button(text="REP", background_color=COL_BTN_OPT, size_hint_x=0.6, bold=True)
        btn_rep.bind(on_press=lambda x: self.send_cmd("repeat"))

        ctrl_layout.add_widget(btn_shuff)
        ctrl_layout.add_widget(btn_prev)
        ctrl_layout.add_widget(btn_play)
        ctrl_layout.add_widget(btn_next)
        ctrl_layout.add_widget(btn_rep)
        self.root.add_widget(ctrl_layout)

        # 6. VOLUME (Gris, en bas)
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

    def _update_conn_rect(self, instance, value):
        self.rect_conn.pos = instance.pos
        self.rect_conn.size = instance.size

    def send_cmd(self, cmd):
        ip = self.ip_input.text.strip()
        if ip: threading.Thread(target=self._req, args=(f"http://{ip}:{PORT}/{cmd}",)).start()

    def _req(self, url):
        try: requests.get(url, timeout=0.5)
        except: pass

    def check_connection(self, instance):
        # Petit effet visuel : le bouton change de texte brièvement
        instance.text = "..."
        Clock.schedule_once(lambda dt: setattr(instance, 'text', "CONNECTER"), 1)
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
        self.lbl_title.text = str(data.get('title', "OnlyAudio"))
        self.lbl_artist.text = str(data.get('artist', "Remote"))

        # Gestion Temps (Sans barre)
        try:
            dur = float(data.get('dur', 1))
            pos = float(data.get('pos', 0))
            
            def fmt(ms):
                seconds = int(ms / 1000)
                return f"{seconds//60}:{seconds%60:02d}"
            
            self.lbl_time.text = f"{fmt(pos)} / {fmt(dur)}"
        except:
            self.lbl_time.text = "--:-- / --:--"

        # Gestion Pochette
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                if self.cover_image.texture != im.texture:
                    self.cover_image.texture = im.texture
            except: pass

if __name__ == "__main__":
    RemoteApp().run()
