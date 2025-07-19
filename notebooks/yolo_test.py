#!/usr/bin/env python3
import cv2
import rerun as rr
import requests
from ultralytics import YOLO

def download_video():
    url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_5mb.mp4"
    try:
        response = requests.get(url, stream=True)
        with open("test_video.mp4", "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        return "test_video.mp4"
    except:
        return None

def main():
    # Initialize
    rr.init("YOLO_Detection", spawn=True)
    model = YOLO("yolo11n.pt")
    
    # Load video
    video_path = "people.mp4"
    if not video_path:
        return
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        # Convert BGR to RGB (OpenCV uses BGR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Log image
        rr.log(f"frame_{frame_count}/image", rr.Image(rgb_frame))
        
        # YOLO detection
        results = model(frame, conf=0.35, verbose=False)
        
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()
            scores = results[0].boxes.conf.cpu().numpy()
            
            if len(boxes) > 0:
                labels = [f"{model.names[int(cls)]} {score:.2f}" 
                            for cls, score in zip(classes, scores)]
                
                # Log boxes
                rr.log(f"frame_{frame_count}/detections", 
                        rr.Boxes2D(
                            array=boxes, 
                            array_format=rr.Box2DFormat.XYXY,
                            labels=labels
                        ))
                
                print(f"Frame {frame_count}: {len(boxes)} detections")
            
        frame_count += 1
    
    cap.release()
    
    import time
    time.sleep(30)

if __name__ == "__main__":
    main()