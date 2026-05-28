---
tags: [user, fix_imports, claude, ai-conversation]
---



# Fix imports

**Created:** 2026-01-24 18:14  
**Updated:** 2026-01-24 18:14

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-01-24 18:14

fix imports now

---

### 🤖 Claude · 2026-01-24 18:14

I can see your code has several import issues. Here's the corrected import section:

```java
package frc.robot.subsystems; 

import java.util.function.BooleanSupplier;

import com.ctre.phoenix.motorcontrol.NeutralMode;
import com.ctre.phoenix.motorcontrol.TalonFXControlMode;
import com.ctre.phoenix.motorcontrol.can.WPI_TalonFX;
import com.ctre.phoenix.motorcontrol.StatorCurrentLimitConfiguration;

import edu.wpi.first.wpilibj.DigitalInput;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.SubsystemBase;

import frc.robot.Constants;
import frc.robot.staticConstants.HardwareMap;
import frc.robot.staticConstants.MaxMotorAmps;
```

**Key fixes:**
1. **Removed trailing space** after `package frc.robot.subsystems;`
2. **Fixed `TalonFXControlMode` import** - moved it before the `can.WPI_TalonFX` import to follow proper ordering
3. **Ensured proper grouping** - Java standard imports, then third-party (CTRE), then WPILib, then your project imports

**Common import issues to check:**
- Make sure the CTRE Phoenix library is in your `vendordeps` folder
- Verify your `Constants.java`, `HardwareMap.java`, and `MaxMotorAmps.java` files exist in the correct packages
- If using Phoenix 6 instead of Phoenix 5, the imports would be different (e.g., `com.ctre.phoenix6.*`)

If you're still having issues, let me know what error message you're getting and I can help troubleshoot further!

---
claude-conversations-hub fix-imports

## Tags
#claude-conversations-hub #fix #fix-imports
