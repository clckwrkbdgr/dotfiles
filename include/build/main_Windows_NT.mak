SHELLMETAS=qwertyuiopasdfghjklzxcvbnm" *?<>|"

CC=vcvarsall cl
CXX=vcvarsall cl
AR=vcvarsall lib
RC=rc
LDFLAGS=/link $(LIBS:+".lib") $(CUSTOM_LDFLAGS)
WARNFLAGS=/W4 /WX
CFLAGS=/EHsc $(WARNFLAGS) $(INCLUDES:^"/I") $(CUSTOM_CFLAGS)
CXXFLAGS=/EHsc $(WARNFLAGS) $(INCLUDES:^"/I") $(CUSTOM_CXXFLAGS)

BUILD_OBJECTS=$(OBJECTS:+".obj") $(RESOURCES:+".RES")

EXECUTABLE=$(TARGET).exe
SHARED_LIB=$(TARGET).dll
STATIC_LIB=$(TARGET).lib

run:: $(EXECUTABLE)
	$(EXECUTABLE)

$(EXECUTABLE): $(BUILD_OBJECTS)
	$(CXX) $^ $(LDFLAGS) /OUT:$(EXECUTABLE)

$(STATIC_LIB): $(BUILD_OBJECTS)
	$(AR) $^ /OUT:$(STATIC_LIB)

$(SHARED_LIB): $(BUILD_OBJECTS)
	$(CXX) /LD /DLL $^ $(LDFLAGS) /OUT:$(SHARED_LIB)

%.rc: %_resource.h
	touch $@

%.RES: %.rc %_resource.h
	$(RC) $<

%.obj: %.c
	$(CXX) -c $^ $(CFLAGS)

%.obj: %.cpp
	$(CXX) -c $^ $(CXXFLAGS)

clean::
	rm -f $(EXECUTABLE) $(STATIC_LIB) $(SHARED_LIB) *.obj *.RES
