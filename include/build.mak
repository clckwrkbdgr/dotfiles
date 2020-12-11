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
#   mytarget:
#      ...
#
# Required setup:
# - TARGET = name of the resulting application/library/java class etc.,
#            without any extension.
# - OBJECTS = list of object files that consist main target (*.o, *obj etc),
#             without any extension.
#
# Supported targets (see below):
# - all: Builds main target.
# - run: Runs main target (and builds if needed).
# - clean: Removes all build artifacts.
#
# Supported languages/platforms:
# - C/C++: Windows MSVS, Unix GCC:
#   CUSTOM_LDFLAGS = additional linker flags.
#   CUSTOM_CFLAGS = additional compiler flags for C.
#   CUSTOM_CXXFLAGS = additional compiler flags for C++.
# - Java (define PLATFORM=Java before including this file).
#   CLASSPATH = Java classpath (semicolon-separated).

all: $(TARGET)

run:: $(TARGET)

clean::

.PHONY: all clean

include $(HOME)/.config/include/build/main_$(PLATFORM)$(OS).mak
