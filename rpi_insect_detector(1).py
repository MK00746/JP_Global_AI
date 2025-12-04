#!/usr/bin/env python3
"""
Raspberry Pi Insect Detection & Upload System
Captures images, runs YOLO detection, and uploads to Supabase
"""

import os
import sys
import time
import base64
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
from ultralytics import YOLO
from picamera2 import Picamera2
import requests

# =============================================================================
# CONFIGURATION - Update these values
# =============================================================================

# Supabase Configuration (will be automatically handled by your Flask API)
# No need to configure these - your Flask app handles Supabase connection

# Device Configuration
# OPTION 1: Use Device Key (Recommended - Get from admin panel)
DEVICE_KEY = "e3ffce0c332d47319d8f1fc13d80542b616e838655984a2f92da4a0c5f830136"  # Replace with actual device key from admin

# OPTION 2: Use Farmer ID directly (For testing only)
USE_DEVICE_KEY = False  # Set to True after you get device key from admin
FARMER_ID = "farmer_001"  # Your farmer ID

# Model Configuration
MODEL_PATH = "my_model_ncnn_model"  # Your YOLO NCNN model
CONFIDENCE_THRESHOLD = 0.5

# Camera Configuration
CAMERA_RESOLUTION = (854, 480)  # Width x Height
CAMERA_PREVIEW = True  # Show live preview window

# API Endpoint
API_ENDPOINT = "https://jpglobal-ai.onrender.com/api/upload_result"

# Insect Label Mapping (update based on your model's class names)
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
            self.model = YOLO(MODEL_PATH, task='detect')
            self.labels = self.model.names
            print(f"✓ Model loaded successfully")
            print(f"✓ Detected classes: {self.labels}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            sys.exit(1)
        
        # Initialize camera
        print(f"\n[2/3] Initializing Picamera2 at {CAMERA_RESOLUTION[0]}x{CAMERA_RESOLUTION[1]}")
        try:
            self.camera = Picamera2()
            config = self.camera.create_video_configuration(
                main={"format": 'RGB888', "size": CAMERA_RESOLUTION}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # Let camera warm up
            print("✓ Camera initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing camera: {e}")
            sys.exit(1)
        
        # Verify API connectivity
        print(f"\n[3/3] Verifying API connectivity to: {API_ENDPOINT}")
        if self._test_connection():
            print("✓ API connection verified")
        else:
            print("⚠ Warning: Could not verify API connection")
            print("  Continuing anyway - uploads may fail")
        
        # Set bounding box colors
        self.bbox_colors = [
            (255, 127, 80),   # Coral - whiteflies
            (64, 156, 255),   # Blue - aphids
            (76, 217, 100),   # Green - thrips
            (175, 82, 222),   # Purple - beetle
            (255, 204, 0)     # Gold - fungus gnats
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
        """Test connection to the API endpoint"""
        try:
            # Try to reach the health endpoint or base URL
            response = requests.get(API_ENDPOINT.replace('/api/upload_result', '/health'), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def capture_frame(self):
        """Capture a frame from the camera"""
        frame = self.camera.capture_array()
        # Convert RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame
    
    def detect_insects(self, frame):
        """Run YOLO detection on the frame"""
        results = self.model(frame, verbose=False)
        detections = results[0].boxes
        
        detected_insects = []
        annotated_frame = frame.copy()
        
        for i in range(len(detections)):
            # Get bounding box coordinates
            xyxy_tensor = detections[i].xyxy.cpu()
            xyxy = xyxy_tensor.numpy().squeeze()
            xmin, ymin, xmax, ymax = xyxy.astype(int)
            
            # Get class and confidence
            class_idx = int(detections[i].cls.item())
            confidence = detections[i].conf.item()
            class_name = self.labels[class_idx]
            
            # Only process if confidence is above threshold
            if confidence >= CONFIDENCE_THRESHOLD:
                # Map to standardized insect name
                insect_name = INSECT_MAPPING.get(class_idx, class_name)
                detected_insects.append({
                    'insect': insect_name,
                    'confidence': confidence,
                    'bbox': (xmin, ymin, xmax, ymax)
                })
                
                # Draw bounding box
                color = self.bbox_colors[class_idx % len(self.bbox_colors)]
                cv2.rectangle(annotated_frame, (xmin, ymin), (xmax, ymax), color, 2)
                
                # Draw label
                label = f'{insect_name}: {int(confidence*100)}%'
                label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_ymin = max(ymin, label_size[1] + 10)
                cv2.rectangle(annotated_frame, 
                            (xmin, label_ymin - label_size[1] - 10),
                            (xmin + label_size[0], label_ymin + baseline - 10),
                            color, cv2.FILLED)
                cv2.putText(annotated_frame, label, (xmin, label_ymin - 7),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return detected_insects, annotated_frame
    
    def upload_to_supabase(self, image, detections):
        """Upload detection results to Supabase via Flask API"""
        
        if len(detections) == 0:
            print("⚠ No insects detected - skipping upload")
            return False
        
        print(f"\n📤 Uploading detection results...")
        print(f"   Detected {len(detections)} insect(s)")
        
        # Count insects by type
        insect_counts = {}
        for det in detections:
            insect_name = det['insect']
            insect_counts[insect_name] = insect_counts.get(insect_name, 0) + 1
        
        # Display what was detected
        for insect, count in insect_counts.items():
            print(f"   - {insect}: {count}")
        
        # Use the most common insect for the primary classification
        primary_insect = max(insect_counts, key=insect_counts.get)
        total_count = sum(insect_counts.values())
        
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare payload
        payload = {
            "insect": primary_insect,
            "count": total_count,
            "image_base64": image_base64
        }
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        if USE_DEVICE_KEY:
            headers["Device-Key"] = DEVICE_KEY
            print(f"   Using device key authentication")
        else:
            payload["farmer_id"] = FARMER_ID
            print(f"   Using farmer_id: {FARMER_ID}")
        
        # Send request
        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Upload successful!")
                print(f"   Status: {result.get('status')}")
                if 'image_url' in result:
                    print(f"   Image URL: {result['image_url'][:50]}...")
                return True
            else:
                print(f"✗ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"✗ Upload timeout - check your internet connection")
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
                # Capture frame
                frame = self.capture_frame()
                
                # Run detection for preview
                detections, annotated_frame = self.detect_insects(frame)
                
                # Add status overlay
                status_text = f"Detections: {len(detections)} | Press [SPACE] to capture"
                cv2.putText(annotated_frame, status_text, (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Show preview
                if CAMERA_PREVIEW:
                    cv2.imshow('InsectDetect - Live Preview', annotated_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):  # Spacebar - Capture and upload
                    print("\n" + "="*60)
                    print("📸 CAPTURE TRIGGERED")
                    print("="*60)
                    
                    # Capture fresh frame
                    capture_frame = self.capture_frame()
                    detections, annotated_capture = self.detect_insects(capture_frame)
                    
                    if len(detections) > 0:
                        # Save locally first
                        self.save_locally(annotated_capture, detections, prefix="detection")
                        
                        # Upload to Supabase
                        self.upload_to_supabase(annotated_capture, detections)
                    else:
                        print("⚠ No insects detected in capture")
                        save_anyway = input("Save image anyway? (y/n): ")
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
        self.camera.stop()
        cv2.destroyAllWindows()
        print("✓ Cleanup complete")
        print("\nThank you for using JP Global InsectDetect!")

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    # Validate configuration
    if USE_DEVICE_KEY and DEVICE_KEY == "YOUR_DEVICE_KEY_HERE":
        print("⚠️  WARNING: DEVICE_KEY not configured")
        print("   You can still test with farmer_id, but device key is recommended")
        print("   To get a device key:")
        print("   1. Login to https://jpglobal-ai.onrender.com as admin")
        print("   2. Go to Device Management")
        print("   3. Create a new device and copy the key")
        print("\n   Continuing with farmer_id for now...\n")
        time.sleep(3)
    
    # Initialize and run detector
    detector = InsectDetector()
    detector.run()

if __name__ == "__main__":
    main()
