## **Logic Point A — Jumping & Vertical Movement**

This logic includes jumping, falling, variable jump height, wall sliding, and collision with platforms.

### **Boundary Cases**

| Boundary Input | Why It’s a Boundary |
| ----- | ----- |
| Very high fall speed | Tests how fast the player can fall and collisions |
| Jump button pressed when jump timer is 0 | Tests when you repeat the jump button over and over along with infinite jumping |
| Player moves above top of screen  | Tests ceiling boundaries and collisions |

### **Test Data**

| Boundary Input | Test Data Example |
| ----- | ----- |
| Very high fall speed | Player falls from a tall height until their velocity \> 15 |
| Jump with jump\_timer \= 0 | Player spams jump repeatedly while falling |
| Player above screen | Force player Y to \-50 during the well entry |

### **Expected Outcomes**

| Boundary Input | Expected Outcome |
| ----- | ----- |
| Very high fall speed | Player lands correctly and the collision works properly |
| Jump with zero timer | Player can’t jump in the air and the jump timer works correctly  |
| Player above screen | Player is clamped back into level; game does not soft-lock |

—----------------------------------------------------------------------------------------------------------------------------

## **Logic Point B — Attack Hitbox Creation**

This logic includes upper, lower, and side attacks and find the position of attack hitboxes.

### **Boundary Cases**

| Boundary Input | Why It’s a Boundary |
| ----- | ----- |
| Up attack close to ceiling | Hitbox may spawn outside area |
| Down attack while grounded | Should not work (down attack is air-only) |
| Side attack while touching a wall | Hitbox may spawn inside a solid wall |

### **Test Data**

| Boundary Input | Test Data Example |
| ----- | ----- |
| Up attack near ceiling | Player at top of map presses W \+ attack |
| Down attack on ground | Player stands still and presses S \+ attack |
| Side attack against wall | Player holds left against wall and attacks |

### **Expected Outcomes**

| Boundary Input | Expected Outcome |
| ----- | ----- |
| Up attack near ceiling | Hitbox doesn’t collide forcing the player to move |
| Down attack while grounded | Game automatically does a side attack |
| Side attack against wall | Hitbox appears in correct position and not inside wall |

---

## **Logic Point C — Platform Collision & Wall Sliding**

This logic handles horizontal collisions, platform edges, wall sliding, and world boundaries.

### **Boundary Cases**

| Boundary Input | Why It’s a Boundary |
| ----- | ----- |
| Player touches wall by 1 pixel | Tests the earliest trigger for wall sliding |
| Player moves exactly to screen edge | Tests wall clamping logic |
| Landing exactly on a platform's edge | Tests vertical collision and prevents falling through |

### **Test Data**

| Boundary Input | Test Data Example |
| ----- | ----- |
| 1-pixel wall contact | Move player slowly into wall one pixel per frame |
| Screen-edge clamp | Move player until x \= 0 or x \= SCREEN\_WIDTH |
| Platform edge landing | Jump so rect.right \== platform.rect.left |

### **Expected Outcomes**

| Boundary Input | Expected Outcome |
| ----- | ----- |
| 1-pixel wall contact | Player only wall-slides when actually touching wall |
| Screen-bound clamp | Player never exits the screen; no jitter |
| Platform edge landing | Player stands on platform and does not fall through |

---

## **Reflection**

The logic points that feels the most fragile is platform collision and wall sliding, because if you’re even one pixel off the player might clip into a wall or go through a platform. I’ll need to watch the collision updates so nothing collides wrong. The boundary case that surprised me was how easily the downward attack can break if the play is one pixel above the ground.  
