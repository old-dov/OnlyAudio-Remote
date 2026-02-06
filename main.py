import threading
import requests
import base64
import io
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.stencilview import StencilView
from kivy.animation import Animation
from kivy.properties import StringProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard

DEFAULT_IP = "192.168.1.15" 
PORT = "5000"

class MarqueeLabel(StencilView):
    text = StringProperty("Déconnecté")
    font_style = StringProperty("H5")
    color = ObjectProperty([1, 1, 1, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = MDLabel(
            text=self.text, font_style=self.font_style,
            theme_text_color="Custom", text_color=self.color,
            halign="center", valign="center",
            size_hint=(None, 1), adaptive_width=True
        )
        self.add_widget(self.label)
        self.bind(text=self.update_label, size=self.restart_animation)
        self.anim = None

    def update_label(self, *args):
        self.label.text = self.text
        Clock.schedule_once(self.restart_animation, 0.1)

    def restart_animation(self, *args):
        if self.anim: self.anim.cancel()
        self.label.texture_update()
        self.label.width = self.label.texture_size[0] + 50
        if self.label.width > self.width:
            self.label.x = self.width
            duration = self.label.width / 50.0
            self.anim = Animation(x=-self.label.width, duration=duration) + Animation(x=self.width, duration=0)
            self.anim.repeat = True
            self.anim.start(self.label)
        else:
            self.label.center_x = self.center_x

# --- DIFFÉRENCE ICI : PLUS D'IMAGES, QUE DU CODE ---
KV = '''
<MainScreen>:
    # FOND D'ÉCRAN GRIS FONCÉ (Au lieu de l'image qui plante)
    md_bg_color: 0.1, 0.1, 0.1, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "10dp"

        # INPUT IP
        MDBoxLayout:
            adaptive_height: True
            spacing: "10dp"
            MDTextField:
                id: ip_input
                text: root.default_ip
                hint_text: "IP PC"
                mode: "fill"
                fill_color_normal: 0.2, 0.2, 0.2, 1
                text_color_focus: 0, 1, 1, 1
                theme_text_color: "Custom"
                text_color_normal: 1, 1, 1, 1
            MDIconButton:
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: 0, 1, 1, 1
                on_release: root.check_connection()

        # POCHETTE (Carré gris par défaut)
        MDCard:
            size_hint: None, None
            size: "260dp", "260dp"
            pos_hint: {"center_x": 0.5}
            radius: [15,]
            md_bg_color: 0.2, 0.2, 0.2, 1
            elevation: 2
            
            # L'image ne s'affichera que si reçue du réseau
            FitImage:
                id: cover_image
                radius: [15,]

        # INFOS
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            spacing: "5dp"
            MarqueeLabel:
                id: track_title
                text: "En attente..."
                font_style: "H4"
                size_hint_y: None
                height: "50dp"
                color: 1, 1, 1, 1
            MDLabel:
                id: track_artist
                text: "OnlyAudio"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0, 1, 1, 1
                font_style: "H6"
            MDLabel:
                id: track_meta
                text: "- / -"
                halign: "center"
                theme_text_color: "Secondary"
                font_style: "Caption"

        # PROGRESSION
        MDBoxLayout:
            adaptive_height: True
            MDLabel:
                id: lbl_curr
                text: "0:00"
                theme_text_color: "Secondary"
                font_style: "Caption"
            MDLabel:
                id: lbl_dur
                text: "0:00"
                theme_text_color: "Secondary"
                font_style: "Caption"
                halign: "right"
        MDProgressBar:
            id: progress
            value: 0
            max: 100
            color: 0, 1, 1, 1
            min_height: "6dp"

        # BOUTONS
        MDBoxLayout:
            adaptive_height: True
            spacing: "15dp"
            pos_hint: {"center_x": 0.5}
            padding: [0, 10, 0, 10]
            MDIconButton:
                icon: "shuffle"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("shuffle")
            MDIconButton:
                icon: "skip-previous"
                icon_size: "42dp"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("prev")
            MDIconButton:
                id: btn_play
                icon: "play-circle"
                icon_size: "74dp"
                theme_text_color: "Custom"
                text_color: 0, 1, 1, 1
                on_release: root.send_cmd("play_pause")
            MDIconButton:
                icon: "skip-next"
                icon_size: "42dp"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("next")
            MDIconButton:
                icon: "repeat"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("repeat")

        # VOLUME
        MDBoxLayout:
            adaptive_height: True
            spacing: "30dp"
            pos_hint: {"center_x": 0.5}
            MDIconButton:
                icon: "volume-minus"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("vol_down")
            MDIconButton:
                icon: "volume-plus"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.send_cmd("vol_up")
'''

class MainScreen(MDScreen):
    default_ip = StringProperty(DEFAULT_IP)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update_status, 1)
    def send_cmd(self, cmd):
        ip = self.ids.ip_input.text
        threading.Thread(target=self._req, args=(f"http://{ip}:{PORT}/{cmd}",)).start()
    def _req(self, url):
        try: requests.get(url, timeout=0.5)
        except: pass
    def check_connection(self):
        self.update_status(0)
    def update_status(self, dt):
        ip = self.ids.ip_input.text
        threading.Thread(target=self._fetch, args=(f"http://{ip}:{PORT}/status",)).start()
    def _fetch(self, url):
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                data = r.json()
                Clock.schedule_once(lambda d: self.apply_data(data), 0)
        except: pass
    def apply_data(self, data):
        self.ids.track_title.text = data.get('title', "...")
        self.ids.track_artist.text = data.get('artist', "")
        self.ids.track_meta.text = f"{data.get('album','')} - {data.get('year','')}"
        dur = data.get('dur', 1); pos = data.get('pos', 0)
        if dur > 0: self.ids.progress.value = (pos / dur) * 100
        self.ids.lbl_curr.text = f"{int(pos/1000)//60}:{int(pos/1000)%60:02d}"
        self.ids.lbl_dur.text = f"{int(dur/1000)//60}:{int(dur/1000)%60:02d}"
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                # On charge l'image seulement si elle arrive du réseau
                im = CoreImage(io.BytesIO(base64.b64decode(b64)), ext="png")
                self.ids.cover_image.texture = im.texture
            except: pass

class RemoteApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        return Builder.load_string(KV)

if __name__ == "__main__":
    RemoteApp().run()
