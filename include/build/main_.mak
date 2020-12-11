CC=gcc
CXX=g++
LDFLAGS=$(CUSTOM_LDFLAGS)
WARNFLAGS=-Wall -Wextra -Werror
CFLAGS=$(WARNFLAGS) $(CUSTOM_CFLAGS)
CXXFLAGS=$(WARNFLAGS) $(CUSTOM_CXXFLAGS)

BUILD_OBJECTS=$(OBJECTS:.=.o)

run:: $(TARGET)
	./$(TARGET)

$(TARGET): $(BUILD_OBJECTS)
	$(CXX) -o $(TARGET) $(BUILD_OBJECTS) $(LDFLAGS)

%.o: %.c
	$(CC) -c $^ $(CFLAGS)

%.o: %.cpp
	$(CXX) -c $^ $(CXXFLAGS)

clean::
	rm -f $(TARGET) *.o
