"""
XWarp AI 专线极简客户端
Author: howellxuKing
Features: 一键极简开关 + KEY 激活 + 智能白名单分流
"""

import sys
import os
import json
import base64
import urllib.parse
import threading
import subprocess
import winreg
import ctypes
from PIL import Image
import customtkinter as ctk

# 设置外观主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LOCAL_HTTP_PORT = 10809
LOCAL_SOCKS_PORT = 10808


class WindowsProxyManager:
    """Windows 系统代理控制器 (基于 Win32 API 与注册表)"""
    INTERNET_SETTINGS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    @staticmethod
    def set_system_proxy(enable: bool, proxy_server: str = f"127.0.0.1:{LOCAL_HTTP_PORT}"):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WindowsProxyManager.INTERNET_SETTINGS_KEY, 0, winreg.KEY_WRITE) as key:
                if enable:
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_server)
                    winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>;*.cn;*.baidu.com;*.qq.com;*.bilibili.com;*.taobao.com;*.jd.com")
                else:
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            # 通知系统网络设置已变更
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
            internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
            return True
        except Exception as e:
            print(f"[ProxyManager] 注册表修改失败: {e}")
            return False


class XWarpApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("XWarp AI 专线客户端")
        self.geometry("460x640")
        self.resizable(False, False)
        self.configure(fg_color="#09090b")

        self.current_key = None
        self.parsed_node = None
        self.is_connected = False
        self.core_process = None

        self.load_local_config()
        self.init_ui()

        # 退出时恢复系统代理
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_local_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_key = data.get("key")
                    self.parsed_node = data.get("node")
            except Exception:
                pass

    def save_local_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"key": self.current_key, "node": self.parsed_node}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("保存配置失败:", e)

    def parse_xwarp_key(self, key_str: str):
        key_str = key_str.strip()
        raw_uri = key_str
        if key_str.startswith("XWARP://"):
            b64_content = key_str[8:]
            try:
                raw_uri = base64.b64decode(b64_content).decode("utf-8")
            except Exception:
                return None

        if not raw_uri.startswith("hy2://"):
            return None

        try:
            url_part = raw_uri[6:]
            auth_and_host, query_str = url_part.split("/?", 1) if "/?" in url_part else (url_part, "")
            auth, host_port = auth_and_host.split("@", 1)
            host, port = host_port.split(":", 1)
            query = urllib.parse.parse_qs(query_str.split("#")[0])

            return {
                "server": host,
                "port": int(port),
                "auth": auth,
                "obfs": query.get("obfs", ["salamander"])[0],
                "obfs_password": query.get("obfs-password", [""])[0],
                "sni": query.get("sni", ["gateway.icloud.com"])[0],
                "insecure": query.get("insecure", ["1"])[0] == "1",
                "raw_uri": raw_uri
            }
        except Exception as e:
            print("解析 URI 失败:", e)
            return None

    def init_ui(self):
        # 顶栏 Logo 展示
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(28, 10), padx=20, fill="x")

        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(72, 72))
            self.logo_label = ctk.CTkLabel(self.header_frame, text="", image=self.logo_img)
            self.logo_label.pack()

        # 标题文本
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="XWARP",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#e11d48"
        )
        self.title_label.pack(pady=(6, 2))

        self.sub_label = ctk.CTkLabel(
            self.header_frame,
            text="全球 AI 极速专线 · 智能分流",
            font=ctk.CTkFont(size=12),
            text_color="#71717a"
        )
        self.sub_label.pack()

        # 主内容区域容器
        self.main_container = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=16, border_width=1, border_color="#27272a")
        self.main_container.pack(pady=16, padx=24, fill="both", expand=True)

        if not self.parsed_node:
            self.render_activation_ui()
        else:
            self.render_connected_ui()

    def render_activation_ui(self):
        # 清除容器内容
        for widget in self.main_container.winfo_children():
            widget.destroy()

        prompt_label = ctk.CTkLabel(
            self.main_container,
            text="首次使用请激活",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#fafafa"
        )
        prompt_label.pack(pady=(36, 6))

        desc_label = ctk.CTkLabel(
            self.main_container,
            text="请在下方粘贴您获得的专属激活码 KEY\n激活后即可一键连接全球主流 AI 官网",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa",
            justify="center"
        )
        desc_label.pack(pady=(0, 20))

        self.key_entry = ctk.CTkEntry(
            self.main_container,
            placeholder_text="粘贴 XWARP:// 激活码...",
            height=44,
            corner_radius=10,
            fg_color="#09090b",
            border_color="#3f3f46",
            text_color="#fafafa"
        )
        self.key_entry.pack(fill="x", padx=24, pady=10)

        self.activate_btn = ctk.CTkButton(
            self.main_container,
            text="🚀 立即激活",
            height=46,
            corner_radius=10,
            fg_color="#e11d48",
            hover_color="#be123c",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.on_activate_click
        )
        self.activate_btn.pack(fill="x", padx=24, pady=(12, 10))

        self.status_msg = ctk.CTkLabel(self.main_container, text="", font=ctk.CTkFont(size=12), text_color="#ef4444")
        self.status_msg.pack(pady=4)

    def on_activate_click(self):
        key_text = self.key_entry.get().strip()
        parsed = self.parse_xwarp_key(key_text)
        if not parsed:
            self.status_msg.configure(text="无效的激活码格式，请核对后重试", text_color="#ef4444")
            return

        self.current_key = key_text
        self.parsed_node = parsed
        self.save_local_config()
        self.render_connected_ui()

    def render_connected_ui(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # 状态徽章
        self.status_badge = ctk.CTkLabel(
            self.main_container,
            text="● 未连接",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#71717a"
        )
        self.status_badge.pack(pady=(28, 4))

        # 节点简要信息
        node_info = f"专线节点: {self.parsed_node['server']}"
        self.node_info_label = ctk.CTkLabel(
            self.main_container,
            text=node_info,
            font=ctk.CTkFont(size=11),
            text_color="#52525b"
        )
        self.node_info_label.pack(pady=(0, 20))

        # 核心超大开关按钮
        self.toggle_btn = ctk.CTkButton(
            self.main_container,
            text="⚡ 一键开启 AI 专线",
            height=68,
            corner_radius=14,
            fg_color="#e11d48",
            hover_color="#be123c",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.on_toggle_proxy
        )
        self.toggle_btn.pack(fill="x", padx=28, pady=10)

        # 白名单放行提示框
        info_box = ctk.CTkFrame(self.main_container, fg_color="#09090b", corner_radius=10, border_width=1, border_color="#27272a")
        info_box.pack(fill="x", padx=24, pady=(20, 10))

        tags = ["ChatGPT", "Claude", "Perplexity", "Midjourney", "DeepSeek", "Suno"]
        tags_text = "  ·  ".join(tags)

        ctk.CTkLabel(
            info_box,
            text="[ 已加速的国外 AI 工具 ]",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e11d48"
        ).pack(pady=(10, 4))

        ctk.CTkLabel(
            info_box,
            text=tags_text + "\n\n(国内网页与应用自动直连，不耗专线网速)",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa",
            justify="center"
        ).pack(pady=(0, 10))

        # 底部小按钮：更换 KEY
        reset_btn = ctk.CTkButton(
            self.main_container,
            text="更换激活码",
            font=ctk.CTkFont(size=11),
            text_color="#71717a",
            fg_color="transparent",
            hover_color="#27272a",
            width=80,
            height=26,
            command=self.on_reset_key
        )
        reset_btn.pack(side="bottom", pady=12)

    def on_toggle_proxy(self):
        if not self.is_connected:
            self.connect_proxy()
        else:
            self.disconnect_proxy()

    def get_core_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "xwarp-core.exe")

    def generate_client_config(self):
        node = self.parsed_node
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "xwarp_client.yaml")
        
        content = f"""server: {node['server']}:{node['port']}
auth: {node['auth']}
tls:
  sni: {node['sni']}
  insecure: {str(node['insecure']).lower()}
obfs:
  type: {node['obfs']}
  {node['obfs']}:
    password: {node['obfs_password']}
http:
  listen: 127.0.0.1:{LOCAL_HTTP_PORT}
socks5:
  listen: 127.0.0.1:{LOCAL_SOCKS_PORT}
bandwidth:
  up: 50 mbps
  down: 200 mbps
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        return config_path

    def on_toggle_proxy(self):
        if not self.is_connected:
            self.connect_proxy()
        else:
            self.disconnect_proxy()

    def connect_proxy(self):
        core_exe = self.get_core_path()
        if not os.path.exists(core_exe):
            self.status_badge.configure(text="● 错误: 缺少核心组件 xwarp-core.exe", text_color="#ef4444")
            return

        try:
            config_file = self.generate_client_config()
            CREATE_NO_WINDOW = 0x08000000
            self.core_process = subprocess.Popen(
                [core_exe, "client", "-c", config_file],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            self.status_badge.configure(text=f"● 核心启动失败: {e}", text_color="#ef4444")
            return

        # 开启 Windows 系统代理
        success = WindowsProxyManager.set_system_proxy(True)
        if success:
            self.is_connected = True
            self.status_badge.configure(text="● 已连接 (AI 专线高速运行中)", text_color="#22c55e")
            self.toggle_btn.configure(
                text="✓ 专线已开启 (点击关闭)",
                fg_color="#15803d",
                hover_color="#166534"
            )
        else:
            self.status_badge.configure(text="● 开启代理失败，请检查权限", text_color="#ef4444")

    def disconnect_proxy(self):
        if self.core_process:
            try:
                self.core_process.terminate()
                self.core_process.wait(timeout=2)
            except Exception:
                try:
                    self.core_process.kill()
                except Exception:
                    pass
            self.core_process = None

        WindowsProxyManager.set_system_proxy(False)
        self.is_connected = False
        self.status_badge.configure(text="● 未连接", text_color="#71717a")
        self.toggle_btn.configure(
            text="⚡ 一键开启 AI 专线",
            fg_color="#e11d48",
            hover_color="#be123c"
        )

    def on_reset_key(self):
        if self.is_connected:
            self.disconnect_proxy()
        self.current_key = None
        self.parsed_node = None
        self.save_local_config()
        self.render_activation_ui()

    def on_close(self):
        if self.is_connected:
            self.disconnect_proxy()
        self.destroy()


if __name__ == "__main__":
    app = XWarpApp()
    app.mainloop()
