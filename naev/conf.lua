-- START GENERATED SECTION
-- The contents of this section will be rewritten by Naev!

-- The location of Naev's data pack, usually called 'ndata'
data = nil

-- The factor to use in Full-Scene Anti-Aliasing
-- Anything lower than 2 will simply disable FSAA
fsaa = 1

-- Synchronize framebuffer updates with the vertical blanking interval
vsync = false

-- Use OpenGL Vertex Buffer Objects extensions
vbo = false

-- Use OpenGL MipMaps
mipmaps = false

-- Use OpenGL Texture Compression
compress = false

-- Use OpenGL Texture Interpolation
interpolate = true

-- Use OpenGL Non-"Power of Two" textures if available
-- Lowers memory usage by a lot, but may cause slow downs on some systems
npot = false

-- If true enables engine glow
engineglow = true

-- The window size or screen resolution
-- Set both of these to 0 to make Naev try the desktop resolution
width = 1024
height = 768

-- Factor used to divide the above resolution with
-- This is used to lower the rendering resolution, and scale to the above
scalefactor = 1.000000

-- Run Naev in full-screen mode
fullscreen = false

-- Display a framerate counter
showfps = false

-- Limit the rendering framerate
maxfps = 200

-- Sound backend (can be "openal" or "sdlmix")
sound_backend = "openal"

-- Maxmimum number of simultaneous sounds to play, must be at least 16.
snd_voices = 128

-- Sets sound to be relative to pilot when camera is following a pilot instead of referenced to camera.
snd_pilotrel = true

-- Enables EFX extension for OpenAL backend.
al_efx = true

-- Size of the OpenAL music buffer (in kilobytes).
al_bufsize = 128

-- Disable all sound
nosound = false

-- Volume of sound effects and music, between 0.0 and 1.0
sound = 0.851852
music = 0.000000

-- The name or numeric index of the joystick to use
-- Setting this to nil disables the joystick support
joystick = nil

-- Whether or not to autorefuel
autorefuel = true

-- Number of lines visible in the comm window.
mesg_visible = 5

-- Delay in ms before starting to repeat (0 disables)
repeat_delay = 500
-- Delay in ms between repeats once it starts to repeat
repeat_freq = 30

-- Minimum and maximum zoom factor to use in-game
-- At 1.0, no sprites are scaled
-- zoom_far should be less then zoom_near
zoom_manual = false
zoom_far = 0.500000
zoom_near = 1.000000

-- Zooming speed in factor increments per second
zoom_speed = 0.250000

-- Zooming modulation factor for the starry background
zoom_stars = 1.000000

-- Font sizes (in pixels) for NAEV
-- Warning, setting to other than the default can cause visual glitches!
-- Console default: 10
font_size_console = 10
-- Intro default: 18
font_size_intro = 18
-- Default size: 12
font_size_def = 12
-- Small size: 10
font_size_small = 10

-- Sets the velocity (px/s) to compress up to when time compression is enabled.
compression_velocity = 5000.000000

-- Sets the multiplier to compress up to when time compression is enabled.
compression_mult = 200.000000

-- Enables compression on savegames
save_compress = true

-- Afterburner sensitivity
afterburn_sensitivity = 250

-- Mouse-flying thrust control
mouse_thrust = 1

-- Condition under which the autonav aborts.
autonav_abort = 0.500000

-- Enables developer mode (universe editor and teh likes)
devmode = 0

-- Save the config everytime game exits (rewriting this bit)
conf_nosave = 0

-- Enables FPU exceptions - only works on DEBUG builds
fpu_except = false


-- Keybindings

-- Makes your ship accelerate forward.
accel = { type = "keyboard", mod = "any", key = "up" }
-- Makes your ship turn left.
left = { type = "keyboard", mod = "any", key = "left" }
-- Makes your ship turn right.
right = { type = "keyboard", mod = "any", key = "right" }
-- Makes your ship face the direction you're moving from. Useful for braking.
reverse = { type = "keyboard", mod = "any", key = "down" }
-- Cycles through ship targets.
target_next = { type = "keyboard", mod = "none", key = "t" }
-- Cycles backwards through ship targets.
target_prev = { type = "keyboard", mod = "ctrl", key = "t" }
-- Targets the nearest non-disabled ship.
target_nearest = { type = "keyboard", mod = "none", key = "n" }
-- Cycles through hostile ship targets.
target_nextHostile = { type = "keyboard", mod = "ctrl", key = "r" }
-- Cycles backwards through hostile ship targets.
target_prevHostile = "none"
-- Targets the nearest hostile ship.
target_hostile = { type = "keyboard", mod = "none", key = "r" }
-- Clears the currently-targeted ship, planet or jump point.
target_clear = { type = "keyboard", mod = "any", key = "backspace" }
-- Fires primary weapons.
primary = { type = "keyboard", mod = "any", key = "space" }
-- Faces the targeted ship if one is targeted, otherwise faces targeted planet or jump point.
face = { type = "keyboard", mod = "any", key = "a" }
-- Attempts to board the targeted ship.
board = { type = "keyboard", mod = "none", key = "b" }
-- Fires secondary weapons.
secondary = { type = "keyboard", mod = "any", key = "left shift" }
-- Activates weapon set 1.
weapset1 = { type = "keyboard", mod = "any", key = "1" }
-- Activates weapon set 2.
weapset2 = { type = "keyboard", mod = "any", key = "2" }
-- Activates weapon set 3.
weapset3 = { type = "keyboard", mod = "any", key = "3" }
-- Activates weapon set 4.
weapset4 = { type = "keyboard", mod = "any", key = "4" }
-- Activates weapon set 5.
weapset5 = { type = "keyboard", mod = "any", key = "5" }
-- Activates weapon set 6.
weapset6 = { type = "keyboard", mod = "any", key = "6" }
-- Activates weapon set 7.
weapset7 = { type = "keyboard", mod = "any", key = "7" }
-- Activates weapon set 8.
weapset8 = { type = "keyboard", mod = "any", key = "8" }
-- Activates weapon set 9.
weapset9 = { type = "keyboard", mod = "any", key = "9" }
-- Activates weapon set 0.
weapset0 = { type = "keyboard", mod = "any", key = "0" }
-- Cycles through your escorts.
e_targetNext = { type = "keyboard", mod = "none", key = "e" }
-- Cycles backwards through your escorts.
e_targetPrev = { type = "keyboard", mod = "ctrl", key = "e" }
-- Orders escorts to attack your target.
e_attack = { type = "keyboard", mod = "any", key = "f" }
-- Orders escorts to hold their positions.
e_hold = { type = "keyboard", mod = "any", key = "g" }
-- Orders escorts to return to your ship hangars.
e_return = { type = "keyboard", mod = "ctrl", key = "c" }
-- Clears your escorts of commands.
e_clear = { type = "keyboard", mod = "none", key = "c" }
-- Initializes the autonavigation system.
autonav = { type = "keyboard", mod = "ctrl", key = "j" }
-- Cycles through planet targets.
target_planet = { type = "keyboard", mod = "none", key = "p" }
-- Attempts to land on the targeted planet or targets the nearest landable planet. Requests permission if necessary.
land = { type = "keyboard", mod = "none", key = "l" }
-- Cycles through jump points.
thyperspace = { type = "keyboard", mod = "none", key = "h" }
-- Opens the star map.
starmap = { type = "keyboard", mod = "none", key = "m" }
-- Attempts to jump via a jump point.
jump = { type = "keyboard", mod = "none", key = "j" }
-- Opens the in-system overlay map.
overlay = { type = "keyboard", mod = "any", key = "tab" }
-- Toggles mouse flying.
mousefly = { type = "keyboard", mod = "ctrl", key = "x" }
-- Engages active cooldown mode.
cooldown = { type = "keyboard", mod = "ctrl", key = "s" }
-- Scrolls the log upwards.
log_up = { type = "keyboard", mod = "any", key = "page up" }
-- Scrolls the log downwards.
log_down = { type = "keyboard", mod = "any", key = "page down" }
-- Attempts to initialize communication with the targeted ship.
hail = { type = "keyboard", mod = "none", key = "y" }
-- Automatically initialize communication with a ship that is hailing you.
autohail = { type = "keyboard", mod = "ctrl", key = "y" }
-- Zooms in on the radar.
mapzoomin = { type = "keyboard", mod = "any", key = "[+]" }
-- Zooms out on the radar.
mapzoomout = { type = "keyboard", mod = "any", key = "[-]" }
-- Takes a screenshot.
screenshot = { type = "keyboard", mod = "any", key = "[*]" }
-- Pauses the game.
pause = { type = "keyboard", mod = "any", key = "pause" }
-- Toggles 2x speed modifier.
speed = { type = "keyboard", mod = "any", key = "`" }
-- Opens the small in-game menu.
menu = { type = "keyboard", mod = "any", key = "escape" }
-- Opens the information menu.
info = { type = "keyboard", mod = "none", key = "i" }
-- Opens the Lua console.
console = { type = "keyboard", mod = "any", key = "f2" }
-- Switches to tab 1.
switchtab1 = { type = "keyboard", mod = "alt", key = "1" }
-- Switches to tab 2.
switchtab2 = { type = "keyboard", mod = "alt", key = "2" }
-- Switches to tab 3.
switchtab3 = { type = "keyboard", mod = "alt", key = "3" }
-- Switches to tab 4.
switchtab4 = { type = "keyboard", mod = "alt", key = "4" }
-- Switches to tab 5.
switchtab5 = { type = "keyboard", mod = "alt", key = "5" }
-- Switches to tab 6.
switchtab6 = { type = "keyboard", mod = "alt", key = "6" }
-- Switches to tab 7.
switchtab7 = { type = "keyboard", mod = "alt", key = "7" }
-- Switches to tab 8.
switchtab8 = { type = "keyboard", mod = "alt", key = "8" }
-- Switches to tab 9.
switchtab9 = { type = "keyboard", mod = "alt", key = "9" }
-- Switches to tab 0.
switchtab0 = { type = "keyboard", mod = "alt", key = "0" }

-- END GENERATED SECTION
