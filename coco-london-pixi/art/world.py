"""Where things are: one coordinate system for every asset (a 3840 x 2160 frame, 4K)."""
W, H = 3840, 2160
MARGIN = 200            # extra width on each side of wide layers, for parallax
WIDE = W + 2 * MARGIN   # width of the wide layers; x = 0 in a wide layer is -MARGIN on screen

HORIZON = 1150          # eye level: where receding lines meet
BANK_TOP = 1196         # top of the far embankment wall
WATER_TOP = 1222        # the far waterline
COPING = 1572           # top of the near balustrade
PAVE_TOP = 1652         # promenade pavement
KERB = 1770             # kerb line
ROAD_TOP = 1786
ROAD_BOTTOM = 1992
VP_X = W / 2            # the scene's vanishing point

# the sun: upper left and a little in front of the scene (matches paint.SUN)
