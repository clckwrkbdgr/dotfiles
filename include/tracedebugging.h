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
 *
 * Example of working with different streams:
 *   // Will append to mylogfile.log
 *   FILE * mylogfile = fopen("mylogfile.log", "a+");
 *   BADGER_CURRENT_LOG_STREAM(mylogfile)
 *   // Will write to stderr directly even if 'stderr' is redefined.
 *   BADGER_CURRENT_LOG_STREAM(BADGER_GET_DIRECT_STDERR());
 */

/*******************************************************************************
 * DEFINITIONS */

#ifdef __GNUC__
#define BADGER_STATIC_FUNCTION static __attribute__ ((unused))
#else
#define BADGER_STATIC_FUNCTION static /*inline */ /* AIX does not have pragmas to ignore 'unused' warnings */
#endif

#if defined(__cplusplus)
#  if defined(_WIN32)
#    define BADGER_EXTERN extern "C" __declspec(dllimport)
#  else
#    define BADGER_EXTERN extern "C"
#  endif
#else
#  if defined(_WIN32)
#    define BADGER_EXTERN __declspec(dllimport)
#  else
#    define BADGER_EXTERN extern
#  endif
#endif

#ifdef __cplusplus
# define BADGER_NOTHROW throw()
#else
# define BADGER_NOTHROW
#endif

/*******************************************************************************
 * SYSTEM STUFF */

#ifndef __GNUC__
#define __THROW
#endif

#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <sys/types.h> /* For pid_t */
#include <sys/stat.h> /* For mkdir */
#include <time.h>

/* #include <unistd.h> */
#if defined(_WIN32)
   BADGER_EXTERN
   unsigned long
   __stdcall
   GetCurrentProcessId(void);
#elif defined(__GNUC__)
#  ifdef _AIX
     BADGER_EXTERN pid_t getpid(void);
     BADGER_EXTERN int isatty (int __fd);
#  else
     BADGER_EXTERN pid_t getpid(void) __THROW;
     BADGER_EXTERN int isatty (int __fd) __THROW;
#  endif//AIX
#else
   BADGER_EXTERN pid_t getpid(void) __THROW;
   BADGER_EXTERN int isatty (int __fd) __THROW;
#endif//GNUC

/* #include <stdlib.h> */
#if defined(_WIN32)
   BADGER_EXTERN char * getenv(const char*);
#elif defined(__GNUC__)
   BADGER_EXTERN char * getenv(const char*) BADGER_NOTHROW;
#else
   BADGER_EXTERN char * getenv(const char*);
#endif

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
#ifndef _WIN32
      pid = getpid();
#else
      pid = GetCurrentProcessId();
#endif//_WIN32
   }
   return pid;
}

/** Returns base info prefix format string
 * (filename, line, pid etc.; ends with a space).
 * If use_colors is non-zero, add color escape sequences.
 */
BADGER_STATIC_FUNCTION
const char * BADGER_TRACE_FORMAT(int use_colors)
{
   if(use_colors) {
      return BADGER_MAGENTA "%s" BADGER_NOCOLOR
            ":" BADGER_YELLOW "%lld(%llx)" BADGER_NOCOLOR
            ":" BADGER_GREEN "%s" BADGER_NOCOLOR
            ":" BADGER_BLUE "%d" BADGER_NOCOLOR
            ":" BADGER_CYAN "%s" BADGER_NOCOLOR
            ":" " ";
   } else {
      return "%s:%lld(%llx):%s:%d:%s: ";
   }
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
   static long long pid = 0;
   if(pid == 0) {
       pid = BADGER_PID();
   }
#if defined(_WIN32)
   long long thread_id =  = GetCurrentThreadId();
#else
   static const long long thread_id = 0xA;
#endif
#ifndef _WIN32
   int use_colors = isatty(fileno(outfile));
#else
   static const int use_colors = 0;
#endif
   time_t timestamp = time(NULL);
   struct tm * tm_info = localtime(&timestamp);
   char time_buffer[24] = {0};
   strftime(time_buffer, sizeof(time_buffer) - 1, "%Y-%m-%d %H:%M:%S", tm_info);

   fprintf(outfile, BADGER_TRACE_FORMAT(use_colors), time_buffer, pid, thread_id, filename, line_number, func_name);
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

/** Returns stream for file descriptor=2 directly regardles of where
 * 'stderr' points to. It can be useful if application overrides default
 * 'stderr', like FastCGI does.
 */
BADGER_STATIC_FUNCTION
FILE * BADGER_GET_DIRECT_STDERR(void)
{
   FILE * direct_stderr = NULL;
   if(!direct_stderr) {
      direct_stderr = fdopen(2, "w");
   }
   return direct_stderr;
}

/** Returns default trace file name for usage in BADGER_GET_TRACE_FILE().
 * Default location is $HOME/badger.debug.trace
 * If $TTY_USERNAME is defined (e.g. for SSH connections),
 * trace files is stored in subdir: $HOME/$TTY_USERNAME/badger.debug.trace
 */
BADGER_STATIC_FUNCTION
const char * BADGER_DEFAULT_TRACE_FILE_NAME(void)
{
   static char path[255] = {0};
   if(!path[0]) {
#ifndef _WIN32
      strcpy(path, getenv("HOME"));
      if(getenv("TTY_USERNAME")) {
         strcat(path, "/");
         strcat(path, getenv("TTY_USERNAME"));
         mkdir(path, 0755);
      }
      strcat(path, "/badger.debug.trace");
#else
      strcpy(path, getenv("TEMP"));
      strcat(path, "/badger.debug.trace");
#endif//_WIN32
   }
   return path;
}

/** Returns main file stream for given filename.
 * Opens file for given filename if wasn't opened before.
 * See BADGER_DEFAULT_TRACE_FILE_NAME() for default trace file.
 */
BADGER_STATIC_FUNCTION
FILE * BADGER_GET_TRACE_FILE(const char * filename)
{
   static FILE * logfile = NULL;
   if(!logfile) {
      logfile = fopen(filename, "a+");
      if(!logfile) {
         fprintf(stderr, "Failed to open %s\n", filename);
         fflush(stderr);
         return NULL;
      }
   }
   return logfile;
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
