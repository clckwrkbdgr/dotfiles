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
 * - MSVS: `/FI/path/to/custom/include/tracedebugging.h`
 *   For MSVS there is no such global variable like for *nix/Makefile,
 *   but there should be global user property file, usually:
 *   `$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props`.
 *   Values of these variables should be checked for every VS version,
 *   usually `UserRootDir = %LOCALAPPDATA%/Microsoft/MSBuild/v4.0`.
 *   Just add node `/ItemDefinitionGroup/ClCompile/ForcedIncludeFiles`
 *   with value `/path/to/custom/include/tracedebugging.h;%(ForcedIncludeFiles)`
 * NOTE: Some implementations may require to explicitly specify
 *       include directory, e.g.: * `-I /path/to/custom/include`
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
 *
 * Example of profiling:
 *   {
 *      BADGER_PROFILE_START("Entering scope", ...);
 *      ...
 *      BADGER_PROFILE("Tick...", ...);
 *      for(...)
 *      {
 *         ...
 *         BADGER_PROFILE("Tick...", ...);
 *      }
 *      ...
 *      BADGER_PROFILE("Tick...", ...);
 *      ...
 *      BADGER_PROFILE("Done");
 *   }
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
#    if !defined(_DLL)
#      define BADGER_EXTERN_CRT extern "C"
#    endif
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
#ifndef BADGER_EXTERN_CRT
#  define BADGER_EXTERN_CRT BADGER_EXTERN
#endif

#ifdef __cplusplus
# define BADGER_NOTHROW throw()
#else
# define BADGER_NOTHROW
#endif

#ifdef _WIN32
#pragma warning(push)
#pragma warning(disable : 4505) // Unreferenced local function has been removed
#endif

#if defined(_WIN32) && defined(__cplusplus) && ((_MANAGED == 1) || (_M_CEE == 1))
# define BADGER_WIN_CLR // MSVC++ /clr mode.
#endif

/*******************************************************************************
 * INITIALIZE */

#ifdef BADGER_WIN_CLR
#pragma unmanaged
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
   BADGER_EXTERN
   unsigned long
   __stdcall
   GetCurrentThreadId(void);
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

#if defined(_WIN32)
   BADGER_EXTERN_CRT
#     if _MSC_VER >= 1900 // VS2015+
      __declspec(allocator)
#     else
      __declspec(noalias)
#     endif
      __declspec(restrict)
      void * malloc (size_t __size);
   BADGER_EXTERN_CRT
#     if _MSC_VER < 1900 // VS2015+
      __declspec(noalias)
#     endif
      void free (void *__ptr);
#else
#  ifdef _AIX
     BADGER_EXTERN void * malloc (size_t __size);
     BADGER_EXTERN void free (void *__ptr);
#  else
     BADGER_EXTERN void * malloc (size_t __size) __THROW;
     BADGER_EXTERN void free (void *__ptr) __THROW;
#  endif//AIX
#endif

/* #include <stdlib.h> */
#if defined(_WIN32)
   BADGER_EXTERN_CRT char * getenv(const char*);
#elif defined(__GNUC__)
#  ifdef _AIX
     BADGER_EXTERN char * getenv(const char*);
#  else
     BADGER_EXTERN char * getenv(const char*) BADGER_NOTHROW;
#  endif//AIX
#else
   BADGER_EXTERN char * getenv(const char*);
#endif

#ifdef _WIN32
BADGER_EXTERN
void
__stdcall
OutputDebugStringA(
    const char * lpOutputString
    );
#endif

#ifdef _WIN32
union _LARGE_INTEGER;

BADGER_EXTERN
int
__stdcall
QueryPerformanceCounter(
    union _LARGE_INTEGER * lpPerformanceCount
    );

BADGER_EXTERN
int
__stdcall
QueryPerformanceFrequency(
    union _LARGE_INTEGER * lpFrequency
    );
#endif

/*******************************************************************************
 * HELPERS */

#define BADGER_ISPRINTABLE(c)  ( c >= 0x20 && c <= 0x7e )

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

/** Returns current thread ID. */
BADGER_STATIC_FUNCTION
long long BADGER_THREAD_ID()
{
#ifndef _WIN32
   return 0xA;
#else
   return GetCurrentThreadId();
#endif//_WIN32
}

BADGER_STATIC_FUNCTION
const char * BADGER_TIMESTAMP(char * time_str_buffer, size_t buffer_size)
{
   time_t timestamp;
#ifndef _WIN32
   struct tm * tm_info = NULL;
#else
   struct tm tm_buffer;
   struct tm * tm_info = &tm_buffer;
#endif
   timestamp = time(NULL);
#ifndef _WIN32
   tm_info = localtime(&timestamp);
#else
   localtime_s(tm_info, &timestamp);
#endif
   strftime(time_str_buffer, buffer_size - 1, "%Y-%m-%d %H:%M:%S", tm_info);
   time_str_buffer[buffer_size - 1] = 0;
   return time_str_buffer;
}

/** Returns 1 (TRUE) if stream supports color sequences.
 */
BADGER_STATIC_FUNCTION
int BADGER_USE_COLORS(FILE * stream)
{
#ifndef _WIN32
   return isatty(fileno(stream));
#else
   (void)stream;
   return 0;
#endif
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

/** Returns formatted debug trace line.
 * Memory is auto-allocated to fit the full line.
 * WARNING: Memory should be freed by caller!
 */
BADGER_STATIC_FUNCTION
char * BADGER_VSNPRINTF(const char * format, va_list args)
{
   size_t needed = 0;
   char * buffer = NULL;

#if defined(_WIN32) && _MSC_VER < 1900 // MSVS 2015+
# define vscprintf(...) _vscprintf(__VA_ARGS__)
# define vsnprintf(buffer, size, ...) vsnprintf_s(buffer, size, size, __VA_ARGS__)
#else
# define vscprintf(...) vsnprintf(NULL, 0, __VA_ARGS__)
#endif
   needed = vscprintf(format, args);
   buffer = (char*)malloc(needed + 1);

   vsnprintf(buffer, needed + 1, format, args);
   buffer[needed] = '\0';
#if defined(_WIN32) && _MSC_VER < 1900 // MSVS 2015+
# undef vsnprintf
#endif
#undef vscprintf

   return buffer;
}

/** Returns formatted debug trace line.
 * Memory is auto-allocated to fit the full line.
 * WARNING: Memory should be freed by caller!
 */
BADGER_STATIC_FUNCTION
char * BADGER_SNPRINTF(const char * format, ...)
{
   va_list args;
   char * result = NULL;
   va_start(args, format);
   result = BADGER_VSNPRINTF(format, args);
   va_end(args);
   return result;
}

/** Creates string with trace header.
 * Default format is: <pid>:<filename>:<line_number>:<func_name>:
 * Header ends with a space.
 * Memory is auto-allocated to fit the full header.
 * WARNING: Memory should be freed by caller!
 */
BADGER_STATIC_FUNCTION
char * BADGER_GET_TRACE_HEADER(
      const char * filename, int line_number, const char * func_name,
      int use_colors
      )
{
   char time_buffer[24] = {0};
   const char * format = NULL;
   format = BADGER_TRACE_FORMAT(use_colors),
   BADGER_TIMESTAMP(time_buffer, sizeof(time_buffer));

   return BADGER_SNPRINTF(format,
         time_buffer, BADGER_PID(), BADGER_THREAD_ID(),
         filename, line_number, func_name);
}

/** Puts string to outfile.
 * No line break is added.
 * On Windows additionally prints it to debug console.
 */
BADGER_STATIC_FUNCTION
void BADGER_FPUTS(FILE * outfile, const char * text)
{
   fputs(text, outfile);
#ifdef _WIN32
   OutputDebugStringA(text);
#endif
}

/** Base function: prints formatted message to specified file.
 * Default format is: <pid>:<filename>:<line_number>:<func_name>:<message...>
 * If outfile is a TTY, prints colored info fields.
 */
BADGER_STATIC_FUNCTION
void BADGER_FPRINTF(FILE * outfile,
      const char * filename, int line_number, const char * func_name,
      const char * format, ...)
{
   va_list args;
   char * header;
   char * message;
   if(outfile == NULL)
   {
      return;
   }

   header = BADGER_GET_TRACE_HEADER(filename, line_number, func_name,
         BADGER_USE_COLORS(outfile)
         );
   BADGER_FPUTS(outfile, header);
   free((void*)header);

   va_start(args, format);
   message = BADGER_VSNPRINTF(format, args);
   va_end(args);
   BADGER_FPUTS(outfile, message);
   free((void*)message);

   BADGER_FPUTS(outfile, "\n");
   fflush(outfile);
}

/** Prints formatted array of chars (bytes) with caption.
 * Outputs printable characters as-is with heading dot symbol, for non-printable dumps their hex equivalent.
 * Dumps 16 charactes in a row.
 * Default format follows basic BADGER_FPRINTF().
 * See BADGER_FPRINTF() for more details.
 */
BADGER_STATIC_FUNCTION
void BADGER_FPRINTF_ARRAY(FILE * outfile,
      const char * filename, int line_number, const char * func_name,
      const char * caption, const char * arr, size_t arr_size)
{
   char * header;
   char * part;
   static char _badger_char;
   static char _badger_output[4];
   static char const hex_chars[16] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };
   size_t _badger_index;
   size_t _badger_subindex;
   if(outfile == NULL)
   {
      return;
   }

   _badger_output[0] = ' ';
   _badger_output[3] = '\0';

   header = BADGER_GET_TRACE_HEADER(filename, line_number, func_name,
         BADGER_USE_COLORS(outfile)
         );
   BADGER_FPUTS(outfile, header);
   free((void*)header);
   BADGER_FPUTS(outfile, caption);
   BADGER_FPUTS(outfile, ":\n");

#define BADGER_ARRAY_CHARS_IN_A_ROW 16
   for (_badger_index = 0; _badger_index <= (size_t)(arr_size / BADGER_ARRAY_CHARS_IN_A_ROW); ++_badger_index)
   {
      part = BADGER_SNPRINTF( /* TODO should re-use static buffer instead of allocating anew */
            "  %u-%u = [ ",
            _badger_index * BADGER_ARRAY_CHARS_IN_A_ROW,
            _badger_index * BADGER_ARRAY_CHARS_IN_A_ROW + BADGER_ARRAY_CHARS_IN_A_ROW - 1
            );
      BADGER_FPUTS(outfile, part);
      free((void*)part);

      for (_badger_subindex = 0; _badger_subindex < BADGER_ARRAY_CHARS_IN_A_ROW; ++_badger_subindex)
      {
         if (_badger_index * BADGER_ARRAY_CHARS_IN_A_ROW + _badger_subindex >= arr_size) {
            break;
         }
         _badger_char = arr[_badger_index * BADGER_ARRAY_CHARS_IN_A_ROW + _badger_subindex];
         if (BADGER_ISPRINTABLE(_badger_char)) {
            _badger_output[1] = '.';
            _badger_output[2] = _badger_char;
         } else {
            _badger_output[1] = hex_chars[(_badger_char & 0xF0) >> 4];
            _badger_output[2] = hex_chars[(_badger_char & 0x0F) >> 0];
         }
         BADGER_FPUTS(outfile, _badger_output);
      }
      BADGER_FPUTS(outfile, " ]\n");
   }
   fflush(outfile);
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
#ifndef _WIN32
      direct_stderr = fdopen(2, "w");
#else
      direct_stderr = _fdopen(2, "w");
#endif
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
      strcpy_s(path, sizeof(path) - 1, getenv("TEMP"));
      strcat_s(path, sizeof(path) - 1, "/badger.debug.trace");
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
#ifndef _WIN32
      logfile = fopen(filename, "a+");
#else
      logfile = _fsopen(filename, "a+", 0x40); // _SH_DENYNO to allow shared access.
#endif
      if(!logfile) {
         fprintf(stderr, "Failed to open %s\n", filename);
         fflush(stderr);
         return NULL;
      }
   }
   return logfile;
}

/*******************************************************************************
 * PROFILING */

#if defined(_WIN32) && defined(__cplusplus) // [platform-specific]

typedef long long BADGER_ULTRA_TIME;

/** Returns current timestamp with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_GET_ULTRA_TIMESTAMP(void)
{
   static BADGER_ULTRA_TIME frequency = 0;
   if(!frequency) {
     QueryPerformanceFrequency((union _LARGE_INTEGER *)&frequency);
   }
   BADGER_ULTRA_TIME current;
   QueryPerformanceCounter((union _LARGE_INTEGER *)&current);
   current = current * 1000000 / frequency;
   return current;
}

/** Converts ultra timestamp with microseconds to unsigned long long. */
BADGER_STATIC_FUNCTION
unsigned long long BADGER_ULTRA_TIME_TO_ULLONG(BADGER_ULTRA_TIME timestamp)
{
   return timestamp;
}

/** Returns difference between two ultra timestamps with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_ULTRA_TIME_DIFF(BADGER_ULTRA_TIME end, BADGER_ULTRA_TIME begin)
{
   return end - begin;
}

#elif __linux__

typedef struct timespec BADGER_ULTRA_TIME;

/** Returns current timestamp with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_GET_ULTRA_TIMESTAMP(void)
{
   BADGER_ULTRA_TIME current;
   clock_gettime(CLOCK_REALTIME, &current);
   return current;
}

/** Converts ultra timestamp with microseconds to unsigned long long. */
BADGER_STATIC_FUNCTION
unsigned long long BADGER_ULTRA_TIME_TO_ULLONG(BADGER_ULTRA_TIME timestamp)
{
   return timestamp.tv_sec * 1000000 + timestamp.tv_nsec / 1000;
}

/** Returns difference between two ultra timestamps with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_ULTRA_TIME_DIFF(BADGER_ULTRA_TIME end, BADGER_ULTRA_TIME begin)
{
   BADGER_ULTRA_TIME result;
   result.tv_sec = end.tv_sec - begin.tv_sec;
   result.tv_nsec = end.tv_nsec - begin.tv_nsec;
   return result;
}

#else // Default dumb implementation.

typedef time_t BADGER_ULTRA_TIME;

/** Returns current timestamp with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_GET_ULTRA_TIMESTAMP(void)
{
   return time(NULL);
}

/** Converts ultra timestamp with microseconds to unsigned long long. */
BADGER_STATIC_FUNCTION
unsigned long long BADGER_ULTRA_TIME_TO_ULLONG(BADGER_ULTRA_TIME timestamp)
{
   return timestamp;
}

/** Returns difference between two ultra timestamps with microseconds. */
BADGER_STATIC_FUNCTION
BADGER_ULTRA_TIME BADGER_ULTRA_TIME_DIFF(BADGER_ULTRA_TIME end, BADGER_ULTRA_TIME begin)
{
   return end - begin;
}

#endif // [platform-specific]

/** Profile tracking data. */
struct BADGER_PROFILE_STAMP
{
   BADGER_ULTRA_TIME start;
   BADGER_ULTRA_TIME last;
};

/** Prints formatted trace like BADGER_FPRINTF with additional
 * time profiling info.
 * Creates and returns BADGER_PROFILE_STAMP structure,
 * initialized to the start of the function.
 */
BADGER_STATIC_FUNCTION
struct BADGER_PROFILE_STAMP
BADGER_PROFILE_INIT_FPRINTF(FILE * outfile,
      const char * filename, int line_number, const char * func_name,
      const char * format, ...)
{
   va_list args;
   char * header;
   char * time_profile;
   char * message;
   struct BADGER_PROFILE_STAMP stamp;
   unsigned long long value;
   unsigned long long full_secs;
   unsigned long long full_msecs;
   if(outfile == NULL)
   {
      memset(&stamp, 0, sizeof(stamp));
      return stamp;
   }
   stamp.start = BADGER_GET_ULTRA_TIMESTAMP();
   stamp.last = stamp.start;

   header = BADGER_GET_TRACE_HEADER(filename, line_number, func_name,
         BADGER_USE_COLORS(outfile)
         );
   BADGER_FPUTS(outfile, header);
   free((void*)header);

   value = BADGER_ULTRA_TIME_TO_ULLONG(stamp.start);
   full_secs = value / 1000000;
   full_msecs = value % 1000000;
   time_profile = BADGER_SNPRINTF(
         "[profile started at %llu.%6llu] ",
         full_secs, full_msecs
         );
   BADGER_FPUTS(outfile, time_profile);
   free((void*)time_profile);

   va_start(args, format);
   message = BADGER_VSNPRINTF(format, args);
   va_end(args);
   BADGER_FPUTS(outfile, message);
   free((void*)message);

   BADGER_FPUTS(outfile, "\n");
   fflush(outfile);

   return stamp;
}

/** Prints formatted trace like BADGER_FPRINTF with additional
 * time profiling info.
 * Updates received BADGER_PROFILE_STAMP.last
 * with current timestamp.
 * Prints time passed since the last call and since the start call.
 */
BADGER_STATIC_FUNCTION
void
BADGER_PROFILE_FPRINTF(
      struct BADGER_PROFILE_STAMP * stamp,
      FILE * outfile,
      const char * filename, int line_number, const char * func_name,
      const char * format, ...)
{
   va_list args;
   char * header;
   BADGER_ULTRA_TIME now;
   char * time_profile;
   char * message;
   if(outfile == NULL)
   {
      return;
   }
   now = BADGER_GET_ULTRA_TIMESTAMP();

   header = BADGER_GET_TRACE_HEADER(filename, line_number, func_name,
         BADGER_USE_COLORS(outfile)
         );
   BADGER_FPUTS(outfile, header);
   free((void*)header);

   time_profile = BADGER_SNPRINTF(
         "[passed: %llu msec, total: %llu msec] ",
         BADGER_ULTRA_TIME_TO_ULLONG(BADGER_ULTRA_TIME_DIFF(now, stamp->last)),
         BADGER_ULTRA_TIME_TO_ULLONG(BADGER_ULTRA_TIME_DIFF(now, stamp->start))
         );
   BADGER_FPUTS(outfile, time_profile);
   free((void*)time_profile);

   va_start(args, format);
   message = BADGER_VSNPRINTF(format, args);
   va_end(args);
   BADGER_FPUTS(outfile, message);
   free((void*)message);

   BADGER_FPUTS(outfile, "\n");
   fflush(outfile);

   stamp->last = now;
}

/*******************************************************************************
 * MAIN */

/** Printf-like macro to print arguments to the current stream.
 * (see BADGER_CURRENT_LOG_STREAM, default is stderr)
 * Default format is following:
 *   <date/time>:<pid>:<filename>:<ln>:<func>: <message...>
 * Where:
 *   date/time - ISO repr. of current timestamp;
 *   pid - current process ID;
 *   filename - source file name;
 *   ln - number of line where trace is placed;
 *   func - name of the function where traces is placed;
 *   message - printf-formatted message.
 */
#define BADGER_TRACE(...) \
   BADGER_FPRINTF(BADGER_CURRENT_LOG_STREAM(NULL), \
         __FILE__, __LINE__, __FUNCTION__, __VA_ARGS__)

/** Printf-like macro to print arguments to the current stream.
 * (see BADGER_CURRENT_LOG_STREAM, default is stderr)
 * Default format is following:
 *   <date/time>:<pid>:<filename>:<ln>:<func>: <message...>
 * Where:
 *   date/time - ISO repr. of current timestamp;
 *   pid - current process ID;
 *   filename - source file name;
 *   ln - number of line where trace is placed;
 *   func - name of the function where traces is placed;
 *   message - printf-formatted message.
 */
#define BADGER_TRACE_ARRAY(caption, arr, arr_size) \
   BADGER_FPRINTF_ARRAY(BADGER_CURRENT_LOG_STREAM(NULL), \
         __FILE__, __LINE__, __FUNCTION__, caption, arr, arr_size)

/** Function to start profiling in scope.
 * Required for BADGER_PROFILE() calls (see below).
 * May print optional trace (using printf-like formatting).
 * Whole messsage is formatted using same functionality as in BADGER_TRACE().
 */
#define BADGER_PROFILE_START(...) \
   struct BADGER_PROFILE_STAMP BADGER_PROFILE_STAMP_VARIABLE = \
   BADGER_PROFILE_INIT_FPRINTF(BADGER_CURRENT_LOG_STREAM(NULL), \
         __FILE__, __LINE__, __FUNCTION__, __VA_ARGS__)

/** Main profiling function.
 * Requires initial call to BADGER_PROFILE_START().
 * Prints time in microseconds passed since the last call
 * and since the initial call to BADGER_PROFILE_START().
 * May print optional trace (using printf-like formatting).
 * Whole messsage is formatted using same functionality as in BADGER_TRACE().
 */
#define BADGER_PROFILE(...) \
   BADGER_PROFILE_FPRINTF(&BADGER_PROFILE_STAMP_VARIABLE, \
         BADGER_CURRENT_LOG_STREAM(NULL), \
         __FILE__, __LINE__, __FUNCTION__, __VA_ARGS__)

/*******************************************************************************
 * FINALIZE */

#ifdef BADGER_WIN_CLR
#  pragma managed
#endif

#if defined(_WIN32) && defined(__cplusplus)
#  pragma warning(pop) // For C4505 (unreferenced local function has been removed)
// On some version it still does not work, so forcing usage:
static long long BADGER__UNUSED_FUNCTION_1 = reinterpret_cast<long long>(BADGER_FPRINTF);
static long long BADGER__UNUSED_FUNCTION_1_1 = reinterpret_cast<long long>(BADGER_FPRINTF_ARRAY);
static long long BADGER__UNUSED_FUNCTION_2 = reinterpret_cast<long long>(BADGER_CURRENT_LOG_STREAM);
static long long BADGER__UNUSED_FUNCTION_3 = reinterpret_cast<long long>(BADGER_GET_DIRECT_STDERR);
static long long BADGER__UNUSED_FUNCTION_4 = reinterpret_cast<long long>(BADGER_DEFAULT_TRACE_FILE_NAME);
static long long BADGER__UNUSED_FUNCTION_5 = reinterpret_cast<long long>(BADGER_GET_TRACE_FILE);
static long long BADGER__UNUSED_FUNCTION_6 = reinterpret_cast<long long>(BADGER_PROFILE_INIT_FPRINTF);
static long long BADGER__UNUSED_FUNCTION_7 = reinterpret_cast<long long>(BADGER_PROFILE_FPRINTF);
#endif
