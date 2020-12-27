# Impact Puzzle Generator

This is a semi-automatic glass impact jigsaw puzzle generator. It tries to simulate a projectile impact to a piece of glass, generating the characteristic ring and radial fracture pattern, and adding tabs to the resulting pieces. The resulting jigsaw can be exported to SVG for laser-cutting in clear acrylic.

## How it works

The algoritm generates a series of  jagged, skewed, concentric point rings . A point ring is a circular ring of points (angular divisions), i.e, a circle approximation. Expressed in polar coordinates, each point has the same radius, and the points are angularly equaly spaced, covering the full 360 degrees of a circle, dividing it in equal sectors. A jagged ring is when you add random variations to the radius and angle of these points. The ring gets skewed if the radius and radial jitter is greater in a specific angular direction.

Each ring tries to loosely track the previous ring, staying within a distance range of it. The target separation between rings increases exponentially. After the rings are generated, they are joined by procedurally generated tabs, which may be omitted randomly. Tabs can be jagged, with a trapezoidal protrusion that connects and interlocks it to the neighboring piece, of fracture tabs, which are jittery paths between points and don't usally interlock pieces together.

### Drawing Mode

You are presented with an adjustable rectangular frame, representing your piece of glass. You may press wherever you want within the drawing canvas (even outside the frame), and drag your mouse while pressing.  The impact point will be the point where you clicked the mouse. While you drag the mouse, a red arrow will be displayed, representing the "impact" direction. The longer the arrow, the more the impact will be skewed towards the pointing direction (i.e. separation between rings gets larger in that direction). When you release the mouse, the impact will be randomly generated.
You may configure several parameters for the impact generation. The allowed range for some settings exceed the practical and even sane limits, so beware. I decided not to limit the ranges too much to allow for "artistic" and weird puzzles, even when they aren't manufacturable.

#### Impact shape settings

* **Impact radius**: the target projectile radius in mm, unless you have loaded a custom projectile
* **Final radius**: the target whole impact radius in mm. It's actually a measure of how much the impact "expands". The actual size of the impact depends on many other things and it's difficult to predict.
* **Minimum first ring crown**: the target radial separation between the first and second ring, in mm. Succesive radial distances between rings increment exponentially. This fixes the smallest piece height, to avoid too small pieces.
* **Number of rings**: the target number of impact rings. Depending on many other things, some of them may be cropped by the frame or deleted if they fall completely outside the frame.
* **Number of angluar divisions**: the target number ring angular divisions. Depending on many other things, some of them may be cropped by the frame or deleted if they fall completely outside the frame.
* **Initial/Final ring radius jitter**: radial jitter applied to the radius of the ring points. Relative to the nominal distance. Determines how radially "jagged" the rings get. The jitter applied to each ring increments (or decrements) exponentially from the initial to the final value for each succesive ring.
* **Initial/Final ring angle jitter**: radial jitter applied to the angle of the ring points. Relative to the nominal distance. The jitter applied to each ring increments (or decrements) exponentially from the initial to the final value for each succesive ring.

#### Probability settings

* **Probability of no radial segment (%)**: probability of radial segment omision during generation. 
* **Probability of no ringsegment (%)**: probability of ring segment omision during generation. 
* **Probability of tab not jagged (%)**: probability of having a fracture tab instead of a jagged tab between two ring points.
* **Probability of tab from library (%)**: probability of using a custom tab from the library instead of a jagged or fracture tab, if a tab library is loaded.
#### Tab settings

These settings apply to jagged tabs only, except for segment jitter which is also used for fracture tab generation

* **Relative tab top/bottom length**: target length of the top side/bottom gap of the tab, relative to its span length.
* **Relative tab depth**: target tab protrusion depth, relative to its span length.
* **Tab segment/angle jitter: random** jitter applied to segment length and angle between segments during tab procedural generation

There is a tab preview area where the current "nominal"  tab is shown in black, along with several random tabs generated from the current settings in gray, so you can see the a sample of the possible tabs that will be generated.

### Edit Mode

The edition mode lets you manually adjust the puzzle to correct generation issues or modify its shape. You may zoom the puzzle using the mouse wheel, and pan around by dragging while pressing the right mouse button.
The error checker finds places where tabs are intersecting or too close together, and pieces which aren't properly supported, which don't have enough jagged tabs to properly lock them within the jigsaw. The automatic issue fixer leaves a lot to be desired, but fixes some common issues automatically. The rest have to be fixed manually.
You may select tabs by clicking over them, and delete, flip or switch them to be jagged or fracture. Tab replacement takes the current tab settings.
You may also modify the jigsaw shape by clicking on the blue connecting dots to pick a point, and clicking again somewhere else to move it to the new position. New tabs will be generated to connect the new point to its neighbours. Right clicking deselcts the point and terminates the edition.

## Custom Projectiles
There's a crude projectile editor that lets you create your own custom projectiles to launch at the glass. You may open the editor via the button in the right panel. Then, you can start drawing your projectile. A left click in the canvas creates a new contour point. A right click deletes the last point (undo functionality). When you're finished, a final double-click with the left button closes the shape and finishes the projectile. Its centroid will be calculated and then you can save the projectile (.pro files) for later use.

If you want to break the glass using a custom projectile, you may do so by setting Drawing Mode, pressing the "Load projectile" button and choosing any .pro projectile file. You may scale the projectile before impact with the mouse wheel, and turn it using Q and E keys. Once you're satisfied, click and drag as usual to create the impact, which will roughly take the shape of the projectile.

If you want to go back to normal drawing mode, without a custom projectile, press the "Load projectile" button again and then "Cancel" in the file selection dialog.

Beware that custom projectile impact functionality isn't well polished. It won't work well with concave projectile shapes or high aspect ratio shapes (i.e. much larger in one dimension than in the other, for example a stick or a banana). I may improve it someday.

## Custom Tabs
There's a tab editor that lets you create your own custom tab shapes. Tabs are saved as ".tab" files. Place all of your custom tabs in a folder. You may then load your tab library via the "Load tab library" button, so that your custom tabs are used while generating the impact. A selectable percentage of tabs will be chosen randomly from your library. This feature is still experimental and has some bugs. I plan to improve on it.

## Limitations and quirks

### Code quality

* This is my first ever python app, I come from C. I've tried to be as pythonic as possible but don't expect too much. It's mostly made to work and be usable
* Also, the software architecture and code style aren't that great, and I learned python on the way. I'll fix it someday (TM)...

### Interface

* You need at least a Full-HD (1920x1080 pixel)  screen to run this properly. The interface doesn't autoresize automatically.
* It's a quite CPU-intensive. A 4th generation laptop Core i7 moves it fluidly below about 2000 tabs or 500 pieces, and remains usable until about 2000 pieces. In any case, 2000 piece clear puzzles aren't probably practical anyway
* It should work in Linux and MacOS, but it has only been tested in Windows 10.
* Everythin is expressed in millimeters only.
* The color coding for tab errors is weird.

### Algorithm

* All rings have the same angular divisions, and this is architectural. Play with jitter values in order to break the "spiderweb" look and feel. With the proper settings, the pieces "naturally" acquire multiple shapes

## Feature roadmap

* WIP:  Support for custom drawn tabs from a tab library, to increase variability

