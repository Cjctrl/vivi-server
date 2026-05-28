---
tags: [user, robot_hardware_configuration_and_motor_specifications, frc, robotics, claude, ai-conversation]
---



# Robot hardware configuration and motor specifications

**Created:** 2026-01-24 18:55  
**Updated:** 2026-01-24 19:03

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-24 18:55

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

im trying to make a climber that will hook onto the bar then do a pivot pull

---

### 🤖 Claude · 2026-01-24 18:57

I'll help you create a climber subsystem for the 2026 FRC game REBUILT. Based on the game manual, robots can climb the TOWER to earn points, with three levels (LEVEL 1, LEVEL 2, and LEVEL 3) based on how high the robot's bumpers are positioned.

Here's a comprehensive climber subsystem with a hook mechanism and pivot pull:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create the commands to operate this climber:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create an example of how to integrate this into your RobotContainer:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've created a comprehensive climber subsystem for the 2026 REBUILT game. Here's what I've provided:

## **Key Features:**

### **1. Climber Subsystem (`ClimberSubsystem.java`)**
- **Hook and Pivot Mechanism**: Extends up to deploy a hook, then retracts to pull the robot up
- **Three Climbing Levels**: Corresponds to LEVEL 1, 2, and 3 scoring in the game
- **Motion Magic Control**: Smooth, profiled movement using TalonFX Motion Magic
- **Safety Features**:
  - Limit switch for calibration/zeroing
  - Soft limits to prevent over-extension
  - Stall detection
  - Current limiting
  - Gravity compensation

### **2. Position Constants (adjust these for your robot)**:
- **STOWED**: Starting position (0.0 rotations)
- **HOOK_DEPLOY**: Fully extended to reach rung (~15 rotations)
- **HOOK_ENGAGED**: Slight retraction to secure hook (~12 rotations)
- **CLIMB_PARTIAL**: Pull to Level 1 (~8 rotations)
- **CLIMB_MID**: Pull to Level 2 (~4 rotations)
- **CLIMB_FULL**: Pull to Level 3 (~0.5 rotations) - Maximum points!

### **3. Command Suite**:
- `CalibrateClimber`: Zero the encoder at limit switch
- `DeployHook`: Extend to reach the rung
- `EngageHook`: Retract slightly to secure
- `ClimbToLevel1/2/3`: Progressive climbing
- `FullClimbSequence`: One-button complete climb
- `ManualClimberControl`: Override for testing
- `HoldClimberPosition`: Low-voltage hold for stability

### **4. Control Options**:
**Option A - Automatic**: Press one button for full sequence
**Option B - Progressive**: Deploy → Engage → Choose level
**Option C - Manual**: Joystick control for fine adjustment

## **Setup Instructions:**

1. **Tune the position constants** based on your mechanism geometry
2. **Calibrate PID values** (start with provided values, then tune)
3. **Test each level** individually before trying full sequence
4. **Verify soft limits** to prevent mechanism damage
5. **Practice the sequence** - climbing is usually done in the last 30 seconds!

The code follows FRC best practices with safety features, telemetry, and both automatic and manual control options. Good luck with your climb! 🎯

---

### 🧑 CJ · 2026-01-24 19:00

im making the subsystem for the climber, not the command i neep to initilize the motors,  theres a lead and folow

---

### 🤖 Claude · 2026-01-24 19:00

I'll create a complete climber subsystem based on the Everybot design with a winch-and-barb mechanism. This will initialize the motors properly with a lead and follow configuration.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2026-01-24 19:00

it only has level 2 capablities

---

### 🤖 Claude · 2026-01-24 19:01

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've updated the climber subsystem for **Level 2 only** capabilities (20 points). Here are the key changes:

## **What Changed:**

### **1. Simplified Position Constants**
- **STOWED_POSITION** (0.0) - Starting position
- **DEPLOY_POSITION** (20.0) - Barb lowered for engagement  
- **CLIMB_LEVEL2_POSITION** (5.0) - Level 2 climb for 20 points
- Removed Level 1 and Level 3 positions

### **2. Simplified States**
- **STOWED** - Winch retracted, barb up
- **DEPLOYING** - Lowering barb
- **DEPLOYED** - Ready to hook
- **ENGAGED** - Barb hooked on tower
- **CLIMBING** - Pulling to Level 2
- **HOLDING** - Maintaining position
- **MANUAL** - Manual override

### **3. Core Methods**
```java
climber.calibrate();        // Zero at limit switch
climber.deploy();           // Lower barb
climber.engage();           // Secure hook
climber.climbToLevel2();    // Pull to Level 2
climber.holdPosition();     // Hold for endgame
climber.stow();             // Return to start
```

### **4. Key Features**
- ✅ **Lead/Follow motor setup** properly initialized
- ✅ **Limit switch** for calibration
- ✅ **Brake mode** prevents backslip (critical for winch!)
- ✅ **Current limiting** protects motors
- ✅ **Motion Magic** for smooth movement
- ✅ **Gravity compensation** for winch load
- ✅ **Telemetry** for debugging

**Next step:** Tune the position constants based on your winch spool diameter and strap length! 🎯

---

### 🧑 CJ · 2026-01-24 19:02

add constants as seaprate 

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

---

### 🤖 Claude · 2026-01-24 19:03

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me update the ClimberSubsystem to use these constants:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've separated all the constants into the `Constants.java` file. Here's what I've created:

## **📁 File Structure:**

### **1. Constants.java** (Updated)
Contains a new `ClimberConstants` inner class with all tunable values:

**Position Constants:**
- `STOWED_POSITION` - Zero point
- `DEPLOY_POSITION` - Barb lowered
- `ENGAGE_OFFSET` - How much to retract to secure
- `CLIMB_LEVEL2_POSITION` - Final climb position

**Motion Magic:**
- Cruise velocity, acceleration, jerk

**PID Gains:**
- kP, kI, kD, kS, kV, kA, kG

**Limits & Tolerances:**
- Soft limits, manual speed, stall detection

### **2. ClimberSubsystem.java** (Updated)
Now uses `ClimberConstants.*` throughout:
```java
import frc.robot.Constants.ClimberConstants;

// Example usage:
config.MotionMagic.MotionMagicCruiseVelocity = ClimberConstants.MOTION_CRUISE_VELOCITY;
leadMotor.setControl(motionMagicControl.withPosition(ClimberConstants.DEPLOY_POSITION));
```

## **✅ Benefits:**
1. **Easy Tuning** - All values in one place
2. **No Magic Numbers** - Every constant has a clear name
3. **Clean Code** - Subsystem focuses on logic, not values
4. **Team-Friendly** - Anyone can adjust constants without touching code logic

## **🔧 Next Steps:**
1. Adjust position constants based on your actual winch geometry
2. Tune PID values during testing
3. Test motion limits to prevent mechanism damage

All constants are now organized and ready for tuning! 🎯

---
claude-conversations-hub robot-hardware-configuration-and-motor-specifications

## Tags
#claude-conversations-hub #robot #robot-hardware-configuration-and-motor-specifications
