---
tags: [user, aligning_constants_with_photonlib, frc, first-robotics, constants, photonvision, photonlib, wpi-lib, java, robotics, 2026, claude-conversation]
---



# Aligning constants with PhotonLib

**Created:** 2026-01-17 19:03  
**Updated:** 2026-01-17 19:04

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-17 19:03

```java
// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot;

/**
 * The Constants class provides a convenient place for teams to hold robot-wide numerical or boolean
 * constants. This class should not be used for any other purpose. All constants should be declared
 * globally (i.e. public static). Do not put anything functional in this class.
 *
 * <p>It is advised to statically import this class (or one of its inner classes) wherever the
 * constants are needed, to reduce verbosity.
 */
public final class Constants {
  public static class OperatorConstants {
    public static final int kDriverControllerPort = 0;
  }
}

```

make the constants macth the photon lib and vice versa

---

### 🤖 Claude · 2026-01-17 19:04

I'll help you create matching constants between the PhotonVision subsystem and the Constants class. Here's an updated Constants file with vision-specific constants that match your PhotonVision implementation:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now I'll update the PhotonVision subsystem to use these constants:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've updated both files to work together:

## Key Changes:

### Constants.java
- Added `VisionConstants` inner class with all configuration values
- Camera names match PhotonVision dashboard requirements
- Camera transforms broken down into individual measurement constants for easy tuning
- Added filtering thresholds (ambiguity, tag count, distance)
- Added standard deviation values for pose estimator fusion
- Added pipeline index constants

### photonVision.java
- Now imports and uses `VisionConstants` throughout
- Camera initialization uses constant names
- Transform3d creation uses constant transforms
- Added `filterMeasurement()` method that applies ambiguity threshold
- Added `setAprilTagPipeline()` convenience method
- Improved documentation referencing the constants

## Benefits:
1. **Single source of truth** - all vision config in Constants.java
2. **Easy tuning** - adjust camera positions, thresholds in one place
3. **Type safety** - constants are compile-time checked
4. **Team workflow** - follows FRC best practices for constant organization

You can now easily adjust camera positions, filtering parameters, and other settings in the Constants file without touching the subsystem code!

---
aligning-constants-with-photonlib claude-conversations-hub

## Tags
#aligning #aligning-constants-with-photonlib #claude-conversations-hub
