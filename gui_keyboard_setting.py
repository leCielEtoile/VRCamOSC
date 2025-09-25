# gui_keyboard_setting.py - キーボード設定GUI

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from typing import Dict, Optional, Any, Callable
from pynput import keyboard


class KeyCaptureDialog:
    """キー入力キャプチャダイアログ"""
    
    def __init__(self, parent, target_name: str):
        self.parent = parent
        self.target_name = target_name
        self.captured_key = None
        self.dialog = None
        self.listener = None
        
    def show(self) -> Optional[Any]:
        """ダイアログ表示してキー入力を待機"""
        # ダイアログ作成
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"{self.target_name} - キー設定")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 中央配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (200)
        y = (self.dialog.winfo_screenheight() // 2) - (125)
        self.dialog.geometry(f"400x250+{x}+{y}")
        
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(main_frame, 
                               text=f"{self.target_name} のキーを設定",
                               font=("", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 説明
        info_label = ttk.Label(main_frame,
                              text="設定したいキーを押してください\n"
                                   "（テンキー、文字キー、ファンクションキーなど）",
                              justify=tk.CENTER,
                              font=("", 10))
        info_label.pack(pady=(0, 15))
        
        # 状態表示
        self.status_label = ttk.Label(main_frame, 
                                     text="⌨️ キー入力を待機中...",
                                     foreground="blue",
                                     font=("", 11))
        self.status_label.pack(pady=(0, 20))
        
        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 20))
        self.progress.start()
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="キャンセル", 
                  command=self._cancel,
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="クリア", 
                  command=self._clear,
                  width=15).pack(side=tk.LEFT)
        
        # キーリスナー開始
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            suppress=False
        )
        self.listener.start()
        
        # モーダルダイアログとして実行
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
        self.dialog.wait_window()
        
        return self.captured_key
    
    def _on_key_press(self, key):
        """キー押下処理"""
        try:
            self.captured_key = key
            
            # キー名取得
            key_name = self._get_key_display_name(key)
            
            # UI更新（メインスレッドで実行）
            self.dialog.after(0, lambda: self._show_captured_key(key_name))
            
            # 少し待ってからダイアログを閉じる
            self.dialog.after(1500, self._close_dialog)
            
        except Exception as e:
            print(f"キー処理エラー: {e}")
    
    def _get_key_display_name(self, key) -> str:
        """表示用キー名取得"""
        try:
            # VKコードがある場合
            if hasattr(key, 'vk') and key.vk is not None:
                # ファンクションキーの場合
                if 112 <= key.vk <= 123:
                    return f"F{key.vk - 111}"
                
                # テンキーの場合
                if 97 <= key.vk <= 105:
                    return f"Numpad {key.vk - 96}"
                elif key.vk == 96:
                    return "Numpad 0"
                
                # テンキー演算子
                elif key.vk == 106:
                    return "Multiply"      # * (乗算)
                elif key.vk == 107:
                    return "Add"           # + (加算)
                elif key.vk == 109:
                    return "Subtract"      # - (減算)
                elif key.vk == 110:
                    return "Decimal"       # . (小数点)
                elif key.vk == 111:
                    return "Divide"        # / (除算)
                
                # 特殊キーの場合
                for key_attr in dir(keyboard.Key):
                    if not key_attr.startswith('_'):
                        try:
                            key_value = getattr(keyboard.Key, key_attr)
                            if hasattr(key_value, 'value') and key_value.value == key.vk:
                                return key_attr.replace('_', ' ').title()
                        except:
                            continue
                
                # 文字キーの場合
                if hasattr(key, 'char') and key.char:
                    return key.char.upper()
                
                return f"VK_{key.vk}"
            
            # nameがある場合
            if hasattr(key, 'name'):
                return key.name
            
            # charがある場合
            if hasattr(key, 'char') and key.char:
                return key.char
            
            return str(key)
        except:
            return "unknown_key"
    
    def _show_captured_key(self, key_name: str):
        """キャプチャしたキーを表示"""
        self.progress.stop()
        self.status_label.config(
            text=f"✅ キーを設定しました: {key_name}",
            foreground="green"
        )
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        if self.listener:
            self.listener.stop()
        self.dialog.destroy()
    
    def _cancel(self):
        """キャンセル処理"""
        self.captured_key = None
        if self.listener:
            self.listener.stop()
        self.dialog.destroy()
    
    def _clear(self):
        """クリア処理（キー設定を削除）"""
        self.captured_key = "CLEAR"
        if self.listener:
            self.listener.stop()
        self.dialog.destroy()


class KeyboardSettingsPanel:
    """キーボード設定パネル"""
    
    def __init__(self, parent, keyboard_handler, update_callback: Optional[Callable] = None):
        self.parent = parent
        self.keyboard_handler = keyboard_handler
        self.update_callback = update_callback
        
        # 設定ファイル
        self.config_file = Path("keyboard_config.json")
        
        # メインフレーム
        self.frame = ttk.LabelFrame(parent, text="⌨️ テンキー操作キー設定", padding="15")
        
        # 現在のキー設定
        self.current_bindings = {}
        self.current_advanced_bindings = {}
        
        # 高度機能定義
        self.advanced_functions = [
            ("copy_current", "📋 現在位置→クリップボード", "Decimal"),
            ("move_clipboard", "📥 クリップボード→移動", "Numpad 0"),
            ("toggle_flight", "✈️ 飛行モード切り替え", "Divide"),
            ("toggle_lookatme", "👁️ LookAtMe切り替え", "Multiply")
        ]
        
        self._create_widgets()
        self._load_current_settings()
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # 説明
        info_frame = ttk.Frame(self.frame)
        info_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(info_frame,
                  text="各Pinに対応するキーを自由に設定できます（推奨：テンキーでの操作）",
                  font=("", 10)).pack()
        
        ttk.Label(info_frame,
                  text="デフォルト: テンキー1-9 (短押し=移動、長押し=保存) + 演算子キー(. 0 / *)",
                  font=("", 9),
                  foreground="gray").pack()
        
        # Pin操作キー設定
        pin_settings_frame = ttk.Frame(self.frame)
        pin_settings_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # ヘッダー
        headers = [("Pin", 60), ("設定キー", 150), ("操作", 100), ("", 80)]
        for col, (header, width) in enumerate(headers):
            label = ttk.Label(pin_settings_frame, text=header, font=("", 10, "bold"))
            label.grid(row=0, column=col, padx=5, pady=5, sticky=tk.W)
            if width:
                pin_settings_frame.grid_columnconfigure(col, minsize=width)
        
        # Pin 1-9の設定行
        self.key_labels = {}
        self.set_buttons = {}
        self.clear_buttons = {}
        
        for pin in range(1, 10):
            row = pin
            
            # Pin番号
            pin_label = ttk.Label(pin_settings_frame, text=f"Pin {pin}")
            pin_label.grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
            
            # 現在のキー表示
            self.key_labels[pin] = ttk.Label(pin_settings_frame, text="Numpad {}".format(pin), 
                                           relief="sunken", width=20)
            self.key_labels[pin].grid(row=row, column=1, padx=5, pady=3, sticky=(tk.W, tk.E))
            
            # 設定ボタン
            self.set_buttons[pin] = ttk.Button(pin_settings_frame, text="🔧 設定",
                                             command=lambda p=pin: self._set_key(p))
            self.set_buttons[pin].grid(row=row, column=2, padx=5, pady=3)
            
            # クリアボタン
            self.clear_buttons[pin] = ttk.Button(pin_settings_frame, text="🗑️ クリア",
                                               command=lambda p=pin: self._clear_key(p))
            self.clear_buttons[pin].grid(row=row, column=3, padx=5, pady=3)
        
        # 高度機能キー設定
        advanced_frame = ttk.LabelFrame(self.frame, text="🚀 高度機能キー設定", padding="15")
        advanced_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(15, 0))
        advanced_frame.grid_columnconfigure(1, weight=1)
        
        # 高度機能ヘッダー
        headers_advanced = [("機能", 180), ("設定キー", 120), ("操作", 100), ("", 80)]
        for col, (header, width) in enumerate(headers_advanced):
            label = ttk.Label(advanced_frame, text=header, font=("", 10, "bold"))
            label.grid(row=1, column=col, padx=5, pady=5, sticky=tk.W)
            if width:
                advanced_frame.grid_columnconfigure(col, minsize=width)
        
        # 高度機能設定行
        self.advanced_key_labels = {}
        self.advanced_set_buttons = {}
        self.advanced_clear_buttons = {}
        
        for idx, (action, description, default_key) in enumerate(self.advanced_functions):
            row = idx + 2
            
            # 機能説明
            func_label = ttk.Label(advanced_frame, text=description)
            func_label.grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
            
            # 現在のキー表示
            self.advanced_key_labels[action] = ttk.Label(advanced_frame, text=default_key, 
                                                      relief="sunken", width=15)
            self.advanced_key_labels[action].grid(row=row, column=1, padx=5, pady=3, sticky=(tk.W, tk.E))
            
            # 設定ボタン
            self.advanced_set_buttons[action] = ttk.Button(advanced_frame, text="🔧 設定",
                                                        command=lambda a=action: self._set_advanced_key(a))
            self.advanced_set_buttons[action].grid(row=row, column=2, padx=5, pady=3)
            
            # クリアボタン
            self.advanced_clear_buttons[action] = ttk.Button(advanced_frame, text="🗑️ クリア",
                                                          command=lambda a=action: self._clear_advanced_key(a))
            self.advanced_clear_buttons[action].grid(row=row, column=3, padx=5, pady=3)
        
        # 設定操作ボタン
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(15, 10))
        
        ttk.Button(button_frame, text="🔄 デフォルトに戻す",
                  command=self._reset_to_default).pack(side=tk.LEFT, padx=(0, 10))
        
        # 長押し設定
        threshold_frame = ttk.LabelFrame(self.frame, text="⏱️ 長押し設定")
        threshold_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(15, 0))
        threshold_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(threshold_frame, text="長押し判定時間:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.threshold_var = tk.DoubleVar(value=0.8)
        threshold_control = ttk.Frame(threshold_frame)
        threshold_control.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        self.threshold_scale = ttk.Scale(threshold_control, from_=0.3, to=2.0, 
                                       variable=self.threshold_var, orient=tk.HORIZONTAL)
        self.threshold_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.threshold_label = ttk.Label(threshold_control, text="0.8秒")
        self.threshold_label.pack(side=tk.LEFT)
        
        # 値変更時の更新
        self.threshold_var.trace('w', self._on_threshold_changed)
    
    def _load_current_settings(self):
        """現在の設定を読み込み"""
        # Pin操作キーの読み込み
        if hasattr(self.keyboard_handler, 'get_key_bindings'):
            bindings = self.keyboard_handler.get_key_bindings()
            self.current_bindings = bindings
        else:
            self._load_default_settings()
        
        # 高度機能キーの読み込み
        if hasattr(self.keyboard_handler, 'get_special_key_bindings'):
            advanced_bindings = self.keyboard_handler.get_special_key_bindings()
            self.current_advanced_bindings = advanced_bindings
        else:
            self._load_default_advanced_settings()
        
        # 表示更新
        self._update_display()
        
        # 長押し閾値読み込み
        if hasattr(self.keyboard_handler, 'long_press_threshold'):
            self.threshold_var.set(self.keyboard_handler.long_press_threshold)
    
    def _load_default_settings(self):
        """デフォルトPin操作設定読み込み"""
        self.current_bindings = {
            1: "Numpad 1", 2: "Numpad 2", 3: "Numpad 3",
            4: "Numpad 4", 5: "Numpad 5", 6: "Numpad 6", 
            7: "Numpad 7", 8: "Numpad 8", 9: "Numpad 9"
        }
    
    def _load_default_advanced_settings(self):
        """デフォルト高度機能設定読み込み"""
        self.current_advanced_bindings = {
            "copy_current": "Decimal",
            "move_clipboard": "Numpad 0", 
            "toggle_flight": "Divide",
            "toggle_lookatme": "Multiply"
        }
    
    def _update_display(self):
        """表示更新"""
        # Pin操作キー表示更新
        for pin in range(1, 10):
            key_name = self.current_bindings.get(pin, "未設定")
            if key_name == "未設定":
                self.key_labels[pin].config(text=key_name, foreground="gray")
            else:
                self.key_labels[pin].config(text=key_name, foreground="black")
        
        # 高度機能キー表示更新
        for action, label_widget in self.advanced_key_labels.items():
            key_name = self.current_advanced_bindings.get(action, "未設定")
            if key_name == "未設定":
                label_widget.config(text=key_name, foreground="gray")
            else:
                label_widget.config(text=key_name, foreground="black")
    
    def _set_key(self, pin_number: int):
        """Pin操作キー設定"""
        try:
            # キーキャプチャダイアログ表示
            dialog = KeyCaptureDialog(self.parent, f"Pin {pin_number}")
            captured_key = dialog.show()
            
            if captured_key == "CLEAR":
                # クリア処理
                self._clear_key(pin_number)
                return
            elif captured_key:
                # キー名取得
                key_name = dialog._get_key_display_name(captured_key)
                
                # 他のPin操作キーとの競合チェック
                for existing_pin, existing_key in self.current_bindings.items():
                    if existing_pin != pin_number and existing_key == key_name:
                        result = messagebox.askyesno(
                            "キー重複", 
                            f"キー '{key_name}' は既にPin {existing_pin}に設定されています。\n"
                            f"Pin {existing_pin}の設定を削除してPin {pin_number}に設定しますか？"
                        )
                        if result:
                            del self.current_bindings[existing_pin]
                        else:
                            return
                
                # 高度機能キーとの競合チェック
                action_names = {
                    "copy_current": "現在位置→クリップボード",
                    "move_clipboard": "クリップボード→移動",
                    "toggle_flight": "飛行モード切り替え",
                    "toggle_lookatme": "LookAtMe切り替え"
                }
                
                for existing_action, existing_key in self.current_advanced_bindings.items():
                    if existing_key == key_name:
                        action_name = action_names.get(existing_action, existing_action)
                        result = messagebox.askyesno(
                            "キー重複", 
                            f"キー '{key_name}' は既に{action_name}機能に設定されています。\n"
                            f"{action_name}機能の設定を削除してPin {pin_number}に設定しますか？"
                        )
                        if result:
                            del self.current_advanced_bindings[existing_action]
                        else:
                            return
                
                # キー設定
                self.current_bindings[pin_number] = key_name
                
                # キーボードハンドラーに設定反映
                if hasattr(self.keyboard_handler, 'set_key_binding'):
                    self.keyboard_handler.set_key_binding(pin_number, captured_key)
                
                # 表示更新
                self._update_display()
                
                messagebox.showinfo("設定完了", 
                                   f"Pin {pin_number} に '{key_name}' を設定しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"キー設定エラー: {e}")
    
    def _clear_key(self, pin_number: int):
        """Pin操作キー設定クリア"""
        try:
            if pin_number in self.current_bindings:
                del self.current_bindings[pin_number]
                
                # キーボードハンドラーから削除
                if hasattr(self.keyboard_handler, 'remove_key_binding'):
                    self.keyboard_handler.remove_key_binding(pin_number)
                
                # 表示更新
                self._update_display()
                
                messagebox.showinfo("クリア完了", 
                                   f"Pin {pin_number} のキー設定をクリアしました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"キー設定クリアエラー: {e}")
    
    def _set_advanced_key(self, action: str):
        """高度機能キー設定"""
        try:
            # 機能名を日本語に変換
            action_names = {
                "copy_current": "現在位置→クリップボード",
                "move_clipboard": "クリップボード→移動",
                "toggle_flight": "飛行モード切り替え",
                "toggle_lookatme": "LookAtMe切り替え"
            }
            action_name = action_names.get(action, action)
            
            # キーキャプチャダイアログ表示
            dialog = KeyCaptureDialog(self.parent, f"{action_name}機能")
            captured_key = dialog.show()
            
            if captured_key == "CLEAR":
                # クリア処理
                self._clear_advanced_key(action)
                return
            elif captured_key:
                # キー名取得
                key_name = dialog._get_key_display_name(captured_key)
                
                # Pin操作キーとの競合チェック
                for existing_pin, existing_key in self.current_bindings.items():
                    if existing_key == key_name:
                        result = messagebox.askyesno(
                            "キー競合", 
                            f"キー '{key_name}' は既にPin {existing_pin}に設定されています。\n"
                            f"Pin {existing_pin}の設定を削除して{action_name}機能に設定しますか？"
                        )
                        if result:
                            del self.current_bindings[existing_pin]
                        else:
                            return
                
                # 他の高度機能キーとの競合チェック
                for existing_action, existing_key in self.current_advanced_bindings.items():
                    if existing_action != action and existing_key == key_name:
                        existing_action_name = action_names.get(existing_action, existing_action)
                        result = messagebox.askyesno(
                            "キー競合", 
                            f"キー '{key_name}' は既に{existing_action_name}機能に設定されています。\n"
                            f"{existing_action_name}機能の設定を削除して{action_name}機能に設定しますか？"
                        )
                        if result:
                            del self.current_advanced_bindings[existing_action]
                        else:
                            return
                
                # キー設定
                self.current_advanced_bindings[action] = key_name
                
                # キーボードハンドラーに設定反映
                if hasattr(self.keyboard_handler, 'set_special_key_binding'):
                    self.keyboard_handler.set_special_key_binding(action, captured_key)
                
                # 表示更新
                self._update_display()
                
                messagebox.showinfo("設定完了", 
                                   f"{action_name}機能に '{key_name}' を設定しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"高度機能キー設定エラー: {e}")
    
    def _clear_advanced_key(self, action: str):
        """高度機能キー設定クリア"""
        try:
            action_names = {
                "copy_current": "現在位置→クリップボード",
                "move_clipboard": "クリップボード→移動", 
                "toggle_flight": "飛行モード切り替え",
                "toggle_lookatme": "LookAtMe切り替え"
            }
            action_name = action_names.get(action, action)
            
            if action in self.current_advanced_bindings:
                del self.current_advanced_bindings[action]
                
                # キーボードハンドラーから削除
                if hasattr(self.keyboard_handler, 'remove_special_key_binding'):
                    self.keyboard_handler.remove_special_key_binding(action)
                
                # 表示更新
                self._update_display()
                
                messagebox.showinfo("クリア完了", 
                                   f"{action_name}機能のキー設定をクリアしました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"高度機能キー設定クリアエラー: {e}")
    
    def _reset_to_default(self):
        """デフォルト設定に戻す"""
        try:
            result = messagebox.askyesno("確認", 
                                        "全設定をデフォルト設定に戻しますか？\n\n"
                                        "Pin操作: テンキー1-9\n"
                                        "高度機能: テンキー . 0 / *")
            if result:
                # Pin操作キーをデフォルトに
                self._load_default_settings()
                
                # 高度機能キーをデフォルトに
                self._load_default_advanced_settings()
                
                # キーボードハンドラーに反映
                if hasattr(self.keyboard_handler, 'setup_default_bindings'):
                    self.keyboard_handler.setup_default_bindings()
                
                self._update_display()
                messagebox.showinfo("完了", "デフォルト設定に戻しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"デフォルト設定復元エラー: {e}")
    
    def _save_settings(self):
        """設定保存"""
        try:
            # 設定データ作成
            config_data = {
                "key_bindings": self.current_bindings,
                "special_key_bindings": self.current_advanced_bindings,
                "long_press_threshold": self.threshold_var.get(),
                "version": "3.0"
            }
            
            # ファイル保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # キーボードハンドラーに反映
            if hasattr(self.keyboard_handler, 'load_config'):
                self.keyboard_handler.load_config(config_data)
            
            # コールバック実行
            if self.update_callback:
                self.update_callback()
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存エラー: {e}")
    
    def _on_threshold_changed(self, *args):
        """長押し閾値変更時の処理"""
        try:
            value = self.threshold_var.get()
            self.threshold_label.config(text=f"{value:.1f}秒")
            
            # キーボードハンドラーに反映
            if hasattr(self.keyboard_handler, 'long_press_threshold'):
                self.keyboard_handler.long_press_threshold = value
            
        except Exception as e:
            print(f"閾値変更処理エラー: {e}")
    
    def load_config_file(self):
        """設定ファイルから読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Pin操作キーバインド読み込み
                if "key_bindings" in config_data:
                    self.current_bindings = {
                        int(k): v for k, v in config_data["key_bindings"].items()
                        if str(k).isdigit() and 1 <= int(k) <= 9
                    }
                
                # 高度機能キーバインド読み込み
                if "special_key_bindings" in config_data:
                    self.current_advanced_bindings = config_data["special_key_bindings"]
                else:
                    self._load_default_advanced_settings()
                
                # 長押し閾値読み込み
                if "long_press_threshold" in config_data:
                    self.threshold_var.set(config_data["long_press_threshold"])
                
                self._update_display()
                
                return True
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
        
        return False
    
    def update_status(self):
        """定期的な状態更新"""
        try:
            # キーボードハンドラーの状態を確認して表示を更新
            if hasattr(self.keyboard_handler, 'get_status'):
                status = self.keyboard_handler.get_status()
                
                # 監視状態に応じてUIの有効/無効を切り替え
                monitoring = status.get('monitoring', False)
                
                # Pin操作ボタンの状態更新
                for pin in range(1, 10):
                    if pin in self.set_buttons:
                        self.set_buttons[pin].config(state='normal' if monitoring else 'disabled')
                        self.clear_buttons[pin].config(state='normal' if monitoring else 'disabled')
                
                # 高度機能ボタンの状態更新
                for action in self.advanced_functions:
                    action_key = action[0]
                    if action_key in self.advanced_set_buttons:
                        self.advanced_set_buttons[action_key].config(state='normal' if monitoring else 'disabled')
                        self.advanced_clear_buttons[action_key].config(state='normal' if monitoring else 'disabled')
            
        except Exception as e:
            print(f"状態更新エラー: {e}")
        
        # 1秒後に再実行
        self.frame.after(1000, self.update_status)
    
    def get_all_bindings_summary(self) -> str:
        """全キーバインドのサマリー取得"""
        try:
            summary_lines = ["=== キーバインド設定サマリー ==="]
            
            # Pin操作キー
            summary_lines.append("\n【Pin操作キー】")
            for pin in range(1, 10):
                key_name = self.current_bindings.get(pin, "未設定")
                summary_lines.append(f"  Pin {pin}: {key_name}")
            
            # 高度機能キー
            summary_lines.append("\n【高度機能キー】")
            action_names = {
                "copy_current": "現在位置→クリップボード",
                "move_clipboard": "クリップボード→移動",
                "toggle_flight": "飛行モード切り替え",
                "toggle_lookatme": "LookAtMe切り替え"
            }
            
            for action, description in action_names.items():
                key_name = self.current_advanced_bindings.get(action, "未設定")
                summary_lines.append(f"  {description}: {key_name}")
            
            # 長押し設定
            threshold = self.threshold_var.get()
            summary_lines.append(f"\n【長押し判定時間】\n  {threshold:.1f}秒")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            return f"サマリー取得エラー: {e}"


def create_keyboard_settings_window(parent, keyboard_handler, update_callback: Optional[Callable] = None):
    """キーボード設定ウィンドウ作成"""
    try:
        # 新しいウィンドウ作成
        settings_window = tk.Toplevel(parent)
        settings_window.title("⌨️ キーボード設定")
        settings_window.geometry("600x700")
        settings_window.resizable(True, False)
        settings_window.transient(parent)
        
        # 中央配置
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (300)
        y = (settings_window.winfo_screenheight() // 2) - (350)
        settings_window.geometry(f"600x700+{x}+{y}")
        
        # メインフレーム
        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # スクロール対応
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # キーボード設定パネル
        settings_panel = KeyboardSettingsPanel(scrollable_frame, keyboard_handler, update_callback)
        settings_panel.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # レイアウト
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # マウスホイール対応
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 定期更新開始
        settings_panel.update_status()
        
        # ウィンドウ終了時の処理
        def on_closing():
            try:
                # 設定を保存
                settings_panel._save_settings()
                
                # マウスホイールバインド解除
                canvas.unbind_all("<MouseWheel>")
                
                # ウィンドウ破棄
                settings_window.destroy()
                
                print("キーボード設定ウィンドウを閉じました")
                
            except Exception as e:
                print(f"設定ウィンドウ終了エラー: {e}")
                settings_window.destroy()
        
        settings_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 焦点距離設定
        settings_window.focus_set()
        
        print("キーボード設定ウィンドウを作成しました")
        
        return settings_window, settings_panel
        
    except Exception as e:
        messagebox.showerror("エラー", f"設定ウィンドウの作成に失敗しました: {e}")
        return None, None


def create_keyboard_tab(notebook, keyboard_handler, update_callback: Optional[Callable] = None):
    """キーボード設定タブ作成（ノートブック用）"""
    try:
        # タブフレーム作成
        tab_frame = ttk.Frame(notebook)
        notebook.add(tab_frame, text="⌨️ キーボード設定")
        
        # スクロール対応フレーム
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # パディング付きメインフレーム
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # キーボード設定パネル
        settings_panel = KeyboardSettingsPanel(main_frame, keyboard_handler, update_callback)
        settings_panel.frame.pack(fill=tk.BOTH, expand=True)
        
        # レイアウト
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # マウスホイール対応
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 定期更新開始
        settings_panel.update_status()
        
        print("キーボード設定タブを作成しました")
        
        return tab_frame, settings_panel
        
    except Exception as e:
        print(f"キーボード設定タブ作成エラー: {e}")
        return None, None


# テスト用メイン関数
if __name__ == "__main__":
    print("=== キーボード設定GUI テスト実行 ===")
    
    # ダミーキーボードハンドラー作成
    class DummyKeyboardHandler:
        def __init__(self):
            self.long_press_threshold = 0.8
            self.key_bindings = {1: "Numpad 1", 2: "Numpad 2", 3: "Numpad 3"}
            self.advanced_key_bindings = {
                "copy_current": "Decimal",
                "move_clipboard": "Numpad 0",
                "toggle_flight": "Divide",
                "toggle_lookatme": "Multiply"
            }
        
        def get_key_bindings(self):
            return self.key_bindings
        
        def get_special_key_bindings(self):
            return self.advanced_key_bindings
        
        def set_key_binding(self, pin_number, key_obj):
            print(f"ダミー: Pin {pin_number} にキー設定")
            return True
        
        def set_special_key_binding(self, action, key_obj):
            print(f"ダミー: {action} にキー設定")
            return True
        
        def remove_key_binding(self, pin_number):
            print(f"ダミー: Pin {pin_number} キー削除")
            return True
        
        def remove_special_key_binding(self, action):
            print(f"ダミー: {action} キー削除")
            return True
        
        def setup_default_bindings(self):
            print("ダミー: デフォルト設定復元")
        
        def load_config(self, config_data):
            print("ダミー: 設定読み込み")
        
        def get_status(self):
            return {"monitoring": True, "available": True}
    
    # テスト実行
    try:
        root = tk.Tk()
        root.title("キーボード設定テスト")
        root.geometry("300x200")
        
        dummy_handler = DummyKeyboardHandler()
        
        def open_settings():
            window, panel = create_keyboard_settings_window(root, dummy_handler)
            if window:
                print("設定ウィンドウを開きました")
        
        ttk.Button(root, text="キーボード設定を開く", 
                  command=open_settings).pack(pady=50)
        
        print("テスト用GUIを起動します...")
        root.mainloop()
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()