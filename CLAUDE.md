# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a distributed system for AI-based object/animal/person recognition implementing a concurrent and distributed architecture. The system consists of three main server components and one client:

- **Training Server (Servidor de entrenamiento)**: Receives input/output data and trains AI models in a distributed manner
- **Testing Server (Servidor de testeo)**: Uses trained models to process video frames from multiple cameras and detect objects
- **Video Server (Servidor de video)**: Handles video streaming from multiple IP cameras
- **Surveillance Client (Cliente vigilante)**: Displays detected objects with images, timestamps, and camera information

## Architecture

### System Components

1. **Training Server**
   - Receives training data (inputs/outputs) from clients
   - Distributes workload across nodes for model training
   - Persists trained models for later consumption by testing servers
   - Can process sequentially or in parallel/distributed mode
   - Must train to recognize "n" classes (objects/animals/people)

2. **Testing Server**
   - Loads pre-trained AI models
   - Processes video frames from "c" cameras autonomously
   - Detects trained objects in real-time
   - Saves detected object images to files
   - Maintains a registry of detections with metadata (object type, image, timestamp, camera ID)

3. **Video Server**
   - Handles multiple IP camera streams
   - Uses RTSP protocol or similar for camera communication
   - Distributes frames to testing servers

4. **Surveillance Client**
   - Displays detection registry continuously
   - Shows: object type, captured image, date/time, camera number

### Communication Protocol

- **MUST use raw Sockets only** - no websocket, socketio, frameworks, RabbitMQ, MQ, or communication libraries
- Use RTSP protocol or similar for IP camera communication
- Deploy on LAN and WIFI networks
- Use threading to improve performance and prevent registry corruption

### Concurrency Requirements

- Use threads to handle multiple concurrent operations
- Prevent race conditions when writing to detection registry
- Support multiple cameras processing frames simultaneously
- Distributed workload management across server nodes

## Project Constraints

### Required
- Multiple programming languages (LP1, LP2, LP3, ...) - more languages = better evaluation
- Socket-based communication only
- RTSP or similar protocol for IP cameras
- Threading for concurrency
- Architecture diagram
- Protocol diagram
- Deployment on cluster (virtual or physical)

### Forbidden
- websocket, socketio
- Frameworks for communication
- RabbitMQ, MQ, or other message queue libraries
- High-level communication libraries

## Evaluation Criteria

- Higher "n" (number of object classes to recognize) = better score
- Higher "c" (number of cameras) = better score
- Multiple programming languages = better score
- Groups with >2 students can improve "n" or "c" for bonus points

## Development Setup

The AI training module can be implemented in any programming language.

Server startup order:
1. Start video server
2. Start testing server
3. Start training server
4. Start client(s) - they will connect and send requests

## Deliverables

Compressed file containing:
- Source code files (LP1, LP2, LP3 extensions)
- PDF Report
- PDF Presentation
- Enhanced "n" or "c" for groups >2 students
