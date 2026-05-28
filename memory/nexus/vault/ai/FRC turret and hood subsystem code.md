---
tags: [user, frc_turret_and_hood_subsystem_code, frc, robotics, python, programming, claude, ai-conversation]
---



# FRC turret and hood subsystem code

**Created:** 2026-01-20 01:49  
**Updated:** 2026-01-20 01:50

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-20 01:49

✅ Prompt to Use with Claude or Other LLMs
I have an FRC robot subsystem for a turret that can rotate left and right and has an adjustable hood for changing the shot angle. Each motion (left/right and hood) is powered by a single NEO motor.
I want WPILib Java code that:
* Uses the REV Robotics libraries (REVLib / REV Robotics API) for motor control.
* Controls two subsystems: a Turret Rotation and a Hood Adjuster.
* Uses CANSparkMax controllers with encoders for feedback.
* Provides methods to:
   * Rotate turret to a desired angle (in degrees)
   * Adjust hood to a desired angle (in degrees)
   * Run simple manual control (joystick axis, buttons)
* Includes basic conversion from encoder units ↔ degrees based on a gearbox ratio and sensor units.
* Contains safety limits so the turret and hood don’t move outside configured min/max positions.
* Uses WPILib’s command-based structure (Subsystem + Commands).
Assume:
* Turret rotation is a continuous rotation with zero at forward center and uses a CAN ID of `1`.
* Hood adjuster uses a CAN ID of `2`.
* You have calibration constants for min and max safe angles:
   * Turret: -180° to +180°
   * Hood: 0° to 60°
* Use REV CANSparkMax motors with integrated encoders and built-in PID control via the REV libraries.

```java
package frc.robot.staticConstants;


//  This class contains the hardware ID mappings for the robot's components.
public class HardwareMap {
    // Swerve Drive (12 IDs)
    public static final int SWERVE_FL_DRIVE = 1;
    public static final int SWERVE_FL_STEER = 11;
    public static final int SWERVE_FR_DRIVE = 2;
    public static final int SWERVE_FR_STEER = 124;
    public static final int SWERVE_BL_DRIVE = 3;
    public static final int SWERVE_BL_STEER = 13;
    public static final int SWERVE_BR_DRIVE = 4;
    public static final int SWERVE_BR_STEER = 14;
    public static final int SWERVE_FL_ENCODER = 21;
    public static final int SWERVE_FR_ENCODER = 22;
    public static final int SWERVE_BL_ENCODER = 23;
    public static final int SWERVE_BR_ENCODER = 24;

    // Climber (2 IDs)
    public static final int CLIMBER_MOTOR_LEAD = 50;
    public static final int CLIMBER_MOTOR_FOLLOW = 51;

    // Shooter (2 IDs)
    public static final int SHOOTER_MOTOR_LEAD = 55;
    public static final int SHOOTER_SENSOR_FOLLOW = 56;

    // Intake (2 IDs)
    public static final int INTAKE_MOTOR_LEAD = 60;
    public static final int INTAKE_SENSOR_FOLLOW = 61;

    // Hopper Agitator (2 IDs)
    public static final int HOPPER_AGITATOR_MOTOR_LEAD = 65;
    public static final int HOPPER_AGITATOR_SENSOR_FOLLOW = 66;

    // Kicker (2 IDs)
    public static final int KICKER_MOTOR_LEAD = 70;
    public static final int KICKER_SENSOR_FOLLOW = 71;

//DIO PORTS on the RoboRIO (4 PORTS)
    public static final int INTAKE_BEAM_BREAK_SENSOR = 0;
    public static final int HOPPER_BEAM_BREAK_SENSOR = 1;
    public static final int SHOOTER_BEAM_BREAK_SENSOR = 2;
    public static final int CLIMBER_LIMIT_SWITCH = 3;

    // Joystick USB Ports (2 PORTS)
    public static final int DRIVER_JOYSTICK_PORT = 0;   
    public static final int OPERATOR_BUTTONBOX_PORT = 1;

    // BUTTON BOX BUTTONS
    public static final int BUTTON_BOX_SHOOT_GOAL = 1;
 
    // PWM Ports on the RoboRIO
    public static final int PWM_PORT_BLING = 0;
    public static final int PWM_PORT_BLING2 = 1;

}
```


```java

// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot.staticConstants;

/**
 * This is where we store the maximum recommended amperage for each of
 * our motors from Vex Robotics.
 * https://motors.vex.com/
 * 
 * We will call this class as we initiatize our motor controllers.
 */

public class MaxMotorAmps {
     // Falcon 500 Current Limit settings
     public static final double MAX_AMPS_STATOR_LIMIT_FALCON500 = 30;
     public static final double MAX_AMPS_STATOR_TRIGGER_FALCON500 = 40;
     // public static final double MAX_AMPS_STATOR_LIMIT_FALCON500 = 15;  //To protect falcons during testing
     // public static final double MAX_AMPS_STATOR_TRIGGER_FALCON500 = 20; //To protect falcons during testing
     public static final double MAX_SECS_STATOR_THRESHOLDTIME_FALCON500 = 1; // Number of seconds of exceeding current trigger threshold. 
     // Neo 550 Current Limit Settings
     public static final int MAX_AMPS_STATOR_LIMIT_NEO550 = 20;
     public static final int MAX_AMPS_STATOR_TRIGGER_NEO550 = 30;
     public static final double MAX_SECS_STATOR_THRESHOLDTIME_NEO550 = 60;
     // 775 PRO Current Limit Settings
     public static final int MAX_AMPS_STATOR_LIMIT_775PRO = 30;
     public static final int MAX_AMPS_STATOR_TRIGGER_775PRO = 40;
     public static final int MAX_SECS_STATOR_THRESHOLDTIME_775PRO = 60;
     // NEO Current Limit Settings
     public static final int MAX_AMPS_STATOR_LIMIT_NEO = 40;
     public static final int MAX_AMPS_STATOR_TRIGGER_NEO = 50;
     public static final int MAX_AMPS_STATOR_THRESHOLDTIME_NEO = 60;
     // We will figure these ones out later..
     public static final double MAX_AMPS_CIM = 0;
     public static final double MAX_AMPS_MINICIM = 0;
     public static final double MAX_AMPS_REDLINE = 0;
     public static final double MAX_AMPS_BAG = 0;
}

```

---

### 🤖 Claude · 2026-01-20 01:50

I'll create a comprehensive turret and hood subsystem implementation for your FRC robot using WPILib's command-based structure and REV Robotics libraries.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

I've created a complete implementation for your turret and hood subsystems! Here's what I've provided:

## Key Features:

### **TurretSubsystem & HoodSubsystem**
- ✅ Uses REV CANSparkMax with built-in PID control
- ✅ Encoder position feedback with automatic degree conversion
- ✅ Safety limits enforced (Turret: -180° to +180°, Hood: 0° to 60°)
- ✅ Current limiting using your MaxMotorAmps constants
- ✅ Closed-loop position control methods
- ✅ Manual control methods with limit protection

### **Commands Included:**
1. **SetTurretAngleCommand** - Move turret to specific angle
2. **SetHoodAngleCommand** - Move hood to specific angle  
3. **ManualTurretCommand** - Joystick control with deadband
4. **ManualHoodCommand** - Joystick control with deadband

### **Important Configuration Notes:**

**Update your HardwareMap.java** with these IDs:
```java
public static final int TURRET_MOTOR = 75;
public static final int HOOD_MOTOR = 76;
```

**Tune these constants for your robot:**
- `GEAR_RATIO` - Critical for accurate angle calculations
- PID values (`kP`, `kI`, `kD`, `kFF`) - Will need tuning on actual hardware
- `kMaxOutput`/`kMinOutput` - Adjust for desired speed/safety

**Important:** The encoders reset to zero on initialization. You'll need to manually position the turret to center (0°) and hood to minimum (0°) before enabling the robot, or implement a homing routine.

The example usage at the bottom shows how to integrate these subsystems into your RobotContainer with both manual and automated control!

---
claude-conversations-hub frc-turret-and-hood-subsystem-code

## Tags
#claude-conversations-hub #frc #frc-turret-and-hood-subsystem-code
