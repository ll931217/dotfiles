#include <spawn.h>

void hideurltip(void);

static inline void restoremousecursor(void) {
	hideurltip();
	if (!(win.mode & MODE_MOUSE) && xw.pointerisvisible)
		XDefineCursor(xw.dpy, xw.win, xw.vpointer);
}
static void clearurl(void);
static void urlleave(XEvent *);
static void openUrlOnClick(int col, int row, char* url_opener);
