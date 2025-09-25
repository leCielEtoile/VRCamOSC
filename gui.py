# gui.py - VRChatCameraOSC統合GUI

import tkinter as tk
from tkinter import ttk, messagebox
import time
import pyperclip
from typing import Optional, Dict, Any

from camera_data_utils import CameraState, get_camera_param_info, create_clipboard_data, parse_clipboard_data


class VRChatCameraPinGUI:
    """VRChatCameraOSC統合GUI"""
    
    def __init__(self, pin_system):
        self.pin_system = pin_system
        
        # メインウィンドウ作成
        self.root = tk.Tk()
        self.root.title("VRChatCameraOSC")
        self.root.geometry("1100x650")
        self.root.minsize(1050, 600)
        
        # ウィンドウを中央に配置
        self._center_window()
        
        # GUI作成
        self._create_widgets()
        
        # 定期更新開始
        self._start_updates()
        
        # 終了処理設定
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        print("VRChatCameraOSC GUI 初期化完了")
    
    def _center_window(self):
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="VRChatCameraOSC", 
                               font=("", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # 左側コンテナ (Pin一覧)
        left_frame = ttk.LabelFrame(main_frame, text="📌 Pin一覧", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # Pin一覧テーブル
        columns = ("Pin", "X座標", "Y座標", "Z座標", "RX回転", "RY回転", "RZ回転", "ズーム", "焦点距離", "絞り値", "露出")
        self.pin_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=12)
        
        # ヘッダー設定
        headers = [
            ("Pin", "📌 Pin"),
            ("X座標", "➡️ X"),
            ("Y座標", "⬆️ Y"),
            ("Z座標", "⬇️ Z"),
            ("RX回転", "🔄 RX"),
            ("RY回転", "🔄 RY"),
            ("RZ回転", "🔄 RZ"),
            ("ズーム", "🔍 ズーム"),
            ("焦点距離", "🎯 焦点距離"),
            ("絞り値", "⚪ 絞り値"),
            ("露出", "💡 露出")
        ]
        
        for col_id, header_text in headers:
            self.pin_tree.heading(col_id, text=header_text)
        
        # カラム幅設定
        column_widths = {
            "Pin": 60, "X座標": 50, "Y座標": 50, "Z座標": 50,
            "RX回転": 50, "RY回転": 50, "RZ回転": 50,
            "ズーム": 50, "焦点距離": 70, "絞り値": 50, "露出": 50
        }
        
        for col_id, width in column_widths.items():
            self.pin_tree.column(col_id, width=width, anchor="center")
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.pin_tree.yview)
        self.pin_tree.configure(yscrollcommand=scrollbar.set)
        
        # ダブルクリックイベント
        self.pin_tree.bind("<Double-1>", self._on_pin_double_click)
        
        # グリッド配置
        self.pin_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 右側コンテナ
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 0))
        right_frame.columnconfigure(0, weight=1)
        
        # 現在状態表示
        self._create_current_state_frame(right_frame)
        
        # Pin操作ボタン
        self._create_pin_operation_frame(right_frame)
        
        # カメラ制御ボタン
        self._create_camera_control_frame(right_frame)
        
        # ステータスバー
        self._create_status_bar(main_frame)
    
    def _create_current_state_frame(self, parent):
        """現在状態表示フレーム作成"""
        current_frame = ttk.LabelFrame(parent, text="📍 現在カメラ状態", padding="10")
        current_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        current_frame.columnconfigure(1, weight=1)
        
        # 位置情報
        ttk.Label(current_frame, text="位置:").grid(row=0, column=0, sticky=tk.W)
        self.position_label = ttk.Label(current_frame, text="未取得", 
                                       font=("Consolas", 9))
        self.position_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(current_frame, text="回転:").grid(row=1, column=0, sticky=tk.W)
        self.rotation_label = ttk.Label(current_frame, text="未取得", 
                                       font=("Consolas", 9))
        self.rotation_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # カメラパラメータ
        ttk.Label(current_frame, text="ズーム:").grid(row=2, column=0, sticky=tk.W)
        self.zoom_label = ttk.Label(current_frame, text="未取得", 
                                   font=("Consolas", 9))
        self.zoom_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(current_frame, text="焦点距離:").grid(row=3, column=0, sticky=tk.W)
        self.focal_label = ttk.Label(current_frame, text="未取得", 
                                    font=("Consolas", 9))
        self.focal_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(current_frame, text="絞り値:").grid(row=4, column=0, sticky=tk.W)
        self.aperture_label = ttk.Label(current_frame, text="未取得", 
                                       font=("Consolas", 9))
        self.aperture_label.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(current_frame, text="露出:").grid(row=5, column=0, sticky=tk.W)
        self.exposure_label = ttk.Label(current_frame, text="未取得", 
                                       font=("Consolas", 9))
        self.exposure_label.grid(row=5, column=1, sticky=tk.W, padx=(10, 0))
        
        # 機能状態表示を追加
        ttk.Label(current_frame, text="飛行:").grid(row=6, column=0, sticky=tk.W)
        self.flight_status_label = ttk.Label(current_frame, text="OFF", 
                                           font=("Consolas", 9), foreground="gray")
        self.flight_status_label.grid(row=6, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(current_frame, text="LookAt:").grid(row=7, column=0, sticky=tk.W)
        self.lookatme_status_label = ttk.Label(current_frame, text="OFF", 
                                             font=("Consolas", 9), foreground="gray")
        self.lookatme_status_label.grid(row=7, column=1, sticky=tk.W, padx=(10, 0))
    
    def _create_pin_operation_frame(self, parent):
        """Pin操作フレーム作成"""
        pin_button_frame = ttk.LabelFrame(parent, text="🎯 Pin操作", padding="10")
        pin_button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        pin_buttons_container = ttk.Frame(pin_button_frame)
        pin_buttons_container.pack(fill=tk.X)
        
        # 1列6行レイアウト
        buttons = [
            ("📍 選択Pinに移動", self._goto_selected_pin),
            ("🗑️ 選択Pin削除", self._delete_selected_pin),
            ("📋 選択Pin→クリップボード", self._copy_selected_pin),
            ("📋 現在状態→クリップボード", self._copy_current_state),
            ("📥 クリップボード→移動", self._move_from_clipboard),
            ("⌨️ キーボード設定", self._open_keyboard_settings)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(pin_buttons_container, text=text, 
                      command=command, width=25).pack(fill=tk.X, pady=3)
    
    def _create_camera_control_frame(self, parent):
        """カメラ制御フレーム作成"""
        camera_frame = ttk.LabelFrame(parent, text="📷 カメラ制御", padding="10")
        camera_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        camera_buttons_container = ttk.Frame(camera_frame)
        camera_buttons_container.pack(fill=tk.X)
        
        # 1行目のボタン
        camera_buttons_row1 = ttk.Frame(camera_buttons_container)
        camera_buttons_row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(camera_buttons_row1, text="✈️ 飛行モード", 
                  command=self._toggle_flight_mode, width=20).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(camera_buttons_row1, text="👁️ LookAtMe", 
                  command=self._toggle_lookatme, width=20).pack(side=tk.LEFT)
    
    def _create_status_bar(self, parent):
        """ステータスバー作成"""
        status_frame = ttk.Frame(parent, relief="sunken", padding="5")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="🟢 システム準備完了")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.keyboard_status_label = ttk.Label(status_frame, text="⌨️ キーボード確認中")
        self.keyboard_status_label.grid(row=0, column=1, sticky=tk.E)
        
        # 時刻表示
        self.time_label = ttk.Label(status_frame, text="", font=("", 8))
        self.time_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
    
    def _start_updates(self):
        """定期更新開始"""
        self._update_display()
        self.root.after(1000, self._start_updates)
    
    def _update_display(self):
        """表示更新"""
        try:
            # Pin一覧更新
            self._update_pin_list()
            
            # 現在状態更新
            self._update_current_state()
            
            # キーボード状態更新
            self._update_keyboard_status()
            
            # カメラ制御状態更新
            self._update_camera_control_status()
            
            # 時刻更新
            self._update_time()
            
        except Exception as e:
            print(f"表示更新エラー: {e}")
    
    def _update_pin_list(self):
        """Pin一覧更新"""
        try:
            # 選択状態を保持
            selected_item = None
            selection = self.pin_tree.selection()
            if selection:
                selected_item = self.pin_tree.item(selection[0])['values'][0]
            
            # 既存の項目をクリア
            for item in self.pin_tree.get_children():
                self.pin_tree.delete(item)
            
            # Pin状態一覧取得
            pin_states = self.pin_system.get_all_pin_states()
            
            # Pin番号順でソート
            for pin_num in sorted(pin_states.keys()):
                state = pin_states[pin_num]
                
                item_id = self.pin_tree.insert("", "end", values=(
                    f"Pin {pin_num}",
                    f"{state.position.x:.2f}",
                    f"{state.position.y:.2f}",
                    f"{state.position.z:.2f}",
                    f"{state.rotation.rx:.1f}°",
                    f"{state.rotation.ry:.1f}°",
                    f"{state.rotation.rz:.1f}°",
                    f"{state.camera_params.zoom:.0f}°",
                    f"{state.camera_params.focal_distance:.1f}m",
                    f"f{state.camera_params.aperture:.1f}",
                    f"{state.camera_params.exposure:+.1f}EV"
                ))
                
                # 選択状態を復元
                if selected_item and selected_item == f"Pin {pin_num}":
                    self.pin_tree.selection_set(item_id)
                    self.pin_tree.focus(item_id)
                
        except Exception as e:
            print(f"Pin一覧更新エラー: {e}")
    
    def _update_current_state(self):
        """現在状態更新"""
        try:
            current_state = self.pin_system.get_current_camera_state()
            if current_state:
                pos = current_state.position
                rot = current_state.rotation
                cam = current_state.camera_params
                
                self.position_label.config(
                    text=f"X:{pos.x:8.3f}  Y:{pos.y:8.3f}  Z:{pos.z:8.3f}"
                )
                self.rotation_label.config(
                    text=f"RX:{rot.rx:6.1f}°  RY:{rot.ry:6.1f}°  RZ:{rot.rz:6.1f}°"
                )
                self.zoom_label.config(text=f"{cam.zoom:.1f}° (視野角)")
                self.focal_label.config(text=f"{cam.focal_distance:.2f}m")
                self.aperture_label.config(text=f"f{cam.aperture:.1f}")
                self.exposure_label.config(text=f"{cam.exposure:+.1f}EV")
            else:
                self.position_label.config(text="座標未取得 - カメラを動かしてください")
                self.rotation_label.config(text="回転未取得")
                self.zoom_label.config(text="ズーム未取得")
                self.focal_label.config(text="焦点距離未取得")
                self.aperture_label.config(text="絞り値未取得")
                self.exposure_label.config(text="露出未取得")
                
        except Exception as e:
            print(f"現在状態更新エラー: {e}")
    
    def _update_keyboard_status(self):
        """キーボード状態更新"""
        try:
            status = self.pin_system.get_keyboard_status()
            if status.get("available", False):
                if status.get("monitoring", False):
                    key_count = status.get("configured_keys", 0)
                    special_count = status.get("special_keys", 0)
                    self.keyboard_status_label.config(
                        text=f"⌨️ 監視中 ({key_count}+{special_count}キー)"
                    )
                else:
                    self.keyboard_status_label.config(text="⌨️ 停止中")
            else:
                self.keyboard_status_label.config(text="⌨️ 無効")
                
        except Exception as e:
            print(f"キーボード状態更新エラー: {e}")
    
    def _update_camera_control_status(self):
        """カメラ制御状態更新"""
        try:
            if hasattr(self.pin_system, 'keyboard_handler') and self.pin_system.keyboard_handler:
                feature_status = self.pin_system.keyboard_handler.get_feature_status()
                
                # 飛行モード状態
                if feature_status.get('flight_mode', False):
                    self.flight_status_label.config(text="ON", foreground="blue")
                else:
                    self.flight_status_label.config(text="OFF", foreground="gray")
                
                # LookAtMe状態
                if feature_status.get('lookatme', False):
                    self.lookatme_status_label.config(text="ON", foreground="green")
                else:
                    self.lookatme_status_label.config(text="OFF", foreground="gray")
            
        except Exception as e:
            print(f"カメラ制御状態更新エラー: {e}")
    
    def _update_time(self):
        """時刻更新"""
        try:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.config(text=f"⏰ {current_time}")
        except Exception as e:
            print(f"時刻更新エラー: {e}")
    
    def _update_status(self, message: str):
        """ステータス更新"""
        try:
            self.status_label.config(text=message)
            self.root.after(3000, lambda: self.status_label.config(text="🟢 システム準備完了"))
        except Exception as e:
            print(f"ステータス更新エラー: {e}")
    
    def _get_selected_pin_number(self) -> Optional[int]:
        """選択されたPin番号を取得"""
        try:
            selection = self.pin_tree.selection()
            if selection:
                item = self.pin_tree.item(selection[0])
                pin_text = item['values'][0]
                return int(pin_text.split()[1])
            return None
        except Exception:
            return None
    
    def _on_pin_double_click(self, event):
        """Pin一覧ダブルクリック処理"""
        try:
            pin_number = self._get_selected_pin_number()
            if pin_number:
                self._goto_pin(pin_number)
        except Exception as e:
            print(f"ダブルクリック処理エラー: {e}")
    
    def _goto_selected_pin(self):
        """選択されたPinに移動"""
        try:
            pin_number = self._get_selected_pin_number()
            if pin_number is None:
                messagebox.showwarning("選択エラー", "移動するPinを選択してください")
                return
            
            self._goto_pin(pin_number)
                
        except Exception as e:
            messagebox.showerror("エラー", f"Pin移動エラー: {e}")
    
    def _goto_pin(self, pin_number: int):
        """指定されたPinに移動"""
        try:
            success = self.pin_system.load_pin_to_camera(pin_number)
            if success:
                self._update_status(f"🎯 Pin {pin_number} に移動しました")
            else:
                messagebox.showerror("エラー", f"Pin {pin_number} への移動に失敗しました")
        except Exception as e:
            messagebox.showerror("エラー", f"Pin移動エラー: {e}")
    
    def _delete_selected_pin(self):
        """選択されたPinを削除"""
        try:
            pin_number = self._get_selected_pin_number()
            if pin_number is None:
                messagebox.showwarning("選択エラー", "削除するPinを選択してください")
                return
            
            result = messagebox.askyesno("削除確認", 
                                       f"Pin {pin_number} を削除しますか？\n\n"
                                       f"この操作は取り消せません。")
            if not result:
                return
            
            success = self.pin_system.delete_pin(pin_number)
            if success:
                self._update_status(f"🗑️ Pin {pin_number} を削除しました")
                messagebox.showinfo("削除完了", f"Pin {pin_number} を削除しました")
            else:
                messagebox.showerror("エラー", f"Pin {pin_number} の削除に失敗しました")
                
        except Exception as e:
            messagebox.showerror("エラー", f"Pin削除エラー: {e}")
    
    def _copy_selected_pin(self):
        """選択されたPinをクリップボードに保存"""
        try:
            pin_number = self._get_selected_pin_number()
            if pin_number is None:
                messagebox.showwarning("選択エラー", "コピーするPinを選択してください")
                return
            
            clipboard_text = self.pin_system.copy_pin_to_clipboard(pin_number)
            if clipboard_text:
                pyperclip.copy(clipboard_text)
                self._update_status(f"📋 Pin {pin_number} をクリップボードに保存しました")
                messagebox.showinfo("コピー完了", f"Pin {pin_number} の状態をクリップボードに保存しました")
            else:
                messagebox.showerror("エラー", f"Pin {pin_number} が見つかりません")
                
        except Exception as e:
            messagebox.showerror("エラー", f"Pinコピーエラー: {e}")
    
    def _copy_current_state(self):
        """現在状態をクリップボードに保存"""
        try:
            clipboard_text = self.pin_system.copy_current_state_to_clipboard()
            if clipboard_text:
                pyperclip.copy(clipboard_text)
                self._update_status("📋 現在状態をクリップボードに保存しました")
                messagebox.showinfo("コピー完了", "現在カメラ状態をクリップボードに保存しました")
            else:
                messagebox.showerror("エラー", "現在状態が取得できません。\n\n"
                                   "解決方法:\n"
                                   "1. VRChatでカメラを開いてください\n"
                                   "2. カメラを少し動かしてください")
                
        except Exception as e:
            messagebox.showerror("エラー", f"状態コピーエラー: {e}")
    
    def _move_from_clipboard(self):
        """クリップボードの状態に移動"""
        try:
            clipboard_text = pyperclip.paste()
            
            success = self.pin_system.load_from_clipboard_data(clipboard_text)
            if success:
                self._update_status("📥 クリップボードの状態に移動しました")
                messagebox.showinfo("移動完了", "クリップボードの状態に移動しました")
            else:
                messagebox.showwarning("クリップボード空", 
                                     "クリップボードに有効なカメラ状態が保存されていません。\n\n"
                                     "まず以下のいずれかを実行してください:\n"
                                     "• 選択Pin→クリップボード\n"
                                     "• 現在状態→クリップボード\n"
                                     "• テンキー . キー (現在状態保存)")
                
        except Exception as e:
            messagebox.showerror("エラー", f"クリップボード移動エラー: {e}")
    
    def _open_keyboard_settings(self):
        """キーボード設定画面を開く"""
        try:
            window, panel = self.pin_system.open_keyboard_settings(self.root)
            if window:
                self._update_status("⌨️ キーボード設定画面を開きました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"キーボード設定画面の表示に失敗しました:\n{e}")
    
    def _toggle_flight_mode(self):
        """飛行モード切り替え"""
        try:
            if hasattr(self.pin_system, 'keyboard_handler') and self.pin_system.keyboard_handler:
                self.pin_system.keyboard_handler._toggle_flight_mode()
                self._update_status("✈️ 飛行モードを切り替えました")
            else:
                messagebox.showerror("エラー", "キーボードハンドラーが利用できません")
                
        except Exception as e:
            messagebox.showerror("エラー", f"飛行モード切り替えエラー: {e}")
    
    def _toggle_lookatme(self):
        """LookAtMe切り替え"""
        try:
            if hasattr(self.pin_system, 'keyboard_handler') and self.pin_system.keyboard_handler:
                self.pin_system.keyboard_handler._toggle_lookatme()
                self._update_status("👁️ LookAtMeを切り替えました")
            else:
                messagebox.showerror("エラー", "キーボードハンドラーが利用できません")
                
        except Exception as e:
            messagebox.showerror("エラー", f"LookAtMe切り替えエラー: {e}")
    
    def _on_closing(self):
        """アプリケーション終了処理"""
        try:
            pin_states = self.pin_system.get_all_pin_states()
            pin_count = len(pin_states)
            
            result = messagebox.askyesno("終了確認","VRChatCameraOSCを終了しますか？")
            
            if result:
                print("アプリケーション終了処理を開始")
                
                # システム終了
                self.pin_system.shutdown()
                
                print("正常終了しました")
                
                # ウィンドウ破棄
                self.root.destroy()
                
        except Exception as e:
            print(f"終了処理エラー: {e}")
            # エラーが発生しても強制終了
            self.root.destroy()
    
    def run(self):
        """GUI実行"""
        try:
            print("VRChatCameraOSC GUIを開始します...")
            
            # キーボード監視自動開始
            if self.pin_system.start_key_monitoring():
                print("キーボード監視を開始しました")
                self._update_status("🟢 システム準備完了 - キーボード監視中")
            else:
                print("キーボード監視の開始に失敗しました")
                self._update_status("🟡 システム準備完了 - キーボード無効")
            
            # ウィンドウ表示
            self.root.deiconify()
            
            # 焦点距離設定
            self.root.focus_force()
            
            print("GUIを表示しました")
            
            # メインループ開始
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("強制終了されました")
        except Exception as e:
            print(f"GUI実行エラー: {e}")
            messagebox.showerror("システムエラー", f"GUI実行エラー: {e}")
        finally:
            print("GUI終了")