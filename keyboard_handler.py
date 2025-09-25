# keyboard_handler.py - キーボード入力処理モジュール v1.0

import time
import json
import pyperclip
from pathlib import Path
from typing import Dict, Optional, Any
from pynput import keyboard

from camera_data_utils import create_clipboard_data, parse_clipboard_data


class KeyboardHandler:
    """キーボード入力処理"""
    
    def __init__(self, pin_system):
        self.pin_system = pin_system
        self.pressed_keys = set()
        self.key_press_times = {}
        self.long_press_threshold = 0.8
        self.is_monitoring = False
        self.listener = None
        
        # 設定ファイル
        self.config_file = Path("keyboard_config.json")
        
        # Pin操作キーバインド (Pin番号 -> VKコード)
        self.key_bindings: Dict[int, int] = {}
        
        # 逆マッピング (VKコード -> Pin番号)
        self.vk_to_pin: Dict[int, int] = {}
        
        # 特殊機能キーバインド
        self.special_key_bindings: Dict[str, int] = {}
        self.vk_to_special: Dict[int, str] = {}
        
        # 機能状態管理
        self.flight_mode_enabled = False
        self.lookatme_enabled = False
        
        # 設定読み込み
        self.load_config()
    
    def load_config(self, config_data: Optional[Dict] = None):
        """設定読み込み"""
        if config_data is None:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                except Exception:
                    self.setup_default_bindings()
                    return
            else:
                self.setup_default_bindings()
                return
        
        # 長押し閾値設定
        if "long_press_threshold" in config_data:
            self.long_press_threshold = float(config_data["long_press_threshold"])
        
        # Pin操作キーバインド設定
        if "key_bindings_vk" in config_data:
            key_bindings = config_data["key_bindings_vk"]
            self.key_bindings = {}
            self.vk_to_pin = {}
            
            for pin_str, vk_code in key_bindings.items():
                try:
                    pin_num = int(pin_str)
                    vk = int(vk_code)
                    if 1 <= pin_num <= 9:
                        self.key_bindings[pin_num] = vk
                        self.vk_to_pin[vk] = pin_num
                except (ValueError, TypeError):
                    continue
        
        # 特殊機能キーバインド設定
        if "special_key_bindings_vk" in config_data:
            special_bindings = config_data["special_key_bindings_vk"]
            self.special_key_bindings = {}
            self.vk_to_special = {}
            
            for action, vk_code in special_bindings.items():
                try:
                    vk = int(vk_code)
                    self.special_key_bindings[action] = vk
                    self.vk_to_special[vk] = action
                except (ValueError, TypeError):
                    continue
        
        # 状態復元
        if "flight_mode_enabled" in config_data:
            self.flight_mode_enabled = bool(config_data["flight_mode_enabled"])
        if "lookatme_enabled" in config_data:
            self.lookatme_enabled = bool(config_data["lookatme_enabled"])
        
        # デフォルト設定がない場合は設定
        if not self.key_bindings or not self.special_key_bindings:
            self.setup_default_bindings()
    
    def save_config(self):
        """設定保存"""
        config_data = {
            "key_bindings_vk": {str(pin): vk for pin, vk in self.key_bindings.items()},
            "special_key_bindings_vk": {action: vk for action, vk in self.special_key_bindings.items()},
            "long_press_threshold": self.long_press_threshold,
            "flight_mode_enabled": self.flight_mode_enabled,
            "lookatme_enabled": self.lookatme_enabled,
            "version": "1.0"
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定保存エラー: {e}")
    
    def setup_default_bindings(self):
        """デフォルトキーバインド設定"""
        # Pin操作キー (テンキー1-9のVKコード)
        self.key_bindings = {}
        self.vk_to_pin = {}
        
        for pin in range(1, 10):
            vk_code = 96 + pin  # numpad 1-9のVKコード
            self.key_bindings[pin] = vk_code
            self.vk_to_pin[vk_code] = pin
        
        # 特殊機能キー (テンキーのVKコード)
        self.special_key_bindings = {
            "copy_current": 110,    # . (小数点)
            "move_clipboard": 96,   # Numpad 0
            "toggle_flight": 111,   # / (除算)
            "toggle_lookatme": 106  # * (乗算)
        }
        
        # 逆マッピング作成
        self.vk_to_special = {}
        for action, vk in self.special_key_bindings.items():
            self.vk_to_special[vk] = action
        
        # 設定保存
        self.save_config()
    
    def _get_vk_code(self, key_obj) -> Optional[int]:
        """キーオブジェクトからVKコード取得"""
        if hasattr(key_obj, 'vk') and key_obj.vk is not None:
            return key_obj.vk
        return None
    
    def _get_display_name(self, vk_code: int) -> str:
        """VKコードから表示名取得"""
        try:
            # ファンクションキー
            if 112 <= vk_code <= 123:
                return f"F{vk_code - 111}"
            
            # テンキー
            if 97 <= vk_code <= 105:
                return f"Numpad {vk_code - 96}"
            elif vk_code == 96:
                return "Numpad 0"
            
            # テンキー演算子
            elif vk_code == 106:
                return "Multiply"      # * (乗算)
            elif vk_code == 107:
                return "Add"           # + (加算)
            elif vk_code == 109:
                return "Subtract"      # - (減算)
            elif vk_code == 110:
                return "Decimal"       # . (小数点)
            elif vk_code == 111:
                return "Divide"        # / (除算)
            
            # 特殊キー
            for key_attr in dir(keyboard.Key):
                if not key_attr.startswith('_'):
                    try:
                        key_value = getattr(keyboard.Key, key_attr)
                        if hasattr(key_value, 'value') and key_value.value == vk_code:
                            return key_attr.replace('_', ' ').title()
                    except:
                        continue
            
            # 文字キー
            try:
                key_obj = keyboard.KeyCode.from_vk(vk_code)
                if hasattr(key_obj, 'char') and key_obj.char:
                    return key_obj.char.upper()
            except:
                pass
            
            return f"VK_{vk_code}"
            
        except Exception:
            return f"VK_{vk_code}"
    
    def set_key_binding(self, pin_number: int, key_obj) -> bool:
        """Pin操作キーバインド設定"""
        if not (1 <= pin_number <= 9):
            return False
        
        vk_code = self._get_vk_code(key_obj)
        if vk_code is None:
            return False
        
        # 特殊機能キーとの競合チェック
        if vk_code in self.vk_to_special:
            print(f"警告: VKコード {vk_code} は特殊機能キーと競合します")
            return False
        
        # 既存のバインドから削除
        if pin_number in self.key_bindings:
            old_vk = self.key_bindings[pin_number]
            if old_vk in self.vk_to_pin:
                del self.vk_to_pin[old_vk]
        
        # 新しいバインド設定
        self.key_bindings[pin_number] = vk_code
        self.vk_to_pin[vk_code] = pin_number
        
        # 設定保存
        self.save_config()
        
        return True
    
    def set_special_key_binding(self, action: str, key_obj) -> bool:
        """特殊機能キーバインド設定"""
        valid_actions = ["copy_current", "move_clipboard", "toggle_flight", "toggle_lookatme"]
        if action not in valid_actions:
            return False
        
        vk_code = self._get_vk_code(key_obj)
        if vk_code is None:
            return False
        
        # Pin操作キーとの競合チェック
        if vk_code in self.vk_to_pin:
            print(f"警告: VKコード {vk_code} はPin操作キーと競合します")
            return False
        
        # 既存のバインドから削除
        if action in self.special_key_bindings:
            old_vk = self.special_key_bindings[action]
            if old_vk in self.vk_to_special:
                del self.vk_to_special[old_vk]
        
        # 新しいバインド設定
        self.special_key_bindings[action] = vk_code
        self.vk_to_special[vk_code] = action
        
        # 設定保存
        self.save_config()
        
        return True
    
    def remove_key_binding(self, pin_number: int) -> bool:
        """Pin操作キーバインド削除"""
        if pin_number in self.key_bindings:
            vk_code = self.key_bindings[pin_number]
            if vk_code in self.vk_to_pin:
                del self.vk_to_pin[vk_code]
            
            del self.key_bindings[pin_number]
            
            self.save_config()
            return True
        
        return False
    
    def remove_special_key_binding(self, action: str) -> bool:
        """特殊機能キーバインド削除"""
        if action in self.special_key_bindings:
            vk_code = self.special_key_bindings[action]
            if vk_code in self.vk_to_special:
                del self.vk_to_special[vk_code]
            
            del self.special_key_bindings[action]
            
            self.save_config()
            return True
        
        return False
    
    def get_key_bindings(self) -> Dict[int, str]:
        """Pin操作キーバインド取得 (表示名付き)"""
        return {pin: self._get_display_name(vk) for pin, vk in self.key_bindings.items()}
    
    def get_special_key_bindings(self) -> Dict[str, str]:
        """特殊機能キーバインド取得 (表示名付き)"""
        return {action: self._get_display_name(vk) for action, vk in self.special_key_bindings.items()}
    
    def start_monitoring(self) -> bool:
        """キー監視開始"""
        if self.is_monitoring:
            return True
        
        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            self.is_monitoring = True
            print("キーボード監視開始")
            return True
        except Exception as e:
            print(f"キーボード監視開始エラー: {e}")
            return False
    
    def stop_monitoring(self):
        """キー監視停止"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self.is_monitoring = False
        self.pressed_keys.clear()
        self.key_press_times.clear()
        print("キーボード監視停止")
    
    def _on_press(self, key):
        """キー押下ハンドラー"""
        try:
            vk_code = self._get_vk_code(key)
            if vk_code is not None:
                self._handle_key_press(vk_code)
        except Exception as e:
            print(f"キー押下処理エラー: {e}")
    
    def _on_release(self, key):
        """キー離上ハンドラー"""
        try:
            vk_code = self._get_vk_code(key)
            if vk_code is not None:
                self._handle_key_release(vk_code)
        except Exception as e:
            print(f"キー離上処理エラー: {e}")
    
    def _handle_key_press(self, vk_code: int):
        """キー押下処理"""
        if vk_code not in self.pressed_keys:
            self.pressed_keys.add(vk_code)
            self.key_press_times[vk_code] = time.time()
    
    def _handle_key_release(self, vk_code: int):
        """キー離上処理"""
        if vk_code in self.pressed_keys:
            self.pressed_keys.remove(vk_code)
            
            if vk_code in self.key_press_times:
                press_duration = time.time() - self.key_press_times[vk_code]
                del self.key_press_times[vk_code]
                
                # Pin操作キーの処理
                if vk_code in self.vk_to_pin:
                    pin_number = self.vk_to_pin[vk_code]
                    
                    if press_duration >= self.long_press_threshold:
                        # 長押し: Pin保存
                        self._save_pin(pin_number)
                    else:
                        # 短押し: Pin移動
                        self._move_to_pin(pin_number)
                
                # 特殊機能キーの処理
                elif vk_code in self.vk_to_special:
                    action = self.vk_to_special[vk_code]
                    self._handle_special_action(action)
    
    def _handle_special_action(self, action: str):
        """特殊機能アクション処理"""
        try:
            if action == "copy_current":
                self._copy_current_state()
            elif action == "move_clipboard":
                self._move_from_clipboard()
            elif action == "toggle_flight":
                self._toggle_flight_mode()
            elif action == "toggle_lookatme":
                self._toggle_lookatme()
            else:
                print(f"未知のアクション: {action}")
                
        except Exception as e:
            print(f"特殊機能実行エラー [{action}]: {e}")
    
    def _save_pin(self, pin_number: int):
        """Pin保存"""
        try:
            success = self.pin_system.save_current_state_to_pin(pin_number)
            if success:
                print(f"Pin {pin_number} に現在状態を保存しました")
            else:
                print(f"Pin {pin_number} への保存に失敗しました")
        except Exception as e:
            print(f"Pin保存エラー: {e}")
    
    def _move_to_pin(self, pin_number: int):
        """Pin移動"""
        try:
            success = self.pin_system.load_pin_to_camera(pin_number)
            if success:
                print(f"Pin {pin_number} に移動しました")
            else:
                print(f"Pin {pin_number} への移動に失敗しました")
        except Exception as e:
            print(f"Pin移動エラー: {e}")
    
    def _copy_current_state(self):
        """現在状態をクリップボードに保存"""
        try:
            clipboard_text = self.pin_system.copy_current_state_to_clipboard()
            if clipboard_text:
                pyperclip.copy(clipboard_text)
                print(f"📋 現在カメラ状態をクリップボードに保存しました")
            else:
                print("❌ 現在状態が取得できません - VRChatでカメラを動かしてください")
                
        except Exception as e:
            print(f"現在状態コピーエラー: {e}")
    
    def _move_from_clipboard(self):
        """クリップボードの状態に移動"""
        try:
            clipboard_text = pyperclip.paste()
            
            success = self.pin_system.load_from_clipboard_data(clipboard_text)
            if success:
                print(f"📥 クリップボードの状態に移動しました")
            else:
                print("❌ クリップボードに有効な状態情報がありません")
                
        except Exception as e:
            print(f"クリップボード移動エラー: {e}")
    
    def _toggle_flight_mode(self):
        """飛行モード切り替え"""
        try:
            # 状態を切り替え
            self.flight_mode_enabled = not self.flight_mode_enabled
            
            # OSC送信
            if hasattr(self.pin_system, 'osc_controller') and self.pin_system.osc_controller.client:
                self.pin_system.osc_controller.send_flying_mode(self.flight_mode_enabled)
                
                status = "ON" if self.flight_mode_enabled else "OFF"
                print(f"✈️ 飛行モード: {status}")
                
                # 設定保存
                self.save_config()
            else:
                print("❌ OSC通信が利用できません")
                # 状態を元に戻す
                self.flight_mode_enabled = not self.flight_mode_enabled
                
        except Exception as e:
            print(f"飛行モード切り替えエラー: {e}")
            # エラー時は状態を元に戻す
            self.flight_mode_enabled = not self.flight_mode_enabled
    
    def _toggle_lookatme(self):
        """LookAtMe切り替え"""
        try:
            # 状態を切り替え
            self.lookatme_enabled = not self.lookatme_enabled
            
            # OSC送信
            if hasattr(self.pin_system, 'osc_controller') and self.pin_system.osc_controller.client:
                self.pin_system.osc_controller.send_lookatme(self.lookatme_enabled)
                
                status = "ON" if self.lookatme_enabled else "OFF"
                print(f"👁️ LookAtMe: {status}")
                
                # 設定保存
                self.save_config()
            else:
                print("❌ OSC通信が利用できません")
                # 状態を元に戻す
                self.lookatme_enabled = not self.lookatme_enabled
                
        except Exception as e:
            print(f"LookAtMe切り替えエラー: {e}")
            # エラー時は状態を元に戻す
            self.lookatme_enabled = not self.lookatme_enabled
    
    def get_status(self) -> Dict[str, Any]:
        """ハンドラー状態取得"""
        return {
            'available': True,
            'monitoring': self.is_monitoring,
            'library': 'pynput',
            'status': 'running' if self.is_monitoring else 'stopped',
            'pressed_keys': list(self.pressed_keys),
            'long_press_threshold': self.long_press_threshold,
            'configured_keys': len(self.key_bindings),
            'special_keys': len(self.special_key_bindings),
            'key_bindings': self.get_key_bindings(),
            'special_key_bindings': self.get_special_key_bindings(),
            'flight_mode_enabled': self.flight_mode_enabled,
            'lookatme_enabled': self.lookatme_enabled
        }
    
    def get_feature_status(self) -> Dict[str, bool]:
        """機能の状態取得"""
        return {
            'flight_mode': self.flight_mode_enabled,
            'lookatme': self.lookatme_enabled
        }
    
    def shutdown(self):
        """終了処理"""
        self.stop_monitoring()
        self.save_config()


def create_keyboard_handler(pin_system):
    """キーボードハンドラー作成"""
    return KeyboardHandler(pin_system)