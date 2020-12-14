# A very primitive build system for simple applications,
# including these dotfiles' utilities.
#
# Just include this file in your project's root Makefile:
#   include $(HOME)/.config/include/build.mak
# It requires some setup (see below), but provides default targets,
# so it's better to include after all custom definitions
# but before any custom target/deps:
#   TARGET=...
#   OBJECTS=...
#   include <build.mak>
#   all: <target type>
#   mytarget:
#      ...
#
# Required setup:
# - TARGET = name of the resulting application/library/java class etc.,
#            without any extension.
# - OBJECTS = list of object files that consist main target (*.o, *obj etc),
#             without any extension.
# - Explicit target 'all' with specification of what type of target is being built.
#   Supported values:
#   - $(EXECUTABLE)
#   - $(SHARED_LIB)
#   - $(STATIC_LIB)
#   E.g.:
#     all: $(EXECUTABLE)
#     all: $(STATIC_LIB) $(SHARED_LIB)
#
# Supported targets (see below):
# - all: Builds main target.
# - run: Runs main executable target (and builds if needed).
# - clean: Removes all build artifacts.
#
# Supported languages/platforms:
# - C/C++: Windows MSVS, Unix GCC:
#   LIBS = additional libraries (no extensions).
#   INCLUDES = additional include directories.
#   CUSTOM_LDFLAGS = additional linker flags.
#   CUSTOM_CFLAGS = additional compiler flags for C.
#   CUSTOM_CXXFLAGS = additional compiler flags for C++.
#   Win-only:
#     RESOURCES = names of resource files (*.rc) without extensions.
#                 Each %.rc file is expected be supplied with %_resource.h header.
# - Java (define PLATFORM=Java before including this file).
#   CLASSPATH = Java classpath (semicolon-separated).

all:

run::

clean::

.PHONY: all clean

include $(HOME)/.config/include/build/main_$(PLATFORM)$(OS).mak
