#pragma once
/** This is a header-only library that provides trace debugging
 * (AKA printf-debugging).
 * It's C/C++ compatible and has no dependencies except for stdlib/STL.
 *
 * It does not require any specific macro setup or whatnot,
 * just include it and litter your code with trace functions.
 * It is recommended to add this file to the list of unconditional includes,
 * usually defined in environment variable CFLAGS or CXXFLAGS:
 * - GCC: `-include /path/to/custom/include/tracedebugging.h`
 * - xlC: `-qinclude /path/to/custom/include/tracedebugging.h`
 * NOTE: Some implementations may require adding include directory explicitly:
 * `-I /path/to/custom/include`
 *
 * All symbols here (functions, macros) are named with prefix BADGER_.
 *
 * Example:
 *   void my_function(const char * arg)
 *   {
 *      BADGER_TRACE("Begin, arg=[%s]", arg);
 *   }
 * Example output (to stderr by default): 
 *   12345678:my_source_file.c:5:my_function: Begin, arg=[foo]
 */

/*******************************************************************************
 * DEFINITIONS */

#ifdef __GNUC__
#define BADGER_STATIC_FUNCTION static __attribute__ ((unused))
#else
#define BADGER_STATIC_FUNCTION static /*inline */ /* AIX does not have pragmas to ignore 'unused' warnings */
#endif

/*******************************************************************************
 * SYSTEM STUFF */

#ifndef __GNUC__
#define __THROW
#endif

#include <stdio.h>

/* #include <unistd.h> */
#ifdef __cplusplus
#  ifdef __GNUC__
#    ifdef _AIX
       extern "C" pid_t getpid(void);
       extern "C" int isatty (int __fd);
#    else
       extern "C" pid_t getpid(void) __THROW;
       extern "C" int isatty (int __fd) __THROW;
#    endif//AIX
#  else
     extern "C" pid_t getpid(void) __THROW;
     extern "C" int isatty (int __fd) __THROW;
#  endif//GNUC
#else
  extern pid_t getpid(void) __THROW;
  extern int isatty (int __fd) __THROW;
#endif //C++

/*******************************************************************************
 * HELPERS */

/** Bold colors are 1;31m */
#define BADGER_RED     "\033[0;31m"
#define BADGER_GREEN   "\033[0;32m"
#define BADGER_YELLOW  "\033[0;33m"
#define BADGER_BLUE    "\033[0;34m"
#define BADGER_MAGENTA "\033[0;35m"
#define BADGER_CYAN    "\033[0;36m"
#define BADGER_NOCOLOR "\033[0m"

/** Returns current process ID. */
BADGER_STATIC_FUNCTION
long long BADGER_PID()
{
   static long long pid = 0;
   if(!pid)
   {
      pid = getpid();
   }
   return pid;
}

/** Base function: prints formatted message with varargs to specified stream.
 * Default format is: <pid>:<filename>:<line_number>:<func_name>:<message...>
 * If outfile is a TTY, prints colored info fields.
 */
BADGER_STATIC_FUNCTION
void BADGER_VFPRINTF(FILE * outfile,
      const char * filename, int line_number, const char * func_name,
      const char * format, va_list args)
{
   if(outfile == NULL)
   {
      return;
   }
   static long long pid = BADGER_PID();
   if(isatty(fileno(outfile))) {
      fprintf(outfile, BADGER_MAGENTA "%lld" BADGER_NOCOLOR
            ":" BADGER_GREEN "%s" BADGER_NOCOLOR
            ":" BADGER_BLUE "%d" BADGER_NOCOLOR
            ":" BADGER_CYAN "%s" BADGER_NOCOLOR
            ":" " ", pid, filename, line_number, func_name);
   } else {
      fprintf(outfile, "%lld:%s:%d:%s: ", pid, filename, line_number, func_name);
   }
   vfprintf(outfile, format, args);
   fprintf(outfile, "\n");
   fflush(outfile);
}

/** Base function: prints formatted message to specified file. */
BADGER_STATIC_FUNCTION
void BADGER_FPRINTF(FILE * outfile, const char * filename, int line_number, const char * func_name, const char * format, ...)
{
   va_list args;
   va_start(args, format);
   BADGER_VFPRINTF(outfile, filename, line_number, func_name, format, args);
   va_end(args);
}

/** Returns current logging stream if parameter is NULL.
 * Sets current logging stream to the parameter otherwise.
 * Default is stderr.
 * Stream should be opened manually beforehand.
 */
BADGER_STATIC_FUNCTION
FILE * BADGER_CURRENT_LOG_STREAM(FILE * stream)
{
   static FILE * value = NULL;
   if(value == NULL)
   {
      value = stderr;
   }
   if(stream == NULL)
   {
      return value;
   }
   return value = stream;
}

/*******************************************************************************
 * MAIN */

/** Printf-like macro to print arguments to the current stream.
 * (see BADGER_CURRENT_LOG_STREAM, default is stderr)
 * Default format is following:
 *   <pid>:<filename>:<ln>:<func>: <message...>
 * Where:
 *   pid - current process ID;
 *   filename - source file name;
 *   ln - number of line where trace is placed;
 *   func - name of the function where traces is placed;
 *   message - printf-formatted message.
 */
#define BADGER_TRACE(...) BADGER_FPRINTF(BADGER_CURRENT_LOG_STREAM(NULL), __FILE__, __LINE__, __FUNCTION__, __VA_ARGS__)
