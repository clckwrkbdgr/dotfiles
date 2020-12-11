run:: $(TARGET)
	java $(TARGET).class

$(TARGET): $(TARGET).class

$(TARGET).class: $(TARGET).java
	@echo Compiling $(TARGET).java
	@javac -classpath $(CLASSPATH) $(TARGET).java

clean::
	@rm -f $(TARGET).class
