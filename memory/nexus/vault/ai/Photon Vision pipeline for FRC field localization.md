---
tags: [user, photon_vision_pipeline_for_frc_field_localization, frc, robotics, face-recognition, computer-vision, claude, ai-conversation]
---



# Photon Vision pipeline for FRC field localization

**Created:** 2026-02-21 18:04  
**Updated:** 2026-02-21 18:21

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-02-21 18:04

how would i config a pipline in photon vision for feild localization for frc 2026 rebuilt april tags and flied

---

### 🤖 Claude · 2026-02-21 18:04

The user is asking about configuring a pipeline in PhotonVision for field localization using AprilTags for FRC 2026. Let me answer from my knowledge - PhotonVision AprilTag pipeline configuration for field localization.## PhotonVision AprilTag Pipeline for FRC 2026 Field Localization

Here's how to set up a PhotonVision pipeline for multi-tag field localization:

---

### 1. Install the 2026 Field Layout

When the 2026 game launches, WPILib and PhotonVision will release an updated AprilTag field layout JSON. You'll need to:

- Download the official `2026-field.json` from the WPILib GitHub releases or the FRC game tools
- In the PhotonVision web UI, go to **Settings → AprilTag Fields** and upload the JSON file
- Select it as your active field layout

> Until the 2026 field map is released, you can use the 2025 "Reefscape" layout for testing.

---

### 2. Create an AprilTag Pipeline

In the PhotonVision dashboard:

1. Add a new pipeline → select **AprilTag**
2. Set the **tag family** to `36h11` (standard FRC family)
3. Under **AprilTag Settings**, enable **Do Multi-Target Estimation** — this is critical for field localization accuracy
4. Set **Tag Size** to the correct field tag size (usually **165.1 mm / 6.5 inches** for FRC)

---

### 3. Camera Calibration (Critical)

Field localization is very sensitive to calibration quality:

- Go to **Settings → Camera Calibration**
- Use a **9x6 chessboard or charuco board** printed at a known size
- Take **25–50 images** from varied angles and distances
- Aim for reprojection error **< 1.0 px** (ideally < 0.5)
- A poorly calibrated camera will give bad pose estimates

---

### 4. Set Camera Transform (Physical Mounting)

- In **Settings → Cameras**, set the **camera-to-robot transform**
- This is the 3D offset (X, Y, Z) and rotation (roll, pitch, yaw) from your camera lens to the robot's origin (typically center of the drive base at floor level)
- This must be accurate — measure carefully or use CAD

---

### 5. Robot Code Integration

Use the **PhotonVision vendor library** in your robot project:

```java
PhotonCamera camera = new PhotonCamera("YourCameraName");
PhotonPoseEstimator poseEstimator = new PhotonPoseEstimator(
    AprilTagFieldLayout.loadFromResource(AprilTagFields.k2026Crescendo), // update for 2026
    PoseStrategy.MULTI_TAG_PNP_ON_COPROCESSOR,
    camera,
    kRobotToCam // Transform3d of camera relative to robot
);
```

Then in your periodic:
```java
Optional<EstimatedRobotPose> result = poseEstimator.update();
result.ifPresent(pose -> {
    swerveDrivePoseEstimator.addVisionMeasurement(
        pose.estimatedPose.toPose2d(),
        pose.timestampSeconds,
        VecBuilder.fill(0.5, 0.5, 9999) // std devs — tune these
    );
});
```

**Recommended strategy:** `MULTI_TAG_PNP_ON_COPROCESSOR` — runs PnP solve on the PhotonVision coprocessor using all visible tags simultaneously. Much more accurate than single-tag estimation.

---

### 6. Tuning Tips

- **Standard deviations** passed to `addVisionMeasurement` should scale with distance — trust vision less when tags are far away
- Filter out poses where the estimated Z is wildly off (e.g., > 0.5m from floor) — these are bad solves
- Use **ambiguity filtering**: reject results where `pose.ambiguity > 0.2` on single-tag estimates
- Logs timestamps carefully — use `pose.timestampSeconds` for latency compensation

---

### Things to Watch for 2026 Specifically

- Wait for the official **2026 AprilTag field layout JSON** from WPILib after the game reveal
- Check PhotonVision release notes for any new 2026-specific features (they often add improvements during build season)
- Join the **PhotonVision Discord** — the devs are very active during FRC season and will post 2026 update notes there

Let me know if you want to go deeper on any part of this — camera selection, the math behind PnP, or tuning the pose estimator fusion!

---

### 🧑 CJ · 2026-02-21 18:14

wich way is positive and negitive on the center of the robot

---

### 🤖 Claude · 2026-02-21 18:14

The user is asking about the FRC coordinate system for robot-centric coordinates.## FRC Robot Coordinate System

FRC uses the **NWU (North-West-Up)** convention, which WPILib follows:

```
        +X (Forward / North)
           ↑
           |
 +Y ←------+------→ -Y
(Left)     |      (Right)
           ↓
        -X (Backward)

+Z = Up (out of the floor)
-Z = Down (into the floor)
```

### Breakdown

| Axis | Positive | Negative |
|------|----------|----------|
| **X** | Forward (front of robot) | Backward |
| **Y** | Left side of robot | Right side |
| **Z** | Up | Down |
| **Rotation (Yaw)** | Counter-clockwise | Clockwise |

---

### For Your Camera Transform

When you define your `Transform3d` for the camera-to-robot offset in PhotonVision, use these axes from the **robot's center at floor level**:

- Camera is **6 inches in front** of center → `X = +0.1524m`
- Camera is **4 inches to the right** → `Y = -0.1016m`
- Camera is **18 inches off the floor** → `Z = +0.4572m`

```java
Transform3d kRobotToCam = new Transform3d(
    new Translation3d(0.1524, -0.1016, 0.4572),
    new Rotation3d(0, 0, 0) // roll, pitch, yaw of camera
);
```

---

### Common Gotcha

This coordinate system is **robot-relative**, not field-relative. The front of *your robot* is always +X regardless of which way it's facing on the field. The field has its own separate coordinate system that the pose estimator handles for you.

---

### 🧑 CJ · 2026-02-21 18:18

witch one is robot to tranform

---

### 🤖 Claude · 2026-02-21 18:18

The user is asking about which tab/setting in PhotonVision is for the robot-to-camera transform. Looking at the screenshot, I can see tabs: INPUT, APRILTAG, OUTPUT, TARGETS, 3D. The 3D tab is where the camera-to-robot transform is configured.That's in the **3D** tab (far right in your tab bar)!

Click on **3D** and you'll see a field for the **Robot to Camera Transform** where you enter the X, Y, Z translation and roll, pitch, yaw rotation values for where your camera is mounted relative to the robot center.

Your current settings on the OUTPUT tab look great by the way — **Multi-Target Estimation is on** and max targets is 20, which is exactly what you want for field localization.

---

### 🧑 CJ · 2026-02-21 18:18

heres the 3d tab

---

### 🤖 Claude · 2026-02-21 18:19

The user is showing the 3D tab but it only shows "Target Visualization" with First Person/Third Person view. The Robot to Camera transform is actually in the Settings page, not the pipeline 3D tab. In PhotonVision, the camera transform is set in Settings → Cameras, not in the pipeline tabs.The Robot-to-Camera transform isn't in the pipeline tabs — it's in the **Settings page**! 

Click the **gear icon** on the left sidebar, then look for your camera and you'll see fields to enter the camera's **X, Y, Z, Roll, Pitch, Yaw** offset from the robot center.

What you're seeing in the 3D tab right now is just a visualization of where PhotonVision thinks the tags are relative to your camera — and it looks like it's detecting them correctly! The **purple cube** is your camera origin and the **teal cubes** are the detected AprilTags with their pose axes shown.

---

### 🧑 CJ · 2026-02-21 18:20

that takes ne to divice control

---

### 🤖 Claude · 2026-02-21 18:20

The user is saying the gear icon takes them to device control, not camera settings. In PhotonVision, the robot-to-camera transform is actually configured in the camera settings. Let me think about where this is in the PhotonVision UI.

In PhotonVision, the camera transform is set in the **Settings** page under the camera tab. The gear icon might be "device control." Let me think about the actual PhotonVision UI layout.

In PhotonVision's web UI, there's a left sidebar with icons. The robot-to-camera transform is typically found by clicking on the camera name/settings area. Actually, in newer versions of PhotonVision, I believe the transform is set in the pipeline's 3D tab itself - there should be a section below the visualization for entering the transform values.


Looking at the 3D tab more carefully, it seems to only show the target visualization controls, so the camera transform must be configured elsewhere. The camera icon on the left sidebar is likely where the robot-to-camera offset gets configured, separate from the device control settings.Try **scrolling down** on the 3D tab — the robot-to-camera transform fields might be **below** the visualization window! The page may just be cut off.

If not, try the **camera icon** on the left sidebar (looks like a camera) rather than the gear — some versions of PhotonVision put the camera transform settings there. What icons do you see on the left sidebar?

---

### 🤖 Claude · 2026-02-21 18:21

The user accidentally opened the "Robot Offset Mode" dropdown showing None, Single Point, Dual Point options. The camera transform is actually set in code (PhotonPoseEstimator), not in PhotonVision UI in newer versions.Looks like you accidentally opened the **Robot Offset Mode** dropdown — go ahead and keep that set to **None**.

The **camera-to-robot transform is actually not set in the PhotonVision UI anymore** in recent versions — it's set in your **robot code** when you create the `PhotonPoseEstimator`:

```java
Transform3d kRobotToCam = new Transform3d(
    new Translation3d(0.0, 0.0, 0.0), // X, Y, Z in meters from robot center
    new Rotation3d(0, 0, 0)           // roll, pitch, yaw in radians
);

PhotonPoseEstimator poseEstimator = new PhotonPoseEstimator(
    fieldLayout,
    PoseStrategy.MULTI_TAG_PNP_ON_COPROCESSOR,
    camera,
    kRobotToCam  // <-- this is where you set it
);
```

So just measure where your camera is physically mounted relative to your robot center and plug those numbers in here. You don't need to touch anything in the PhotonVision UI for the transform.

---
claude-conversations-hub photon-vision-pipeline-for-frc-field-localization

## Tags
#claude-conversations-hub #photon #photon-vision-pipeline-for-frc-field-localization
