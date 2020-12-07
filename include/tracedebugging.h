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
   BADGER_EXTERN
#     if _MSC_VER >= 1900 // VS2015+
      __declspec(allocator)
#     else
      __declspec(noalias)
#     endif
      __declspec(restrict)
      void * malloc (size_t __size);
   BADGER_EXTERN
#     if _MSC_VER < 1900 // VS2015+
      __declspec(noalias)
#     endif
      void free (void *__ptr);
#else
   BADGER_EXTERN void * malloc (size_t __size) __THROW;
   BADGER_EXTERN void free (void *__ptr) __THROW;
#endif

/* #include <stdlib.h> */
#if defined(_WIN32)
   BADGER_EXTERN char * getenv(const char*);
#elif defined(__GNUC__)
   BADGER_EXTERN char * getenv(const char*) BADGER_NOTHROW;
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
   size_t needed = 0;
   char * buffer = NULL;
   format = BADGER_TRACE_FORMAT(use_colors),
   BADGER_TIMESTAMP(time_buffer, sizeof(time_buffer));

#if defined(_WIN32) && _MSC_VER < 1900 // MSVS 2015+
# define snprintf(buffer, size, ...) _snprintf_s(buffer, size, size, __VA_ARGS__)
#endif
   needed = snprintf(NULL, 0, format,
         time_buffer, BADGER_PID(), BADGER_THREAD_ID(),
         filename, line_number, func_name);
   buffer = (char*)malloc(needed + 1);

   snprintf(buffer, needed + 1, format,
         time_buffer, BADGER_PID(), BADGER_THREAD_ID(),
         filename, line_number, func_name);
   buffer[needed] = '\0';
#if defined(_WIN32) && _MSC_VER < 1900 // MSVS 2015+
# undef snprintf
#endif

   return buffer;
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
# define vsnprintf(buffer, size, ...) vsnprintf_s(buffer, size, size, __VA_ARGS__)
#endif
   needed = vsnprintf(NULL, 0, format, args);
   buffer = (char*)malloc(needed + 1);

   vsnprintf(buffer, needed + 1, format, args);
   buffer[needed] = '\0';
#if defined(_WIN32) && _MSC_VER < 1900 // MSVS 2015+
# undef vsnprintf
#endif

   return buffer;
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
   char * header;
   char * message;
   if(outfile == NULL)
   {
      return;
   }

   header = BADGER_GET_TRACE_HEADER(filename, line_number, func_name,
         BADGER_USE_COLORS(outfile)
         );
   fputs(header, outfile);
#ifdef _WIN32
   OutputDebugStringA(header);
#endif
   free((void*)header);

   message = BADGER_VSNPRINTF(format, args);
   fputs(message, outfile);
#ifdef _WIN32
   OutputDebugStringA(message);
#endif
   free((void*)message);

   fputs("\n", outfile);
#ifdef _WIN32
   OutputDebugStringA("\n");
#endif
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
      fopen_s(&logfile, filename, "a+");
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
#define BADGER_TRACE(...) BADGER_FPRINTF(BADGER_CURRENT_LOG_STREAM(NULL), __FILE__, __LINE__, __FUNCTION__, __VA_ARGS__)

/*******************************************************************************
 * FINALIZE */

#ifdef BADGER_WIN_CLR
#pragma managed
#endif

#if defined(_WIN32) && defined(__cplusplus)
#pragma warning(pop) // For C4505 (unreferenced local function has been removed)
// On some version it still does not work, so forcing usage:
static void * BADGER__UNUSED_FUNCTION_1 = (void*)BADGER_FPRINTF;
static void * BADGER__UNUSED_FUNCTION_2 = (void*)BADGER_CURRENT_LOG_STREAM;
static void * BADGER__UNUSED_FUNCTION_3 = (void*)BADGER_GET_DIRECT_STDERR;
static void * BADGER__UNUSED_FUNCTION_4 = (void*)BADGER_DEFAULT_TRACE_FILE_NAME;
static void * BADGER__UNUSED_FUNCTION_5 = (void*)BADGER_GET_TRACE_FILE;
#endif
