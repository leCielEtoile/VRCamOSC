# pin_system.py - VRChatカメラPinシステム

import time
from typing import Dict, Optional, Any, Tuple
from pathlib import Path

from camera_data_utils import (
    CameraDataManager, CameraState, Position, Rotation, CameraParams,
    create_clipboard_data, parse_clipboard_data
)


class OSCController:
    """OSC通信制御"""
    
    def __init__(self, target_ip="127.0.0.1", send_port=9000):
        self.target_ip = target_ip
        self.send_port = send_port
        self.client = None
        
        # OSC初期化
        self._initialize_osc()
    
    def _initialize_osc(self):
        """OSC初期化"""
        try:
            from pythonosc.udp_client import SimpleUDPClient
            self.client = SimpleUDPClient(self.target_ip, self.send_port)
            print(f"OSC送信先設定: {self.target_ip}:{self.send_port}")
            return True
        except ImportError:
            print("警告: python-oscライブラリがインストールされていません")
            return False
        except Exception as e:
            print(f"OSC初期化エラー: {e}")
            return False
    
    def send_camera_pose(self, pose_data: list) -> bool:
        """カメラ位置送信"""
        try:
            if not self.client or len(pose_data) < 6:
                return False
            
            # VRChatのOSCエンドポイントに送信
            self.client.send_message("/usercamera/Pose", pose_data)
            return True
            
        except Exception as e:
            print(f"カメラ位置送信エラー: {e}")
            return False
    
    def send_camera_params(self, zoom: float, focal_distance: float, 
                          aperture: float, exposure: float) -> bool:
        """カメラパラメータ送信"""
        try:
            if not self.client:
                return False
            
            # 各パラメータを個別送信
            self.client.send_message("/usercamera/Zoom", zoom)
            self.client.send_message("/usercamera/FocalDistance", focal_distance)
            self.client.send_message("/usercamera/Aperture", aperture)
            self.client.send_message("/usercamera/Exposure", exposure)
            return True
            
        except Exception as e:
            print(f"カメラパラメータ送信エラー: {e}")
            return False
    
    def send_flying_mode(self, enabled: bool) -> bool:
        """飛行モード送信"""
        try:
            if not self.client:
                return False
            
            self.client.send_message("/usercamera/Flying", enabled)
            return True
            
        except Exception as e:
            print(f"飛行モード送信エラー: {e}")
            return False
    
    def send_lookatme(self, enabled: bool) -> bool:
        """LookAtMe送信"""
        try:
            if not self.client:
                return False
            
            self.client.send_message("/usercamera/LookAtMe", enabled)
            return True
            
        except Exception as e:
            print(f"LookAtMe送信エラー: {e}")
            return False


class OSCReceiver:
    """OSC受信処理"""
    
    def __init__(self, port=9001):
        self.port = port
        self.server = None
        self.current_pose = None
        self.current_params = {}
        
        # 受信データ保存
        self.last_update_time = 0
        
        # OSC受信初期化
        self._initialize_receiver()
    
    def _initialize_receiver(self):
        """OSC受信初期化"""
        try:
            from pythonosc import dispatcher
            from pythonosc.osc_server import ThreadingOSCUDPServer
            import threading
            
            # ディスパッチャー作成
            disp = dispatcher.Dispatcher()
            disp.map("/usercamera/Pose", self._handle_pose)
            disp.map("/usercamera/Zoom", self._handle_zoom)
            disp.map("/usercamera/FocalDistance", self._handle_focal_distance)
            disp.map("/usercamera/Aperture", self._handle_aperture)
            disp.map("/usercamera/Exposure", self._handle_exposure)
            disp.map("/usercamera/Flying", self._handle_flying)
            disp.map("/usercamera/LookAtMe", self._handle_lookatme)
            
            # サーバー作成・開始
            self.server = ThreadingOSCUDPServer(("127.0.0.1", self.port), disp)
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
            
            print(f"OSC受信開始: ポート{self.port}")
            return True
            
        except ImportError:
            print("警告: python-oscライブラリがインストールされていません")
            return False
        except Exception as e:
            print(f"OSC受信初期化エラー: {e}")
            return False
    
    def _handle_pose(self, unused_addr, *args):
        """カメラ位置受信処理"""
        try:
            if len(args) >= 6:
                self.current_pose = list(args[:6])
                self.last_update_time = time.time()
        except Exception as e:
            print(f"位置データ処理エラー: {e}")
    
    def _handle_zoom(self, unused_addr, *args):
        """ズーム受信処理"""
        try:
            if args:
                self.current_params['zoom'] = float(args[0])
        except Exception as e:
            print(f"ズームデータ処理エラー: {e}")
    
    def _handle_focal_distance(self, unused_addr, *args):
        """焦点距離距離受信処理"""
        try:
            if args:
                self.current_params['focal_distance'] = float(args[0])
        except Exception as e:
            print(f"焦点距離距離データ処理エラー: {e}")
    
    def _handle_aperture(self, unused_addr, *args):
        """絞り値受信処理"""
        try:
            if args:
                self.current_params['aperture'] = float(args[0])
        except Exception as e:
            print(f"絞り値データ処理エラー: {e}")
    
    def _handle_exposure(self, unused_addr, *args):
        """露出受信処理"""
        try:
            if args:
                self.current_params['exposure'] = float(args[0])
        except Exception as e:
            print(f"露出データ処理エラー: {e}")
    
    def _handle_flying(self, unused_addr, *args):
        """飛行モード受信処理"""
        try:
            if args:
                flying_state = bool(args[0])
                self.current_params['flying'] = flying_state
                # キーボードハンドラーの状態も更新
                if hasattr(self, '_parent_system') and self._parent_system.keyboard_handler:
                    self._parent_system.keyboard_handler.flight_mode_enabled = flying_state
                print(f"飛行モード状態受信: {'ON' if flying_state else 'OFF'}")
        except Exception as e:
            print(f"飛行モードデータ処理エラー: {e}")
    
    def _handle_lookatme(self, unused_addr, *args):
        """LookAtMe受信処理"""
        try:
            if args:
                lookatme_state = bool(args[0])
                self.current_params['lookatme'] = lookatme_state
                # キーボードハンドラーの状態も更新
                if hasattr(self, '_parent_system') and self._parent_system.keyboard_handler:
                    self._parent_system.keyboard_handler.lookatme_enabled = lookatme_state
                print(f"LookAtMe状態受信: {'ON' if lookatme_state else 'OFF'}")
        except Exception as e:
            print(f"LookAtMeデータ処理エラー: {e}")
    
    def set_parent_system(self, parent_system):
        """親システム参照設定（状態同期用）"""
        self._parent_system = parent_system
    
    def get_current_state(self) -> Optional[CameraState]:
        """現在状態取得"""
        try:
            if not self.current_pose or len(self.current_pose) < 6:
                return None
            
            # 位置・回転
            position = Position(self.current_pose[0], self.current_pose[1], self.current_pose[2])
            rotation = Rotation(self.current_pose[3], self.current_pose[4], self.current_pose[5])
            
            # カメラパラメータ (デフォルト値使用)
            camera_params = CameraParams(
                zoom=self.current_params.get('zoom', 45.0),
                focal_distance=self.current_params.get('focal_distance', 1.5),
                aperture=self.current_params.get('aperture', 15.0),
                exposure=self.current_params.get('exposure', 0.0)
            )
            
            return CameraState(position, rotation, camera_params)
            
        except Exception as e:
            print(f"現在状態取得エラー: {e}")
            return None
    
    def get_feature_status(self) -> Dict[str, bool]:
        """機能状態取得（飛行モード、LookAtMe）"""
        return {
            'flying': self.current_params.get('flying', False),
            'lookatme': self.current_params.get('lookatme', False)
        }
    
    def shutdown(self):
        """受信停止"""
        if self.server:
            self.server.shutdown()


class VRChatCameraPinSystem:
    """VRChatカメラPinシステム メインクラス"""
    
    def __init__(self, target_ip="127.0.0.1", send_port=9000, receive_port=9001):
        print("VRChatカメラPinシステムを初期化しています...")
        
        # データマネージャー初期化
        self.data_manager = CameraDataManager()
        
        # OSC制御初期化
        self.osc_controller = OSCController(target_ip, send_port)
        self.osc_receiver = OSCReceiver(receive_port)
        
        # OSCReceiverに親システム参照を設定
        self.osc_receiver.set_parent_system(self)
        
        # キーボードハンドラー (後で初期化)
        self.keyboard_handler = None
        
        print("VRChatカメラPinシステム初期化完了")
    
    def set_keyboard_handler(self, handler):
        """キーボードハンドラー設定"""
        self.keyboard_handler = handler
    
    def save_current_state_to_pin(self, pin_number: int, description: str = "") -> bool:
        """現在状態をPinに保存"""
        try:
            current_state = self.get_current_camera_state()
            if not current_state:
                print(f"現在状態が取得できません - Pin{pin_number}への保存をスキップ")
                return False
            
            success = self.data_manager.save_pin_state(pin_number, current_state, description)
            if success:
                print(f"Pin{pin_number}に現在状態を保存しました")
            return success
            
        except Exception as e:
            print(f"Pin保存エラー: {e}")
            return False
    
    def load_pin_to_camera(self, pin_number: int) -> bool:
        """Pinの状態をカメラに適用"""
        try:
            state = self.data_manager.load_pin_state(pin_number)
            if not state:
                print(f"Pin{pin_number}にデータが保存されていません")
                return False
            
            # OSC送信
            pose_data = state.to_pose_list()
            pose_success = self.osc_controller.send_camera_pose(pose_data)
            
            params_success = self.osc_controller.send_camera_params(
                state.camera_params.zoom,
                state.camera_params.focal_distance,
                state.camera_params.aperture,
                state.camera_params.exposure
            )
            
            if pose_success and params_success:
                print(f"Pin{pin_number}の状態をカメラに適用しました")
                return True
            else:
                print(f"Pin{pin_number}の適用中にOSC送信エラーが発生しました")
                return False
                
        except Exception as e:
            print(f"Pin適用エラー: {e}")
            return False
    
    def delete_pin(self, pin_number: int) -> bool:
        """Pin削除"""
        return self.data_manager.delete_pin_state(pin_number)
    
    def get_current_camera_state(self) -> Optional[CameraState]:
        """現在カメラ状態取得"""
        return self.osc_receiver.get_current_state()
    
    def get_all_pin_states(self) -> Dict[int, CameraState]:
        """全Pin状態取得"""
        return self.data_manager.get_all_pin_states()
    
    def copy_current_state_to_clipboard(self) -> str:
        """現在状態をクリップボード用データとして取得"""
        try:
            current_state = self.get_current_camera_state()
            if not current_state:
                return ""
            
            return create_clipboard_data(current_state)
            
        except Exception as e:
            print(f"現在状態コピーエラー: {e}")
            return ""
    
    def copy_pin_to_clipboard(self, pin_number: int) -> str:
        """Pin状態をクリップボード用データとして取得"""
        try:
            state = self.data_manager.load_pin_state(pin_number)
            if not state:
                return ""
            
            return create_clipboard_data(state, pin_number)
            
        except Exception as e:
            print(f"Pinコピーエラー: {e}")
            return ""
    
    def load_from_clipboard_data(self, clipboard_text: str) -> bool:
        """クリップボードデータから状態を復元してカメラに適用"""
        try:
            state = parse_clipboard_data(clipboard_text)
            if not state:
                return False
            
            # OSC送信
            pose_data = state.to_pose_list()
            pose_success = self.osc_controller.send_camera_pose(pose_data)
            
            params_success = self.osc_controller.send_camera_params(
                state.camera_params.zoom,
                state.camera_params.focal_distance,
                state.camera_params.aperture,
                state.camera_params.exposure
            )
            
            return pose_success and params_success
            
        except Exception as e:
            print(f"クリップボード復元エラー: {e}")
            return False
    
    def start_key_monitoring(self) -> bool:
        """キーボード監視開始"""
        if self.keyboard_handler:
            return self.keyboard_handler.start_monitoring()
        return False
    
    def stop_key_monitoring(self):
        """キーボード監視停止"""
        if self.keyboard_handler:
            self.keyboard_handler.stop_monitoring()
    
    def get_keyboard_status(self) -> Dict[str, Any]:
        """キーボード状態取得"""
        if self.keyboard_handler:
            return self.keyboard_handler.get_status()
        return {"available": False}
    
    def open_keyboard_settings(self, parent_window):
        """キーボード設定ウィンドウを開く"""
        try:
            if self.keyboard_handler:
                from gui_keyboard_setting import create_keyboard_settings_window
                return create_keyboard_settings_window(parent_window, self.keyboard_handler)
            else:
                print("キーボードハンドラーが利用できません")
                return None, None
                
        except ImportError as e:
            print(f"キーボード設定モジュール読み込みエラー: {e}")
            return None, None
        except Exception as e:
            print(f"キーボード設定ウィンドウ作成エラー: {e}")
            return None, None
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "pin_count": len(self.get_all_pin_states()),
            "osc_available": self.osc_controller.client is not None,
            "keyboard_available": self.keyboard_handler is not None,
            "current_state_available": self.get_current_camera_state() is not None
        }
    
    def shutdown(self):
        """システム終了処理"""
        try:
            print("システム終了処理を開始...")
            
            # キーボード監視停止
            self.stop_key_monitoring()
            
            # キーボードハンドラー終了
            if self.keyboard_handler:
                self.keyboard_handler.shutdown()
            
            # OSC受信停止
            if self.osc_receiver:
                self.osc_receiver.shutdown()
            
            print("システム終了処理完了")
            
        except Exception as e:
            print(f"システム終了処理エラー: {e}")


def create_pin_system(target_ip="127.0.0.1", send_port=9000, receive_port=9001):
    """Pinシステム作成ファクトリ関数"""
    try:
        # Pinシステム作成
        pin_system = VRChatCameraPinSystem(target_ip, send_port, receive_port)
        
        # キーボードハンドラー作成・設定
        try:
            from keyboard_handler import create_keyboard_handler
            keyboard_handler = create_keyboard_handler(pin_system)
            pin_system.set_keyboard_handler(keyboard_handler)
            print("キーボードハンドラー初期化完了")
        except ImportError:
            print("警告: キーボードハンドラーの初期化に失敗しました")
        except Exception as e:
            print(f"キーボードハンドラー初期化エラー: {e}")
        
        return pin_system
        
    except Exception as e:
        print(f"Pinシステム作成エラー: {e}")
        raise