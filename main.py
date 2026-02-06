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

# Couleurs (Thème Sombre OnlyAudio)
COL_BG = (0.05, 0.05, 0.05, 1)
COL_INPUT = (0.15, 0.15, 0.15, 1)
COL_BTN_PLAY = (0, 0.6, 0, 1)
COL_BTN_NAV = (0.2, 0.2, 0.2, 1)
COL_BTN_OPT = (0.3, 0.3, 0.3, 1)

class RemoteApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=15, spacing=15)
        
        with self.root.canvas.before:
            Color(*COL_BG)
            self.rect = Rectangle(size=(800, 1600), pos=self.root.pos)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        # 1. CONNEXION (Sécurisée)
        conn_layout = BoxLayout(size_hint_y=0.08, spacing=10)
        self.ip_input = TextInput(
            text=DEFAULT_IP, multiline=False, password=True, # IP Masquée
            font_size='18sp', halign='center', padding_y=[12,0],
            background_color=COL_INPUT, foreground_color=(1,1,1,1),
            hint_text="IP", hint_text_color=(0.5,0.5,0.5,1)
        )
        btn_connect = Button(text="LIER", size_hint_x=0.3, background_color=(0.2, 0.4, 0.6, 1), bold=True)
        btn_connect.bind(on_press=self.check_connection)
        conn_layout.add_widget(self.ip_input)
        conn_layout.add_widget(btn_connect)
        self.root.add_widget(conn_layout)

        # 2. POCHETTE
        self.cover_image = KivyImage(source="", allow_stretch=True, keep_ratio=True, size_hint_y=0.5)
        self.root.add_widget(self.cover_image)

        # 3. INFOS
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.15)
        self.lbl_title = Label(text="OnlyAudio", font_size='24sp', bold=True, color=(1,1,1,1), halign='center', valign='middle')
        self.lbl_title.bind(size=self.lbl_title.setter('text_size'))
        self.lbl_artist = Label(text="Remote", font_size='18sp', color=(0, 0.8, 1, 1))
        info_layout.add_widget(self.lbl_title)
        info_layout.add_widget(self.lbl_artist)
        self.root.add_widget(info_layout)

        # 4. CONTRÔLES
        ctrl_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        
        btn_prev = Button(text="|<", font_size='24sp', background_color=COL_BTN_NAV)
        btn_prev.bind(on_press=lambda x: self.send_cmd("prev"))

        btn_play = Button(text="PLAY/PAUSE", font_size='16sp', background_color=COL_BTN_PLAY, bold=True, size_hint_x=1.5)
        btn_play.bind(on_press=lambda x: self.send_cmd("play_pause"))

        btn_next = Button(text=">|", font_size='24sp', background_color=COL_BTN_NAV)
        btn_next.bind(on_press=lambda x: self.send_cmd("next"))

        ctrl_layout.add_widget(btn_prev)
        ctrl_layout.add_widget(btn_play)
        ctrl_layout.add_widget(btn_next)
        self.root.add_widget(ctrl_layout)

        # 5. VOLUME & OPTIONS
        vol_layout = BoxLayout(size_hint_y=0.12, spacing=10)
        
        btn_vm = Button(text="-", font_size='24sp', background_color=COL_BTN_OPT)
        btn_vm.bind(on_press=lambda x: self.send_cmd("vol_down"))
        
        btn_vp = Button(text="+", font_size='24sp', background_color=COL_BTN_OPT)
        btn_vp.bind(on_press=lambda x: self.send_cmd("vol_up"))
        
        btn_shuff = Button(text="ALEA", font_size='12sp', background_color=COL_BTN_OPT)
        btn_shuff.bind(on_press=lambda x: self.send_cmd("shuffle"))

        vol_layout.add_widget(btn_vm)
        vol_layout.add_widget(btn_shuff)
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
        instance.text = "..."
        Clock.schedule_once(lambda dt: setattr(instance, 'text', "LIER"), 1)
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
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                if self.cover_image.texture != im.texture:
                    self.cover_image.texture = im.texture
            except: pass

if __name__ == "__main__":
    RemoteApp().run()
