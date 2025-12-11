Testing Plan — 

1\. Overview  
This document outlines the structured testing plan for gameplay logic and other systems, including movement physics, attack hitbox creation, and collision handling. It also covers feature-level testing from user stories (difficulty settings, skip mechanics, and hint systems). Boundary and edge case testing is also included to show stability under extreme conditions. Finally, the plan identifies which tests are appropriate for automation based on repetition, rule-based logic, or high-volume input.  
\---

2\. User Stories and Acceptance Criteria

User Story 1: As a competitive player, I want to have a harder difficulty so that I can have a challenge  
\- Acceptance Criterion 1:  
    \- Requirement(s): Difficulty menu exists; difficulty value updates internally  
    \- Purpose: validate that difficulty can be switched reliably  
    \- Test Case:  
        a) Feature: Difficulty Settings  
        b) Test: Open Setting \-\> change difficulty to “hard” \-\> confirm  
        c) Expected Result / Behavior: UI updates to Hard; game stores difficulty  
        d) Automation Candidate: Yes (rule based menu interaction)

\- Acceptance Criterion 2  
    \- Requirement(s): Enemy stats scale based on difficulty level  
    \- Purpose: Ensure hard difficulty meaningfully changes gameplay  
    \- Test Case:  
        a) Feature: Enemy stat scaling  
        b) Test: Spawn enemy on normal \-\> record speed/attack; switch to hard \-\> compare  
        c) Expected Result / Behavior: Enemies have increased speed and higher damage  
        d) Automation Candidate: Yes (data comparison, deterministic checks

User Story 2: As a casual player, I want hard parts of the game to be optional so that I can enjoy that game without frustration.  
\- Acceptance Criterion 1:   
    \- Requirement(s): Skip button input recognized; skip-enabled zones exist  
    \- Purpose: Validate skip accessibility  
    \- Test Case:  
        a) Feature: Skip mechanic  
        b) Test: Player enters skip-enabled one \-\> pressed skip button  
        c) Expected Result / Behavior: Skip action triggers immediately  
        d) Automation Candidate: Yes (simple input \-\> state change) 

\- Acceptance Criterion 2   
    \- Requirement(s): Teleport location configured; trigger move player safely  
    \- Purpose: Ensure skip function reliably moves player  
    \- Setup: Player positioned in a skip-enabled challenge zone  
    \- Test Case:  
        a) Feature: Teleport logic  
        b) Test: Press skip \-? Check new player position  
        c) Expected Result / Behavior: Player appears past obstacle; no clipping or unintended deaths  
        d) Automation Candidate: Yes (position validation)

User Story 3: As a new player, I want to have tool tips/optional hints, so that I can have help if I get stuck  
\- Acceptance Criterion 1   
    \- Requirement(s): Hint setting toggle exists; hint button input recognized  
    \- Purpose: Validate that the player can enable hints and request one   
    \- Test Case:   
        a) Feature: Hint system toggle  
        b) Test: Enable hint mode in settings \-\> press hint button  
        c) Expected Result / Behavior: Game registers button press and attempts to show a hint  
        d) Automation Candidate: Yes (rule-based UI \+ input testing)

\- Acceptance Criterion 2   
    \- Requirement(s): Hint text exists; UI can display a hint  
    \- Purpose: Ensure hints appear correctly and guide the player forward  
    \- Setup: Player stand near a context-appropriate challenge  
    \- Test Case:  
        a) Feature:Hint displayer  
        b) Test: Press hint button while hints are enabled  
        c) Expected Result / Behavior: A readable hint appears on-screen and gives guidance  
        d) Automation Candidate: Partial (some UI checks my need visual confirmation)

\---

3\. Boundary and Edge Testing

Boundary / Edge 1:    
    \- Requirement(s): Jump physics, fall velocity cap, collision checks  
    \- Purpose: Ensure vertical movement behaves correctly at extremes

    \- Test Case 1: Upper Boundary – Very high fall speed  
        a) Upper Boundary: Player falling past max safe velocity  
        b) Testing data used: \<14, 15, 16\> (velocity thresholds)  
        c) Expected Result / Behavior: Player lands correctly; collision stable  
        d) Automation Candidate: Yes (physics simulation)

    \- Test Case 2: Lower Boundary – Jump with jump\_timer \= 0  
        a) Lower Boundary: Jump cannot occur with expired jump timer  
        b) Testing data used: \<0 \- 1, 0, 0 \+ 1\>  
        c) Expected Result / Behavior: No infinite or repeated jumps  
        d) Automation Candidate: Yes

Boundary / Edge 2: Logic Point B – Attack Hit box creation  
    \- Requirement(s): Hitbox spawn logic positions must respect boundaries  
    \- Purpose: Prevent invalid hitboxes or unintended collisions

    \- Test Case 1: Upper Boundary – Up attack near ceiling  
        a) Upper Boundary: Hitbox spawning close to ceiling  
        b) Testing data used: \<Y \= ceiling \+ 1, Y \= ceiling, Y \= ceiling \-   
        c) Expected Result / Behavior: Hitbox adjusts; does not spawn above ceiling  
        d) Automation Candidate: Yes

    \- Test Case 2: Lower Boundary — Down attack while grounded  
        a) Lower Boundary: Down attack should only work in-air  
        b) Testing data used: Grounded state \<1 pixel above, on ground, 1 pixel below\>  
        c) Expected Result / Behavior: Game replaces down attack → side attack  
        d) Automation Candidate: Yes (state machine test) 

Boundary / Edge 3: Logic Point C – Platform Collision & Wall sliding  
    \- Requirement(s): Horizontal/vertical collision accuracy; wall sliding triggers  
    \- Purpose: Ensure pixel-accurate and stable collisions

    \- Test Case 1: Upper Boundary — 1-pixel wall contact  
        a) Upper Boundary: Player touches wall by exactly 1 pixel  
        b) Testing data used: \<1 pixel away, touching, 1 pixel inside\>  
        c) Expected Result / Behavior: Wall slide triggers only at proper contact  
        d) Automation Candidate: Yes (pixel-step simulation) 

    \- Test Case 2: Lower Boundary – Screen-edge clamp  
        a) Lower Boundary: Player at extreme screen positions  
        b) Testing data used: \<x \= \-1, 0, 1\> and \<SCREEN\_WIDTH \-1, SCREEN\_WIDTH, SCREEN\_WIDTH \+1\>  
        c) Expected Result / Behavior: Player never leaves screen; no jitter  
        d) Automation Candidate: yes

\---

4\. Automated Test List  
Repetitive (UI toggles, state changes)  
\-Difficulty menu switching  
\-Hint system toggle  
\-Skip button activation  
\-Jump timer reset verification

Rule-Based (deterministic physics or logic)  
\-Enemy stat scaling on Hard difficulty  
\-Hitbox spawn validation (up, down, side attacks)  
\-Down-attack conversion to side-attack on ground  
\-1-pixel wall slide trigger logic  
\-Platform edge landing detection

High-Volume (physics sweeps, edge scanning)  
\-Vertical fall-speed stress test  
\-Pixel-by-pixel movement near walls  
\-Screen-edge clamping checks  
\-Multiple hint outputs in various levels

