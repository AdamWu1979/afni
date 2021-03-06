/* config.h.  Generated automatically by configure.  */
/* config.h.in.  Generated automatically from configure.in by autoheader.  */
/* Process this file with autoheader to produce config.h.in */
#ifndef CONFIG_H
#define CONFIG_H

/* Package and version. */
#define PACKAGE "gifsicle"
#define VERSION "1.25"

/* Define when using the debugging malloc library. */
/* #undef DMALLOC */

/* Define to a function that returns a random number. */
#define RANDOM random

/* Define to the number of arguments to gettimeofday. (gifview only) */
#define GETTIMEOFDAY_PROTO 2

/* Get the [u_]int*_t typedefs. */
#define NEED_SYS_TYPES_H 1
#ifdef NEED_SYS_TYPES_H
# include <sys/types.h>
#endif
/* #undef u_int16_t */
/* #undef u_int32_t */
/* #undef int32_t */

/* Pathname separator character ('/' on Unix). */
#define PATHNAME_SEPARATOR '/'

/* Define this to write GIFs to stdout even when stdout is a terminal. */
/* #undef OUTPUT_GIF_TO_TERMINAL */

/* Define if GIF LZW compression is off. */
/* #undef GIF_UNGIF */


/* Define to empty if the keyword does not work.  */
/* #undef const */

/* Define as __inline if that's what the C compiler calls it.  */
/* #undef inline */

/* Define if the X Window System is missing or not being used.  */
/* #undef X_DISPLAY_MISSING */

/* Define if you have the strerror function.  */
#define HAVE_STRERROR 1

/* Define if you have the strtoul function.  */
#define HAVE_STRTOUL 1

/* Define if you have the <sys/select.h> header file.  */
#define HAVE_SYS_SELECT_H 1

/* Name of package */
#define PACKAGE "gifsicle"

/* Version number of package */
#define VERSION "1.25"


#ifdef __cplusplus
extern "C" {
#endif

/* Use either the clean-failing malloc library in fmalloc.c, or the debugging
   malloc library in dmalloc.c. */
#ifdef DMALLOC
# include "dmalloc.h"
# define Gif_DeleteFunc		(&debug_free)
# define Gif_DeleteArrayFunc	(&debug_free)
#else
# include <stddef.h>
# define xmalloc(s)		fail_die_malloc((s),__FILE__,__LINE__)
# define xrealloc(p,s)		fail_die_realloc((p),(s),__FILE__,__LINE__)
# define xfree			free
void *fail_die_malloc(size_t, const char *, int);
void *fail_die_realloc(void *, size_t, const char *, int);
#endif

/* Prototype strerror if we don't have it. */
#ifndef HAVE_STRERROR
char *strerror(int errno);
#endif

#ifdef __cplusplus
}
/* Get rid of a possible inline macro under C++. */
/* # undef inline */
#endif
#endif
