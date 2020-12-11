CC=vcvarsall cl
CXX=vcvarsall cl
LDFLAGS=/link $(CUSTOM_LDFLAGS)
BINEXT=.exe
WARNFLAGS=/W4 /WX
CFLAGS=/EHsc $(WARNFLAGS) $(CUSTOM_CFLAGS)
CXXFLAGS=/EHsc $(WARNFLAGS) $(CUSTOM_CXXFLAGS)

BUILD_OBJECTS=$(OBJECTS:+".obj")

run:: $(TARGET)
	$(TARGET)$(BINEXT)

$(TARGET): $(TARGET)$(BINEXT)

$(TARGET)$(BINEXT): $(BUILD_OBJECTS)
	$(CXX) $< $(LDFLAGS)

%.obj: %.c
	$(CXX) -c $^ $(CXXFLAGS)

%.obj: %.cpp
	$(CXX) -c $^ $(CFLAGS)

clean::
	rm -f $(TARGET)$(BINEXT) *.obj
