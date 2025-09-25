# camera_data_utils.py - VRChatカメラデータ共通処理

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Position:
    """カメラ位置"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Rotation:
    """カメラ回転"""
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0


@dataclass
class CameraParams:
    """カメラパラメータ"""
    zoom: float = 45.0
    focal_distance: float = 1.5
    aperture: float = 15.0
    exposure: float = 0.0


@dataclass
class CameraState:
    """カメラ状態"""
    position: Position
    rotation: Rotation
    camera_params: CameraParams
    
    def to_pose_list(self) -> list:
        """OSC用座標リストに変換"""
        return [
            self.position.x, self.position.y, self.position.z,
            self.rotation.rx, self.rotation.ry, self.rotation.rz
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "position": asdict(self.position),
            "rotation": asdict(self.rotation),
            "camera_params": asdict(self.camera_params)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraState':
        """辞書から作成"""
        position = Position(**data.get("position", {}))
        rotation = Rotation(**data.get("rotation", {}))
        camera_params = CameraParams(**data.get("camera_params", {}))
        return cls(position, rotation, camera_params)
    
    @classmethod
    def from_pose_data(cls, pose: Tuple[float, ...], zoom: float = 45.0, 
                      focal_distance: float = 1.5, aperture: float = 15.0, 
                      exposure: float = 0.0) -> 'CameraState':
        """OSC座標データから作成"""
        if len(pose) < 6:
            raise ValueError("座標データが不足しています")
        
        position = Position(pose[0], pose[1], pose[2])
        rotation = Rotation(pose[3], pose[4], pose[5])
        camera_params = CameraParams(zoom, focal_distance, aperture, exposure)
        
        return cls(position, rotation, camera_params)


class CameraParamsValidator:
    """カメラパラメータ検証"""
    
    ZOOM_RANGE = (20.0, 150.0)
    FOCAL_DISTANCE_RANGE = (0.0, 10.0)
    APERTURE_RANGE = (1.4, 32.0)
    EXPOSURE_RANGE = (-10.0, 4.0)
    
    @classmethod
    def validate_zoom(cls, zoom: float) -> float:
        """ズーム値検証"""
        return max(cls.ZOOM_RANGE[0], min(cls.ZOOM_RANGE[1], zoom))
    
    @classmethod
    def validate_focal_distance(cls, focal_distance: float) -> float:
        """焦点距離距離検証"""
        return max(cls.FOCAL_DISTANCE_RANGE[0], min(cls.FOCAL_DISTANCE_RANGE[1], focal_distance))
    
    @classmethod
    def validate_aperture(cls, aperture: float) -> float:
        """絞り値検証"""
        return max(cls.APERTURE_RANGE[0], min(cls.APERTURE_RANGE[1], aperture))
    
    @classmethod
    def validate_exposure(cls, exposure: float) -> float:
        """露出値検証"""
        return max(cls.EXPOSURE_RANGE[0], min(cls.EXPOSURE_RANGE[1], exposure))
    
    @classmethod
    def validate_camera_params(cls, params: CameraParams) -> CameraParams:
        """カメラパラメータ全体検証"""
        return CameraParams(
            zoom=cls.validate_zoom(params.zoom),
            focal_distance=cls.validate_focal_distance(params.focal_distance),
            aperture=cls.validate_aperture(params.aperture),
            exposure=cls.validate_exposure(params.exposure)
        )


class CameraDataManager:
    """カメラデータ管理"""
    
    def __init__(self, data_file: str = "camera_pins.json"):
        self.data_file = Path(data_file)
        self.pin_states: Dict[int, CameraState] = {}
        self.descriptions: Dict[int, str] = {}
        self.load_data()
    
    def save_pin_state(self, pin_number: int, state: CameraState, description: str = "") -> bool:
        """Pin状態保存"""
        try:
            if not (1 <= pin_number <= 9):
                return False
            
            # パラメータ検証
            validated_params = CameraParamsValidator.validate_camera_params(state.camera_params)
            validated_state = CameraState(state.position, state.rotation, validated_params)
            
            self.pin_states[pin_number] = validated_state
            if description.strip():
                self.descriptions[pin_number] = description.strip()
            
            self.save_data()
            return True
            
        except Exception as e:
            print(f"Pin状態保存エラー: {e}")
            return False
    
    def load_pin_state(self, pin_number: int) -> Optional[CameraState]:
        """Pin状態取得"""
        return self.pin_states.get(pin_number)
    
    def delete_pin_state(self, pin_number: int) -> bool:
        """Pin状態削除"""
        try:
            if pin_number in self.pin_states:
                del self.pin_states[pin_number]
                self.descriptions.pop(pin_number, None)
                self.save_data()
                return True
            return False
            
        except Exception as e:
            print(f"Pin状態削除エラー: {e}")
            return False
    
    def get_all_pin_states(self) -> Dict[int, CameraState]:
        """全Pin状態取得"""
        return self.pin_states.copy()
    
    def set_description(self, pin_number: int, description: str):
        """Pin説明設定"""
        if 1 <= pin_number <= 9:
            if description.strip():
                self.descriptions[pin_number] = description.strip()
            else:
                self.descriptions.pop(pin_number, None)
            self.save_data()
    
    def get_description(self, pin_number: int) -> str:
        """Pin説明取得"""
        return self.descriptions.get(pin_number, "")
    
    def save_data(self):
        """データファイル保存"""
        try:
            data = {
                "saved_poses": {
                    str(k): v.to_dict() for k, v in self.pin_states.items()
                },
                "descriptions": {
                    str(k): v for k, v in self.descriptions.items()
                }
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"データ保存エラー: {e}")
    
    def load_data(self):
        """データファイル読み込み"""
        try:
            if not self.data_file.exists():
                return
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Pin状態読み込み
            saved_poses = data.get("saved_poses", {})
            for pin_str, state_data in saved_poses.items():
                try:
                    pin_num = int(pin_str)
                    if 1 <= pin_num <= 9:
                        state = CameraState.from_dict(state_data)
                        # パラメータ検証
                        state.camera_params = CameraParamsValidator.validate_camera_params(state.camera_params)
                        self.pin_states[pin_num] = state
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Pin {pin_str} データ読み込みエラー: {e}")
                    continue
            
            # 説明読み込み
            descriptions = data.get("descriptions", {})
            for pin_str, desc in descriptions.items():
                try:
                    pin_num = int(pin_str)
                    if 1 <= pin_num <= 9:
                        self.descriptions[pin_num] = str(desc)
                except (ValueError, TypeError):
                    continue
                    
        except Exception as e:
            print(f"データ読み込みエラー: {e}")


def create_clipboard_data(state: CameraState, pin_number: Optional[int] = None) -> str:
    """クリップボード用データ作成"""
    try:
        clipboard_data = {
            "type": "vrchat_camera_state",
            "position": asdict(state.position),
            "rotation": asdict(state.rotation),
            "camera_params": asdict(state.camera_params),
        }
        
        if pin_number is not None:
            clipboard_data["pin_number"] = pin_number
        
        return json.dumps(clipboard_data, indent=2)
        
    except Exception as e:
        print(f"クリップボードデータ作成エラー: {e}")
        return ""


def parse_clipboard_data(clipboard_text: str) -> Optional[CameraState]:
    """クリップボードデータ解析"""
    try:
        data = json.loads(clipboard_text)
        
        if (isinstance(data, dict) and
            data.get("type") == "vrchat_camera_state" and
            "position" in data and "rotation" in data and "camera_params" in data):
            return CameraState.from_dict(data)
        
        return None
        
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"クリップボードデータ解析エラー: {e}")
        return None


def get_camera_param_info() -> Dict[str, Dict[str, Any]]:
    """カメラパラメータ情報取得"""
    return {
        "zoom": {
            "name": "ズーム",
            "unit": "度",
            "range": CameraParamsValidator.ZOOM_RANGE,
            "default": 45.0,
            "description": "視野角。小さいほど望遠、大きいほど広角"
        },
        "focal_distance": {
            "name": "焦点距離",
            "unit": "m",
            "range": CameraParamsValidator.FOCAL_DISTANCE_RANGE,
            "default": 1.5,
            "description": "ピントを合わせる距離。手前から奥への深度"
        },
        "aperture": {
            "name": "絞り値",
            "unit": "f値",
            "range": CameraParamsValidator.APERTURE_RANGE,
            "default": 15.0,
            "description": "絞り値。小さいほどボケが大きく、大きいほど全体にピント"
        },
        "exposure": {
            "name": "露出",
            "unit": "EV",
            "range": CameraParamsValidator.EXPOSURE_RANGE,
            "default": 0.0,
            "description": "明るさ調整。マイナスで暗く、プラスで明るく"
        }
    }