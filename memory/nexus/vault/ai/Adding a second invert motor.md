---
tags: [user, adding_a_second_invert_motor, frc, first-robotics, java, motor-control, kicker-subsystem, wpi-lib, ctre, talonfx, inverted-motor, robotics, 2026, claude-conversation]
---



# Adding a second invert motor

**Created:** 2026-01-24 18:42  
**Updated:** 2026-01-24 18:43

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-24 18:42

add a second invert motor

---

### 🤖 Claude · 2026-01-24 18:42

I'll help you add a second inverted motor to the KickerSubsystem. Looking at your code, I can see you have `kickerMotorBottom` and `kickerMotorTop` declared but only `kickerMotor` is being used. Here's the updated code with both motors properly configured:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

## Key Changes Made:

1. **Both motors now initialized**: Changed from single `kickerMotor` to `kickerMotorBottom` and `kickerMotorTop`

2. **Top motor inverted**: In `configureMotors()`, the top motor is configured with `config.MotorOutput.Inverted = true`

3. **All methods updated**: Updated `runManual()`, `stop()`, `setNeutralMode()`, and `setOutputVoltage()` to control both motors

4. **SmartDashboard enhancements**: Now displays velocity for both motors separately

5. **New method added**: `getAverageVelocity()` to get the average velocity of both motors

## What You Need to Update in HardwareMap:

Make sure your `HardwareMap` class has these CAN IDs defined:
```java
public static final int KICKER_MOTOR_BOTTOM = /* your CAN ID */;
public static final int KICKER_MOTOR_TOP = /* your CAN ID */;
```

The top motor will spin in the opposite direction from the bottom motor, which is typical for roller/kicker mechanisms where motors face each other.

---

### 🧑 CJ · 2026-01-24 18:43

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
    public static final int PWM_PORT_BLING2 = 1;} 
```

update it

---

### 🤖 Claude · 2026-01-24 18:43

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Updated! I've changed the kicker motor IDs from:
- `KICKER_MOTOR_LEAD` → `KICKER_MOTOR_BOTTOM` (CAN ID 70)
- `KICKER_SENSOR_FOLLOW` → `KICKER_MOTOR_TOP` (CAN ID 71)

I also fixed the formatting issue with the DIO PORTS comment. Now your kicker subsystem will properly initialize both motors with the correct CAN IDs!

---
adding-a-second-invert-motor claude-conversations-hub

## Tags
#adding #adding-a-second-invert-motor #claude-conversations-hub
