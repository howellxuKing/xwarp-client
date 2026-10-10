"""XWarp AI 专线的界面层；网络连接由主程序控制。"""

import math
import tkinter as tk
import customtkinter as ctk


class ClientUI:
    BG = "#0b0e14"
    CARD = "#141923"
    BORDER = "#252d3b"
    TEXT = "#f3f5fa"
    MUTED = "#8993a7"
    ACCENT = "#fb7276"
    GREEN = "#53dfb4"

    def font(self, size, bold=False):
        return ctk.CTkFont(family="Microsoft YaHei UI", size=size,
                           weight="bold" if bold else "normal")

    def label(self, parent, text, size=13, color=None, bold=False, **kwargs):
        return ctk.CTkLabel(parent, text=text, font=self.font(size, bold),
                           text_color=color or self.TEXT, **kwargs)

    def init_ui(self):
        self.configure(fg_color=self.BG)
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.pack(fill="both", expand=True, padx=28, pady=(24, 18))

        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x")
        mark = ctk.CTkFrame(header, width=36, height=36,
                           corner_radius=11, fg_color=self.ACCENT)
        mark.pack(side="left")
        mark.pack_propagate(False)
        self.label(mark, "X", 23, "#151820", True).pack(expand=True)
        self.label(header, "XWARP", 18, bold=True).pack(side="left", padx=10)
        self.label(header, "CONNECT", 10, self.MUTED).pack(side="left", pady=(4, 0))
        self.label(header, "WINDOWS", 10, self.MUTED).pack(side="right")

        hero = ctk.CTkFrame(shell, fg_color="transparent")
        hero.pack(fill="x", pady=(20, 16))
        self.label(hero, "专为 AI 体验打造", 12, self.ACCENT).pack(anchor="w")
        self.label(hero, "AI 专线", 38, bold=True).pack(anchor="w", pady=(0, 1))
        self.label(hero, "让灵感畅行，让 AI 随时在线。", 13, self.MUTED).pack(anchor="w")

        self.main_container = ctk.CTkFrame(
            shell, fg_color=self.CARD, corner_radius=20,
            border_width=1, border_color=self.BORDER)
        self.main_container.pack(fill="both", expand=True)

        services = ctk.CTkFrame(shell, fg_color="transparent")
        services.pack(fill="x", pady=(16, 0))
        row = ctk.CTkFrame(services, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        self.label(row, "你的 AI 工具，在这里连接", 12, bold=True).pack(side="left")
        self.label(row, "AI 专属", 10, self.ACCENT).pack(side="right")
        grid = ctk.CTkFrame(services, fg_color="transparent")
        grid.pack(fill="x")
        for index, name in enumerate(("ChatGPT", "Claude", "Perplexity",
                                      "Midjourney", "Suno", "Grok")):
            column = index % 3
            grid.grid_columnconfigure(column, weight=1, uniform="services")
            chip = ctk.CTkFrame(grid, fg_color="#171d28", corner_radius=9)
            chip.grid(row=index // 3, column=column, sticky="ew",
                      padx=(0 if column == 0 else 4, 0 if column == 2 else 4),
                      pady=(0 if index < 3 else 7, 0))
            self.label(chip, name, 11, "#bec7d7", height=31).pack()
        self.label(services, "可访问的服务以节点白名单为准", 10, self.MUTED).pack(anchor="w", pady=(8, 0))

        footer = ctk.CTkFrame(shell, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))
        self.label(footer, "XWarp AI 专线", 10, self.MUTED).pack(side="left")
        self.label(footer, "v1.1.0  /  xwarp.cc", 10, "#667287").pack(side="right")

        if self.parsed_node:
            self.render_connected_ui()
        else:
            self.render_activation_ui()

    def clear_card(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def render_activation_ui(self):
        self.clear_card()
        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)
        self.label(content, "01  /  激活专线", 11, self.ACCENT, True).pack(anchor="w")
        self.label(content, "开启你的 AI 连接", 22, bold=True).pack(anchor="w", pady=(14, 4))
        self.label(content, "粘贴专属激活码，即可添加你的 AI 节点。", 12, self.MUTED).pack(anchor="w")

        entry_header = ctk.CTkFrame(content, fg_color="transparent")
        entry_header.pack(fill="x", pady=(24, 8))
        self.label(entry_header, "专线激活码", 11, "#bbc4d5").pack(side="left")
        ctk.CTkButton(entry_header, text="粘贴", width=48, height=23,
                      fg_color="transparent", hover_color=self.BORDER,
                      text_color=self.ACCENT, font=self.font(11),
                      command=self.paste_key).pack(side="right")
        self.key_entry = ctk.CTkEntry(
            content, placeholder_text="XWARP://…", height=48,
            corner_radius=10, fg_color="#0d121c", border_color="#343e51",
            border_width=1, text_color=self.TEXT,
            placeholder_text_color="#68748b", font=self.font(13), show="•")
        self.key_entry.pack(fill="x")
        self.key_entry.bind("<Return>", lambda event: self.on_activate_click())
        self.activate_btn = ctk.CTkButton(
            content, text="激活 AI 专线  →", height=48, corner_radius=10,
            fg_color=self.ACCENT, hover_color="#ed626b", text_color="#171923",
            font=self.font(14, True), command=self.on_activate_click)
        self.activate_btn.pack(fill="x", pady=(16, 0))
        self.status_msg = self.label(content, "激活码仅保存在这台电脑上", 11, self.MUTED,
                                     wraplength=360, justify="left")
        self.status_msg.pack(anchor="w", pady=(12, 0))

    def paste_key(self):
        try:
            value = self.clipboard_get().strip()
        except tk.TclError:
            self.status_msg.configure(text="剪贴板里还没有激活码，请复制后重试。",
                                      text_color=self.ACCENT)
            return
        self.key_entry.delete(0, "end")
        self.key_entry.insert(0, value)
        self.key_entry.focus_set()
        self.status_msg.configure(text="已粘贴，点击激活按钮继续。", text_color=self.MUTED)

    def on_activate_click(self):
        value = self.key_entry.get().strip()
        parsed = self.parse_xwarp_key(value)
        if not parsed:
            self.status_msg.configure(text="激活码格式不正确，请检查后重试。",
                                      text_color=self.ACCENT)
            return
        self.current_key = value
        self.parsed_node = parsed
        self.save_local_config()
        self.render_connected_ui()

    def render_connected_ui(self):
        self.clear_card()
        top = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 0))
        self.label(top, "AI 专线连接", 12, bold=True).pack(side="left")
        self.status_badge = self.label(top, "● 尚未连接", 11, self.MUTED,
                                       wraplength=270, justify="right")
        self.status_badge.pack(side="right")

        self.power_canvas = tk.Canvas(self.main_container, width=260, height=170,
                                      bg=self.CARD, highlightthickness=0, bd=0)
        self.power_canvas.pack(pady=(5, 0))
        self.power_canvas.bind("<Button-1>", self.on_power_click)
        self.power_canvas.bind("<Motion>", self.on_power_hover)
        self.draw_power(False)
        self.connection_hint = self.label(self.main_container, "你的 AI 专线已就绪", 16, bold=True)
        self.connection_hint.pack(pady=(0, 4))
        self.node_info_label = self.label(self.main_container, "节点已配置 · 等待开启", 11, self.MUTED)
        self.node_info_label.pack()
        self.toggle_btn = ctk.CTkButton(
            self.main_container, text="开启 AI 专线", height=46, corner_radius=11,
            fg_color=self.ACCENT, hover_color="#ed626b", text_color="#171923",
            font=self.font(14, True), command=self.on_toggle_proxy)
        self.toggle_btn.pack(fill="x", padx=24, pady=(10, 8))
        ctk.CTkButton(self.main_container, text="更换激活码", width=110, height=24,
                      fg_color="transparent", hover_color=self.BORDER,
                      text_color=self.MUTED, font=self.font(11),
                      command=self.on_reset_key).pack(pady=(0, 12))

    def on_power_click(self, event):
        if (event.x - 130) ** 2 + (event.y - 85) ** 2 <= 62 ** 2:
            self.on_toggle_proxy()

    def on_power_hover(self, event):
        inside = (event.x - 130) ** 2 + (event.y - 85) ** 2 <= 62 ** 2
        self.power_canvas.configure(cursor="hand2" if inside else "")

    def draw_power(self, active):
        canvas = self.power_canvas
        canvas.delete("all")
        color = self.GREEN if active else self.ACCENT
        for radius in (79, 68):
            canvas.create_oval(130-radius, 85-radius, 130+radius, 85+radius,
                               outline="#283447" if active else "#252d3b", width=1)
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            x, y = 130 + 79 * math.cos(radians), 85 + 79 * math.sin(radians)
            canvas.create_oval(x-2, y-2, x+2, y+2, fill="#40516a", outline="")
        canvas.create_oval(69, 24, 191, 146, fill="#152a29" if active else "#30212b",
                           outline=color, width=2)
        canvas.create_arc(109, 64, 151, 108, start=135, extent=270,
                          style="arc", outline=color, width=4)
        canvas.create_line(130, 57, 130, 83, fill=color, width=4, capstyle="round")

    def update_connection_ui(self, active):
        self.draw_power(active)
        self.status_badge.configure(text="● 专线已开启" if active else "● 尚未连接",
                                    text_color=self.GREEN if active else self.MUTED)
        self.connection_hint.configure(text="AI 专线已开启" if active else "你的 AI 专线已就绪")
        self.node_info_label.configure(text="系统代理已开启 · 通过节点访问 AI" if active
                                       else "节点已配置 · 等待开启")
        self.toggle_btn.configure(text="关闭 AI 专线" if active else "开启 AI 专线",
                                  fg_color="#243a38" if active else self.ACCENT,
                                  hover_color="#2f4a45" if active else "#ed626b",
                                  text_color=self.GREEN if active else "#171923")
