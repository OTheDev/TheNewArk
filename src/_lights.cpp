///////////////////////////////////////////////////////////////////////////////
//  The compiled version of the code in this file is uploaded onto the Teensy
//  4.0. It is responsible for controlling the LEDs for TheNewArk.
//
//  Strips:
//                      Strip 1: panels 1-2; 16 LEDs.
//                      Strip 2: panels 3-4; 16 LEDs.
//                      Strip 3: panels 5-6; 16 LEDs.
//                      Strip 4: panels 7-8; 16 LEDs.
//                      Strip 5: panels 9-10; 16 LEDs.
//                      Strip 6: panel 11; 8 LEDs.
//
//  Panels: intervals represent addresses; panel 11 is on top of the Ark.
//          Each panel consists of 8 LEDs.
//
//                               P11 [80,87]
//
//                      P9 [64,71] P8 [56,63] P7 [48,55]
//      P10 [72,79]                                          P6 [40,47]
//      P1  [0,7]                                            P5 [32,39]
//                      P2 [8,15]  P3 [16,23] P4 [24,31]
//
//  Upload: Using the Arduino/Teensyduino GUI, ensure that "Teensy 4.0" is
//          selected on the "Tools -> Board" menu. The correct item also needs
//          to be selected on the "Tools -> Port" menu, which will be
//          OS-dependent. Once the correct board and serial port are selected,
//          we can compile and load the binary file onto the configured board
//          through the configured port using "Upload". Make sure all hardware
//          components are connected prior. Clicking "Verify/Compile" checks
//          the code for errors in compiling it. Clicking "Upload" compiles
//          and loads the binary file onto the configured board through the
//          configured port.
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
//  Includes
///////////////////////////////////////////////////////////////////////////////
#include <math.h>    /* double log2(double x);
                        double pow(double x, double y); */
#include <stdint.h>  /* uintN_t */
#include <stdlib.h>  /* void srand(unsigned int seed);
                        int rand(void); rand() generates a pseudo-random
                        integer in [0, RAND_MAX]. */
#include <OctoWS2811.h>
#include <SoftwareSerial.h>


///////////////////////////////////////////////////////////////////////////////
//  Hardware-related constants: For the `group_*` multidimensional arrays,
//                              please also refer to the panel locations above.
//                                  "Front"      : P1, P10;
//                                  "Right-left" : P2, half of P3;
//                                  "Right-right": P4, half of P3;
//                                  "Left-left"  : P7, half of P8;
//                                  "Left-right" : P9, half of P8;
//                                  "Back"       : P5, P6;
//                                  "Top"        : P11.
///////////////////////////////////////////////////////////////////////////////
#define N_LEDS_PER_STRIP 16   /* Maximum number of LEDs on a strip. */
#define N_STRIPS          6   /* Number of strips. */
#define N_PANELS         11   /* Number of panels. */
#define N_LEDS_PER_PANEL  8   /* Number of LEDs per panel. */
#define N_LEDS           88   /* Number of LEDs (bulbs). */

/* Front */
const uint8_t group_f[4][4] = {
    {72, 73, 74, 75},
    {76, 77, 78, 79},
    {0, 1, 2, 3},
    {4, 5, 6, 7}
};

/* Right-left */
const uint8_t group_rl[3][4] = {
    {8, 9, 10, 11},
    {12, 13, 14, 15},
    {16, 17, 18, 19}
};

/* Right-right */
const uint8_t group_rr[3][4] = {
    {20, 21, 22, 23},
    {24, 25, 26, 27},
    {28, 29, 30, 31}
};

/* Back */
const uint8_t group_b[4][4] = {
    {32, 33, 34, 35},
    {36, 37, 38, 39},
    {40, 41, 42, 43},
    {44, 45, 46, 47}
};

/* Left-left */
const uint8_t group_ll[3][4] = {
    {48, 49, 50, 51},
    {52, 53, 54, 55},
    {56, 57, 58, 59}
};

/* Left-right */
const uint8_t group_lr[3][4] = {
    {60, 61, 62, 63},
    {64, 65, 66, 67},
    {68, 69, 70, 71}
};


///////////////////////////////////////////////////////////////////////////////
//  Color-related constants
///////////////////////////////////////////////////////////////////////////////
#define BLACK 0x000000

/* Declare a structure tag named `color`. */
struct color {
    uint8_t r;
    uint8_t g;
    uint8_t b;
};

/*  The following mapping is based on Scriabin's "sound-to-color synesthesia"
    mapping (see the Wikipedia page on Chromesthesia). In truth, the
    association between sound and color is highly idiosyncratic amongst
    sound-to-color synesthetes.  */
const uint32_t map_cs_to_color[] = {
    0xFF0000,   // C    "RED";
    0xCE9AFF,   // Db   "Violet"
    0xFFFF00,   // D    "Yellow"
    0x656599,   // Eb   "Steel color with metallic sheen"
    0xE3FBFF,   // E    "Whitish-blue"
    0xAC1C00,   // F    "Red, dark"
    0x00CCFF,   // Gb   "Blue, bright"
    0xFF6500,   // G    "Orange-pink"
    0xFF00FF,   // Ab   "Purplish-violet"
    0x33CC33,   // A    "Green"
    0x8C8A8C,   // Bb   "Similar to Eb"
    0x0000FE    // B    "Similar to E"
};


///////////////////////////////////////////////////////////////////////////////
//  Drone-related constants
///////////////////////////////////////////////////////////////////////////////
#define DRONE_BRIGHTNESS_N           100
#define DRONE_MICROSEC_UP        3350000
#define DRONE_MICROSEC_DOWN      1450000
#define DRONE_MICROSEC_ITERATION 4800000

_Static_assert((DRONE_MICROSEC_UP + DRONE_MICROSEC_DOWN) ==
                DRONE_MICROSEC_ITERATION, "Invalid drone times.");

static uint32_t drone_delay_up = DRONE_MICROSEC_UP / DRONE_BRIGHTNESS_N;
static uint32_t drone_delay_down = DRONE_MICROSEC_DOWN / DRONE_BRIGHTNESS_N;

struct color drone_color = {255, 0, 0};
static struct color *drone_brightness;


///////////////////////////////////////////////////////////////////////////////
//  OctoWS2811 setup. http://www.pjrc.com/teensy/td_libs_OctoWS2811.html.
///////////////////////////////////////////////////////////////////////////////
const int config = WS2811_RGB | WS2811_800kHz;

DMAMEM int displayMemory[N_LEDS_PER_STRIP * 6];
int drawingMemory[N_LEDS_PER_STRIP * 6];

OctoWS2811 leds(N_LEDS_PER_STRIP, displayMemory, drawingMemory, config);


///////////////////////////////////////////////////////////////////////////////
//  Parser. The Python program sends USB-serial messages to the program
//          uploaded on the microcontroller. By construction, every message
//          consists of 11 bytes, starting with the character '%' and ending
//          with the character '&':
//              message[0] == '%'
//              message[1] == either '0', '1', or '2'
//                  '0' ==> "drone off" message
//                  '1' ==> "drone on" message
//                  '2' ==> "note" message
//              message[2] == integer 0 (<==> '\0'), 1, ... , or 11
//              message[3] == either '0', '1', ... , '9', or '\0'
//              message[4] == either '0', '1', ... , '9', or '\0'
//              ...
//              message[9] == either '0', '1', ... , '9', or '\0'
//              message[10] == '&'
//
//          In a "drone on" and "drone off" message, the eight characters
//          from message[2] to message[9] are set to the null character '\0':
//              "drone on" message  <==> "%1\0\0\0\0\0\0\0\0&"
//              "drone off" message <==> "%0\0\0\0\0\0\0\0\0&"
//
//          In a "note" message, message[2] is an integer in [0, 11] giving
//          the octave-independent note number (C corresponds to 0, Db to 1,
//          and so on). message[3] through till message[9] are a string of
//          character digits encoding how long lights corresponding to a
//          an arbitrary note number should be lit.
//
//          The Python program sets a timeout of 0, which means that an
//          attempt will be made to ask the OS to write the full message
//          through the serial port but it is possible that the call fails to
//          write the full message. Because the timeout is set to 0, the
//          Python program does not attempt to write the rest of the message.
//          The return value of the OS call the Python program makes ends up
//          being the number of bytes actually written. The Python program
//          can therefore detect in advance whether or not the write was
//          fully successful. If it was not fully successful, the Python
//          program will restart the computer (==> restarting the micro-contr.
//          as well).
//
//          The Python program expects a one-byte response from the
//          microcontroller for every message. If it does not receive a
//          response, the Python program will restart the computer.
//
//          In other words, if communication between the Python program and the
//          microcontroller is ever not as expected, the computer restarts.
//          However, the Python program has never had to restart the computer.
///////////////////////////////////////////////////////////////////////////////
int
parse(void)
{
    int idx = 0;
    char buf[11] = {0};
    char *temp;

    /* Receive entire message into `buf`. */
    while (idx < 11 && Serial.available() > 0 && buf[idx] != '&')
        buf[idx++] = Serial.read();

    /* Flush */
    while (Serial.available() > 0)
        Serial.read();

    /* Check if message is as expected. */
    if (buf[0] == '%' && buf[10] == '&')
    {
        if (buf[1] == '0')
        {
            Serial.write("1");
            Serial.send_now();
            /* "drone off" message */
            all_lights_off();
        }
        else if (buf[1] == '1')
        {
            Serial.write("1");
            Serial.send_now();
            /* "drone on" message */
            drone_lights();
        }
        else if (buf[1] == '2')
        {
            /* "note" message */
            uint8_t note = buf[2];
            uint32_t duration = (uint32_t) strtoull(&buf[3], &temp, 10);

            if (*temp == '\0' || *temp == '&')
            {
                Serial.write("1");
                Serial.send_now();
                randomize_half_panels(map_cs_to_color[note], duration);
            }
            else
            {
                return 0;
            }
        }
        else
        {
            return 0;
        }

        return 1;
    }
    else
    {
        return 0;
    }
}


///////////////////////////////////////////////////////////////////////////////
//  Setup
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  setup: The setup() function will only run once, after each powerup or
 *         reset of the Arduino board. Use it to initialize variables,
 *         pin modes, start using libraries, etc. Called when a sketch
 *         starts.
 *****************************************************************************/
void 
setup() 
{
    /* Sets the speed (baud rate) for the serial communication. Strictly
       speaking, with Teensy, this is a no-op. */
    Serial.begin(57600);
    /* Initialize the OctoWS2811 library. */
    leds.begin();
    /* Initiates an update of the LEDs. */
    leds.show();

    _init_TheNewArk();
}


/*****************************************************************************
 *  _init_TheNewArk: Initialization code pertaining to the TheNewArk project.
 *
 *             Note: This must be called in `setup()`.
 *****************************************************************************/
void
_init_TheNewArk(void)
{
    /* Initialize random number generator. */
    srand(42);  // srand((unsigned) time(NULL));
    /* Initialize an array of brightness levels for the drone. It should be
       noted that free() is not actually called in this program on
       `drone_brightness`. It will be deallocated automatically after the
       Teensy resets due to power off and on. In retrospect, this should have
       simply been a static array. */
    drone_brightness = _create_quadratic_brightness(&drone_color,
                                                    DRONE_BRIGHTNESS_N);
    if (drone_brightness == NULL)
    {
        abort();
    }
}


///////////////////////////////////////////////////////////////////////////////
//  Loop
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  loop: This function loops consecutively.
 *****************************************************************************/
void
loop()
{
    if (Serial.available() > 0)
    {
        parse();
    }
}


///////////////////////////////////////////////////////////////////////////////
//  Drone On
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  drone_lights: The "50 bpm drone" is used. Paddy estimates that the
 *                "50 bpm drone" peaks at 3.248 seconds and ends at 4.800
 *                seconds. The "30 bpm drone" peaks at 2.730 seconds and
 *                ends at 4.000 seconds. (3350000, 1450000) may also be good.
 *
 *                Given an interval [a, b], a < b, to divide the interval
 *                into `n` equal parts, the parts must have length
 *                L = (b - a) / n.
 *****************************************************************************/
void
drone_lights(void)
{
    int i;
    uint8_t off = 0;

    /* Edge case: end right away */
    if (Serial.available() > 0)
    {
        return;
    }

    while (1)
    {
        /* Increase brightness quadratically with time over `_MICROSEC_UP`
           microseconds. */
        for (i = 0; i < DRONE_BRIGHTNESS_N; i++)
        {
            if (Serial.available() > 0 && off == 0)
            {
                off = 1;
            }
            all_lights_RGB(drone_brightness[i].r, 0, 0, drone_delay_up);
        }
        /* Decrease brightness over the same curve over ` _MICROSEC_DOWN`
           microseconds. */
        for (i = DRONE_BRIGHTNESS_N - 1; i >= 0; i--)
        {
            if (Serial.available() > 0 && off == 0)
            {
                off = 1;
            }
            all_lights_RGB(drone_brightness[i].r, 0, 0, drone_delay_down);
        }
        if (off)
        {
            return;
        }
    }
}


///////////////////////////////////////////////////////////////////////////////
//  Note On
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  randomize_half_panels: The 11 panels are divided into 7 groups. Each of
 *                         the 7 groups are themselves divided into 2-4
 *                         groups of 4 LEDs.
 *
 *                         The 7 groups:
 *                              "Front"      : P1, P10.
 *                              "Back"       : P5, P6.
 *                              "Left-left"  : P7, half of P8.
 *                              "Left-right" : P9, half of P8.
 *                              "Right-left" : P2, half of P3.
 *                              "Right-right": P4, half of P3.
 *                              "Top"        : P11.
 *
 *                         Within 6 out of the 7 groups (all except "Top"), one
 *                         group of 4 LEDs is selected at random and lit.
 *
 *                         For "Top", the probability that exactly one group
 *                         of four is lit is 50%; the other 50% of the time,
 *                         no group of four is lit.
 *****************************************************************************/
void
randomize_half_panels(uint32_t color, uint32_t microsec_delay)
{
    /* Loop variable */
    int j;

    /* Choose which group of 4 is selected in each group except "Top" */
    int f  = rand() % 4, b  = rand() % 4;
    int ll = rand() % 3, lr = rand() % 3;
    int rl = rand() % 3, rr = rand() % 3;

    /* Randomize number per subgroup */
    int n_f  = 1 + rand() % 4, n_b  = 1 + rand() % 4;
    int n_ll = 1 + rand() % 4, n_lr = 1 + rand() % 4;
    int n_rl = 1 + rand() % 4, n_rr = 1 + rand() % 4;

    /* "Top" group handled separately */
    if (rand() % 2) {
        int t_base = (rand() % 2) ? 80 : 84;
        int n_t = 1 + rand() % 4;

        for (j = 0; j < n_t; j++) {
            leds.setPixel(t_base + j, color);
        }
    }

    /* Probably should be rewritten but this should suffice */
    for (j = 0; j < n_f; j++)
        leds.setPixel(group_f[f][j], color);
    for (j = 0; j < n_b; j++)
        leds.setPixel(group_b[b][j], color);
    for (j = 0; j < n_ll; j++)
        leds.setPixel(group_ll[ll][j], color);
    for (j = 0; j < n_lr; j++)
        leds.setPixel(group_lr[lr][j], color);
    for (j = 0; j < n_rl; j++)
        leds.setPixel(group_rl[rl][j], color);
    for (j = 0; j < n_rr; j++)
        leds.setPixel(group_rr[rr][j], color);

    leds.show();
    delayMicroseconds(microsec_delay);
    all_lights_off();
}


///////////////////////////////////////////////////////////////////////////////
//  Brightness functions: Suppose there is a 'target' or 'maximum' RGB color
//                        (R, G, B) such that 0 <= R, G, B <= 255. Consider
//                        multiplying the components of the target color by a
//                        factor x in [0, 1] such that the color is
//                        (xR, xG, xB).
//
//                        "Increasing brightness" amounts to increasing x.
//
//                        Since RGB components are integers, we drop any
//                        fractional part to the brightness calculations.
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  _create_linear_brightness: Given the color pointed to be `col`, say,
 *                             (R, G, B), returns a dynamically allocated
 *                             array of colors representing `n` brightness
 *                             levels
 *
 *                                  (x(t)R, x(t)G, x(t)B)
 *
 *                             where x(t) = t / n for t = 1, 2, ..., n.
 *
 *                             Brightness increases linearly with time.
 *
 *                             If the space cannot be allocated, NULL is
 *                             returned.
 *****************************************************************************/
struct color *
_create_linear_brightness(struct color *col, size_t n)
{
    struct color *ret;

    ret = (struct color *) malloc(n * sizeof(struct color));
    if (ret == NULL)
    {
        return NULL;
    }

    for (size_t i = 0; i < n; i++)
    {
        double tmp = (double) (i + 1) / (double) n;
        ret[i].r = (col->r) * tmp;
        ret[i].g = (col->g) * tmp;
        ret[i].b = (col->b) * tmp;
    }

    return ret;
}


/*****************************************************************************
 *  _create_quadratic_brightness: Given the color pointed to be `col`, say,
 *                                (R, G, B), returns a dynamically allocated
 *                                array of colors representing `n` brightness
 *                                levels
 *
 *                                  (x(t)R, x(t)G, x(t)B),
 *
 *                                   x(t) = (t / n)**2 for t = 1, 2, ..., n.
 *
 *                                Brightness increases quadratically with
 *                                time.
 *
 *                                If the space cannot be allocated, NULL
 *                                is returned.
 *****************************************************************************/
struct color *
_create_quadratic_brightness(struct color *col, size_t n)
{
    struct color *ret;

    ret = (struct color *) malloc(n * sizeof(struct color));
    if (ret == NULL)
    {
        return NULL;
    }

    for (size_t i = 0; i < n; i++)
    {
        double tmp = (double) (i + 1) / (double) n;
        double tmp_sq = tmp * tmp;

        ret[i].r = (col->r) * tmp_sq;
        ret[i].g = (col->g) * tmp_sq;
        ret[i].b = (col->b) * tmp_sq;
    }

    return ret;
}


/*****************************************************************************
 *  create_quadratic_brightness: See notes to `_create_quadratic_brightness`.
 *                               This is a more general version.
 *                Example usage:
 *                               struct color min_col = {0, 0, 0};
 *                               struct color max_col = {174, 21, 44};
 *                               drone_brightness =
 *                               create_quadratic_brightness(&min_col,
 *                               &max_col, DRONE_BRIGHTNESS_N);
 *****************************************************************************/
struct color *
create_quadratic_brightness(struct color *min, struct color *max, size_t n)
{
    struct color *ret;

    ret = (struct color *) malloc(n * sizeof(struct color));
    if (ret == NULL)
    {
        return NULL;
    }

    for (size_t i = 0; i < n; i++)
    {
        double tmp = (double) (i + 1) / (double) n;
        double tmp_sq = tmp * tmp;

        ret[i].r = (max->r - min->r) * tmp_sq + (min->r);
        ret[i].g = (max->g - min->g) * tmp_sq + (min->g);
        ret[i].b = (max->b - min->b) * tmp_sq + (min->b);
    }

    return ret;
}


/*****************************************************************************
 *  _create_exponential_brightness: Given a color pointed to by `col`, say,
 *                                  (R, G, B), returns a dynamically allocated
 *                                  array of colors representing `n` brightness
 *                                  levels.
 *
 *                                  Brightness increases exponentially with
 *                                  time.
 *
 *                                  If the space cannot be allocated, NULL
 *                                  is returned.
 *
 *                 Technical notes: Let b > 0 a real number. By definition of
 *                                  log,
 *
 *                                      y = log_{b}x <==> x = b^{y}.
 *
 *                                  Suppose we want a sequence of n integer
 *                                  values of x between (0, max]. (Ideally,
 *                                  a float/double would be used for x for
 *                                  more precision, but RGB components are
 *                                  integers in [0, 255].)
 *
 *                                  The maximum exponent e_max is log_{b}max.
 *                                  Let
 *
 *                                      x = b^{e_max * (e / n)},
 *                                      e = 1, 2, ..., n.
 *
 *                                  This function makes use of the integer
 *                                  part of x.
 *****************************************************************************/
struct color *
_create_exponential_brightness(struct color *col, size_t n)
{
    struct color *ret;
    double max_e_r = log2(col->r);
    double max_e_g = log2(col->g);
    double max_e_b = log2(col->b);

    ret = (struct color *) malloc(n * sizeof(struct color));
    if (ret == NULL)
    {
        return NULL;
    }

    for (size_t i = 0; i < n; i++)
    {
        double tmp = (double) (i + 1) / (double) n;

        ret[i].r = pow(2, max_e_r * tmp);
        ret[i].g = pow(2, max_e_g * tmp);
        ret[i].b = pow(2, max_e_b * tmp);
    }

    return ret;
}


///////////////////////////////////////////////////////////////////////////////
//  Other Helpers
///////////////////////////////////////////////////////////////////////////////
/*****************************************************************************
 *  all_lights_off: Turns off all LEDs.
 *****************************************************************************/
void
all_lights_off(void)
{
    for (size_t i = 0; i < N_LEDS; i++) {
        leds.setPixel(i, BLACK);
    }
    leds.show();
}


/*****************************************************************************
 *  all_lights_RGB: Turns on all LEDs with color
 *                  (R, G, B) = (`red`, `green`, `blue`) for time
 *                  `microsec_delay`. Does not turn off the lights.
 *****************************************************************************/
void
all_lights_RGB(uint8_t red, uint8_t green, uint8_t blue,
               uint32_t microsec_delay)
{
    for (size_t i = 0; i < N_LEDS; i++) {
        leds.setPixel(i, red, green, blue);
    }
    leds.show();
    delayMicroseconds(microsec_delay);
}
