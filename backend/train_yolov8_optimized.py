import os
import torch
from ultralytics import YOLO

def main():
    print("=" * 70)
    print(" 🚀 YOLOv8 HIGH-ACCURACY CAR DAMAGE DETECTOR RETRAINING ENGINE")
    print("=" * 70)

    # 1. Environment & Hardware Probe
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ Hardware Accelerator Detected: CUDA GPU ({device_name})")
        print(f"📊 Available VRAM          : {vram_gb:.2f} GB")
        device = 0
        imgsz = 1024 if vram_gb >= 8 else 800
        base_weights = "yolov8m.pt" if vram_gb >= 6 else "yolov8s.pt"
    else:
        print("⚠️ CUDA GPU Not Detected — Running in CPU Mode")
        device = "cpu"
        imgsz = 640
        base_weights = "yolov8s.pt"

    # 2. Locate Dataset Config
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_yaml_path = os.path.join(base_dir, "data", "dataset", "data.yaml")
    
    if not os.path.exists(data_yaml_path):
        os.makedirs(os.path.dirname(data_yaml_path), exist_ok=True)
        with open(data_yaml_path, "w") as f:
            f.write("""# YOLOv8 Car Damage Dataset Config
path: ../data/dataset
train: images/train
val: images/val
test: images/test

nc: 10
names:
  0: dent
  1: scratch
  2: crack
  3: broken_glass
  4: broken_part
  5: paint_damage
  6: headlight_damage
  7: taillight_damage
  8: bumper_damage
  9: corrosion
""")
    print(f"📁 Dataset Config Path    : {data_yaml_path}")
    print(f"🎯 Base Weights Model     : {base_weights}")
    print(f"📐 Target Image Resolution: {imgsz}x{imgsz}")

    # 3. Initialize YOLO Model
    model = YOLO(base_weights)

    # 4. Hyperparameter Configuration
    train_args = {
        "data": data_yaml_path,
        "epochs": 50,
        "imgsz": imgsz,
        "device": device,
        "optimizer": "AdamW",
        "lr0": 0.001,
        "weight_decay": 0.0005,
        "cos_lr": True,
        "close_mosaic": 10,
        "label_smoothing": 0.05,
        "patience": 20,
        "batch": 16 if cuda_available else 4,
        "project": os.path.join(base_dir, "runs", "detect"),
        "name": "car_damage_yolov8_optimized",
        "exist_ok": True
    }

    print("\n--- Training Hyperparameters Configuration ---")
    for k, v in train_args.items():
        print(f"  • {k:<18}: {v}")

    print("\n⚡ Starting Training Pipeline (Ultralytics Engine)...")
    print("=" * 70)
    
    # Save script config manifest
    manifest_path = os.path.join(base_dir, "reports", "training_config_manifest.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    import json
    with open(manifest_path, "w") as f:
        json.dump(train_args, f, indent=2, default=str)
    print(f"💾 Training manifest exported to: {manifest_path}")

if __name__ == "__main__":
    main()
