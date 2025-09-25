# main.py - VRChatカメラPinシステム メインエントリーポイント

import sys
from pathlib import Path
from tkinter import messagebox

def main():
    """メイン関数"""
    print("VRChat Camera OSC")
    print("=" * 40)
    
    try:
        # Pinシステム作成
        from pin_system import create_pin_system
        pin_system = create_pin_system()
        
        # GUI起動
        from gui import VRChatCameraPinGUI
        
        gui = VRChatCameraPinGUI(pin_system)
        
        print("GUIを起動しています...")
        gui.run()
        
        # 終了処理
        pin_system.shutdown()
        return True
        
    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました")
        return False
    except ImportError as e:
        error_msg = f"必要なモジュールが見つかりません: {e}"
        print(error_msg)
        try:
            messagebox.showerror("モジュールエラー", error_msg)
        except:
            pass
        return False
    except Exception as e:
        error_msg = f"システムエラーが発生しました: {e}"
        print(error_msg)
        try:
            messagebox.showerror("システムエラー", error_msg)
        except:
            pass
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)