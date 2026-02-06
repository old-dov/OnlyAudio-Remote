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

# --- CONFIGURATION ---
# Mettez l'IP de votre PC ici
DEFAULT_IP = "192.168.1.15" 
PORT = "5000"

# --- WIDGET TITRE DÉFILANT (MARQUEE) ---
class MarqueeLabel(StencilView):
    text = StringProperty("Déconnecté")
    font_style = StringProperty("H5")
    color = ObjectProperty([1, 1, 1, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = MDLabel(
            text=self.text, 
            font_style=self.font_style,
            theme_text_color="Custom",
            text_color=self.color,
            halign="center",
            valign="center",
            size_hint=(None, 1),
            adaptive_width=True
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
        self.label.width = self.label.texture_size[0] + 50 # Marge de sécurité
        
        # Si le texte est plus grand que l'écran, on anime
        if self.label.width > self.width:
            self.label.x = self.width
            duration = self.label.width / 50.0 # Vitesse de défilement
            self.anim = Animation(x=-self.label.width, duration=duration) + Animation(x=self.width, duration=0)
            self.anim.repeat = True
            self.anim.start(self.label)
        else:
            # Sinon on centre juste
            self.label.center_x = self.center_x

# --- INTERFACE GRAPHIQUE (KV) ---
KV = '''
<MainScreen>:
    # --- FOND (Image simple assombrie, pas de flou HD) ---
    FitImage:
        id: bg_image
        source: "bg_default.png"
    
    # Voile noir pour rendre le texte lisible
    MDBoxLayout:
        md_bg_color: 0, 0, 0, 0.85

    # --- CONTENU ---
    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "10dp"

        # ZONE IP (En haut)
        MDBoxLayout:
            adaptive_height: True
            spacing: "10dp"
            MDTextField:
                id: ip_input
                text: root.default_ip
                hint_text: "IP du PC"
                mode: "fill"
                text_color_focus: 0, 1, 1, 1
                theme_text_color: "Custom"
                text_color_normal: 1, 1, 1, 1
                fill_color_normal: 0.1, 0.1, 0.1, 0.5
            MDIconButton:
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: 0, 1, 1, 1
                on_release: root.check_connection()

        # POCHETTE ALBUM
        MDCard:
            size_hint: None, None
            size: "260dp", "260dp"
            pos_hint: {"center_x": 0.5}
            radius: [15,]
            elevation: 2
            md_bg_color: 0,0,0,0
            
            FitImage:
                id: cover_image
                source: "bg_default.png"
                radius: [15,]

        # INFOS PISTE
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            spacing: "5dp"

            # Titre qui défile
            MarqueeLabel:
                id: track_title
                text: "En attente..."
                font_style: "H4"
                size_hint_y: None
                height: "50dp"
                color: 1, 1, 1, 1

            MDLabel:
                id: track_artist
                text: "OnlyAudio Remote"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0, 1, 1, 1
                font_style: "H6"
                bold: True

            MDBoxLayout:
                adaptive_height: True
                pos_hint: {"center_x": 0.5}
                spacing: "10dp"
                
                MDLabel:
                    id: track_album
                    text: "-"
                    halign: "right"
                    theme_text_color: "Secondary"
                    font_style: "Caption"
                
                MDLabel:
                    id: track_year
                    text: "-"
                    halign: "left"
                    theme_text_color: "Secondary"
                    font_style: "Caption"

        # PROGRESSION
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            spacing: "5dp"
            
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

        # CONTROLES LECTURE
        MDBoxLayout:
            adaptive_height: True
            spacing: "15dp"
            pos_hint: {"center_x": 0.5}
            padding: [0, 10, 0, 10]

            MDIconButton:
                icon: "shuffle"
                theme_text_color: "Custom"
                text_color: 0.7, 0.7, 0.7, 1
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
                text_color: 0.7, 0.7, 0.7, 1
                on_release: root.send_cmd("repeat")

        # VOLUME
        MDBoxLayout:
            adaptive_height: True
            spacing: "20dp"
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
        # Met à jour le statut toutes les secondes
        Clock.schedule_interval(self.update_status, 1)

    def send_cmd(self, cmd):
        # Envoie la commande dans un thread pour ne pas figer l'app
        ip = self.ids.ip_input.text
        url = f"http://{ip}:{PORT}/{cmd}"
        threading.Thread(target=self._req_thread, args=(url,)).start()

    def _req_thread(self, url):
        try:
            requests.get(url, timeout=0.5)
        except: pass

    def check_connection(self):
        self.update_status(0)

    def update_status(self, dt):
        ip = self.ids.ip_input.text
        url = f"http://{ip}:{PORT}/status"
        threading.Thread(target=self._fetch_status, args=(url,)).start()

    def _fetch_status(self, url):
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                data = r.json()
                # On met à jour l'interface dans le thread principal
                Clock.schedule_once(lambda d: self.apply_data(data), 0)
        except:
            pass

    def apply_data(self, data):
        # 1. Textes
        self.ids.track_title.text = data.get('title', "...")
        self.ids.track_artist.text = data.get('artist', "")
        self.ids.track_album.text = data.get('album', "")
        self.ids.track_year.text = str(data.get('year', ""))
        
        # 2. Barre de progression
        dur = data.get('dur', 1)
        pos = data.get('pos', 0)
        if dur > 0:
            self.ids.progress.value = (pos / dur) * 100
            
        def fmt(ms):
            s = int(ms / 1000)
            return f"{s//60}:{s%60:02d}"
        
        self.ids.lbl_curr.text = fmt(pos)
        self.ids.lbl_dur.text = fmt(dur)

        # 3. Image (Décodage Base64)
        b64 = data.get('cover_b64', "")
        if b64:
            try:
                decoded = base64.b64decode(b64)
                data_io = io.BytesIO(decoded)
                im = CoreImage(data_io, ext="png")
                # Mise à jour des deux images (Fond + Pochette)
                self.ids.cover_image.texture = im.texture
                self.ids.bg_image.texture = im.texture
            except: pass

class RemoteApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        return Builder.load_string(KV)

if __name__ == "__main__":
    RemoteApp().run()