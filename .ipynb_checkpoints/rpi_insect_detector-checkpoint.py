#!/usr/bin/env python3
"""
Raspberry Pi Insect Detection & Upload System
Captures images, runs YOLO detection, and uploads to Supabase via Flask API
(Updated: uses Device-Key by default and improved Picamera2 config)
"""

import os
import sys
import time
import base64
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO
from picamera2 import Picamera2
import requests

# =============================================================================
# CONFIGURATION - Update these values
# =============================================================================

# Device Configuration
DEVICE_KEY = "e3ffce0c332d47319d8f1fc13d80542b616e838655984a2f92da4a0c5f830136"  # Replace with actual device key from admin
USE_DEVICE_KEY = True  # Set to True to use DEVICE_KEY (recommended)
FARMER_ID = "farmer_001"  # Fallback (for testing)

# Model Configuration
MODEL_PATH = "/home/jpglobal/yolo/my_model_ncnn_model"  # Your YOLO NCNN model path (works with ultralytics YOLO wrapper)
CONFIDENCE_THRESHOLD = 0.5

# Camera Configuration
CAMERA_RESOLUTION = (854, 480)  # Width x Height
CAMERA_PREVIEW = True  # Show live preview window

# Camera color / AWB
AWB_MODE = 4  # 4 = Daylight ; adjust if needed
USE_COLOR_CORRECTION = True

# API Endpoint (must be the same as your working manual POST)
API_ENDPOINT = "https://jpglobal-ai.onrender.com/api/upload_result"

# Insect Label Mapping (update if your model label order differs)
INSECT_MAPPING = {
    0: "whiteflies",
    1: "aphids",
    2: "thrips",
    3: "beetle",
    4: "fungus gnats"
}

# =============================================================================
# CLASS: InsectDetector
# =============================================================================

class InsectDetector:
    def __init__(self):
        """Initialize the insect detector with camera and model"""
        print("=" * 60)
        print("JP Global InsectDetect - Raspberry Pi Detection System")
        print("=" * 60)

        # Load YOLO model
        print(f"\n[1/3] Loading YOLO model from: {MODEL_PATH}")
        try:
            # Using ultralytics YOLO wrapper. For NCNN converted models ensure the wrapper can load it;
            # if not, you may adapt to your NCNN inference wrapper.
            self.model = YOLO(MODEL_PATH, task='detect')
            self.labels = self.model.names
            print(f"✓ Model loaded successfully")
            print(f"✓ Detected classes: {self.labels}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            sys.exit(1)

        # Initialize camera (Picamera2) using XRGB8888 for best OpenCV compatibility
        print(f"\n[2/3] Initializing Picamera2 at {CAMERA_RESOLUTION[0]}x{CAMERA_RESOLUTION[1]}")
        try:
            self.camera = Picamera2()

            # Use XRGB8888 config to capture BGRA arrays suitable for OpenCV conversion
            camera_config = self.camera.create_video_configuration(
                main={"format": "XRGB8888", "size": CAMERA_RESOLUTION}
            )
            self.camera.configure(camera_config)

            # Try to set helpful AWB/exposure controls (will be ignored if not supported)
            try:
                self.camera.set_controls({
                    "AwbEnable": True,
                    "AwbMode": AWB_MODE,
                    "AeEnable": True,
                    # Brightness/Contrast/Saturation controls may be camera dependent
                })
            except Exception:
                # Some Picamera2 versions or sensor drivers might not accept these controls;
                # that's fine — we continue.
                pass

            self.camera.start()
            time.sleep(1.5)  # Let camera auto-exposure / AWB stabilise
            print("✓ Camera initialized successfully")
            print("✓ Color correction applied (if supported by camera)")
        except Exception as e:
            print(f"✗ Error initializing camera: {e}")
            sys.exit(1)

        # Verify API connectivity
        print(f"\n[3/3] Verifying API connectivity to: {API_ENDPOINT}")
        if self._test_connection():
            print("✓ API connection verified")
        else:
            print("⚠ Warning: Could not verify API connection (continuing; uploads may fail)")

        # Set bounding box colors (kept simple)
        self.bbox_colors = [
            (164, 120, 87),   # neutral
            (68, 148, 228),
            (93, 97, 209),
            (178, 182, 133),
            (88, 159, 106)
        ]

        print("\n" + "=" * 60)
        print("System Ready!")
        print("=" * 60)
        print("\nControls:")
        print("  [SPACEBAR] - Capture & Upload")
        print("  [Q]        - Quit")
        print("  [S]        - Save image locally (no upload)")
        print("\n" + "=" * 60 + "\n")

    def _test_connection(self):
        """Test connection to the API endpoint (uses Device-Key if configured)"""
        try:
            headers = {}
            if USE_DEVICE_KEY and DEVICE_KEY:
                headers["Device-Key"] = DEVICE_KEY
            # Use a short timeout
            r = requests.get(API_ENDPOINT.replace("/api/upload_result", "/health"), headers=headers, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def capture_frame(self):
        """Capture a frame from the camera and return BGR numpy array for OpenCV processing"""
        # Picamera2 configured with XRGB8888 -> capture_array returns BGRA-like array
        frame_bgra = self.camera.capture_array()
        # Convert BGRA -> BGR for OpenCV
        frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

        # Apply minor software color correction if desired
        if USE_COLOR_CORRECTION:
            # subtle adjustments, avoid harsh scaling
            # reduce blue slightly, increase red slightly to reduce blue tint
            frame = frame.astype(np.float32)
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 0.95, 0, 255)  # Blue channel
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 1.05, 0, 255)  # Red channel
            frame = frame.astype(np.uint8)

        return frame

    def detect_insects(self, frame):
        """Run YOLO detection on the frame and return detections + annotated frame"""
        results = self.model(frame, verbose=False)
        detections = results[0].boxes

        detected_insects = []
        annotated_frame = frame.copy()

        for i in range(len(detections)):
            # Extract bbox coordinates
            xyxy_tensor = detections[i].xyxy.cpu()
            xyxy = xyxy_tensor.numpy().squeeze()
            xmin, ymin, xmax, ymax = xyxy.astype(int)

            # Class and confidence
            class_idx = int(detections[i].cls.item())
            confidence = float(detections[i].conf.item())
            class_name = self.labels.get(class_idx, str(class_idx)) if isinstance(self.labels, dict) else (self.labels[class_idx] if class_idx < len(self.labels) else str(class_idx))

            if confidence >= CONFIDENCE_THRESHOLD:
                insect_name = INSECT_MAPPING.get(class_idx, class_name).lower()
                detected_insects.append({
                    'insect': insect_name,
                    'confidence': confidence,
                    'bbox': (xmin, ymin, xmax, ymax)
                })

                color = self.bbox_colors[class_idx % len(self.bbox_colors)]
                cv2.rectangle(annotated_frame, (xmin, ymin), (xmax, ymax), color, 2)
                label = f"{insect_name}: {int(confidence * 100)}%"
                label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_ymin = max(ymin, label_size[1] + 10)
                cv2.rectangle(annotated_frame,
                              (xmin, label_ymin - label_size[1] - 10),
                              (xmin + label_size[0], label_ymin + baseline - 10),
                              color, cv2.FILLED)
                cv2.putText(annotated_frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return detected_insects, annotated_frame

    def upload_to_supabase(self, image, detections):
        """Upload detection results to Flask API (Supabase stored server-side)"""
        if len(detections) == 0:
            print("⚠ No insects detected - skipping upload")
            return False

        print(f"\n📤 Uploading detection results...")
        # Count insects by type
        insect_counts = {}
        for det in detections:
            insect_counts[det['insect']] = insect_counts.get(det['insect'], 0) + 1

        for insect, cnt in insect_counts.items():
            print(f"   - {insect}: {cnt}")

        primary_insect = max(insect_counts, key=insect_counts.get)
        total_count = sum(insect_counts.values())

        # Encode image to base64 (same format as your working example)
        success, buffer = cv2.imencode('.jpg', image)
        if not success:
            print("✗ Failed to encode image")
            return False
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        payload = {
            "insect": primary_insect,
            "count": total_count,
            "image_base64": image_base64
        }

        headers = {"Content-Type": "application/json"}
        if USE_DEVICE_KEY and DEVICE_KEY:
            headers["Device-Key"] = DEVICE_KEY
            print("   Using device key authentication")
        else:
            # Include farmer_id as fallback if device key not used
            payload["farmer_id"] = FARMER_ID
            print(f"   Using farmer_id in payload: {FARMER_ID}")
            print("   ⚠️  Note: For production, get a device key from admin panel")

        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                print("✓ Upload successful!")
                print(f"   Status: {result.get('status')}")
                if 'image_url' in result:
                    print(f"   Image URL: {result['image_url'][:80]}...")
                return True
            else:
                print(f"✗ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False

        except requests.exceptions.Timeout:
            print("✗ Upload timeout - check your internet connection")
            return False
        except Exception as e:
            print(f"✗ Upload error: {e}")
            return False

    def save_locally(self, image, detections, prefix="capture"):
        """Save image locally with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        cv2.imwrite(filename, image)
        print(f"💾 Saved locally: {filename}")
        return filename

    def run(self):
        """Main detection loop with live preview"""
        try:
            while True:
                frame = self.capture_frame()
                detections, annotated_frame = self.detect_insects(frame)

                status_text = f"Detections: {len(detections)} | Press [SPACE] to capture"
                cv2.putText(annotated_frame, status_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                if CAMERA_PREVIEW:
                    cv2.imshow('InsectDetect - Live Preview', annotated_frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord(' '):  # Spacebar - Capture and upload
                    print("\n" + "="*60)
                    print("📸 CAPTURE TRIGGERED")
                    print("="*60)

                    capture_frame = self.capture_frame()
                    detections, annotated_capture = self.detect_insects(capture_frame)

                    if len(detections) > 0:
                        saved_file = self.save_locally(annotated_capture, detections, prefix="detection")
                        self.upload_to_supabase(annotated_capture, detections)
                    else:
                        print("⚠ No insects detected in capture")
                        # On headless device you may want default behaviour - here we ask interactively
                        try:
                            save_anyway = input("Save image anyway? (y/n): ")
                        except Exception:
                            save_anyway = 'n'
                        if save_anyway.lower() == 'y':
                            self.save_locally(annotated_capture, detections, prefix="no_detection")

                    print("="*60 + "\n")

                elif key == ord('s') or key == ord('S'):  # Save locally only
                    capture_frame = self.capture_frame()
                    detections, annotated_capture = self.detect_insects(capture_frame)
                    self.save_locally(annotated_capture, detections, prefix="manual_save")

                elif key == ord('q') or key == ord('Q'):  # Quit
                    print("\n👋 Shutting down...")
                    break

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up resources...")
        try:
            self.camera.stop()
        except Exception:
            pass
        cv2.destroyAllWindows()
        print("✓ Cleanup complete")
        print("\nThank you for using JP Global InsectDetect!")

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    # If you want to test via farmer_id instead of device key, set USE_DEVICE_KEY = False above.
    if USE_DEVICE_KEY and (not DEVICE_KEY or DEVICE_KEY == "YOUR_DEVICE_KEY_HERE"):
        print("⚠️  WARNING: DEVICE_KEY not configured correctly.")
        print("   Changing to farmer_id fallback for this run.")
        time.sleep(2)

    detector = InsectDetector()
    detector.run()

if __name__ == "__main__":
    main()
