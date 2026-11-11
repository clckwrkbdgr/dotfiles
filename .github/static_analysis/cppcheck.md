# cppcheck rules

## 64-bit portability

Check if there is 64-bit portability issues:

- assign address to/from int/long
- casting address from/to integer when returning from function

## Assert

Warn if there are side effects in assert statements (since this cause different behaviour in debug/release builds).

## Auto Variables

A pointer to a variable is only valid as long as the variable is in scope.
Check:

- returning a pointer to auto or temporary variable
- assigning address of an variable to an effective parameter of a function
- returning reference to local/temporary variable
- returning address of function parameter
- suspicious assignment of pointer argument
- useless assignment of function argument

## Boolean

Boolean type checks

- using increment on boolean
- comparison of a boolean expression with an integer other than 0 or 1
- comparison of a function returning boolean value using relational operator
- comparison of a boolean value with boolean value using relational operator
- using bool in bitwise expression
- pointer addition in condition (either dereference is forgot or pointer overflow is required to make the condition false)
- Assigning bool value to pointer or float
- Returning an integer other than 0 or 1 from a function with boolean return value

## Boost usage

Check for invalid usage of Boost:

- container modification during `BOOST_FOREACH`

## Bounds checking

Out of bounds checking:

- Array index out of bounds
- Pointer arithmetic overflow
- Buffer overflow
- Dangerous usage of `strncat()`
- Using array index before checking it
- Partial string write that leads to buffer that is not zero terminated.
- Check for large enough arrays being passed to functions
- Allocating memory with a negative size

## Check function usage

Check function usage:

- missing `return` in non-void function
- return value of certain functions not used
- invalid input values for functions
- Warn if a function is called whose usage is discouraged
- `memset()` third argument is zero
- `memset()` with a value out of range as the 2nd parameter
- `memset()` with a float as the 2nd parameter
- copy elision optimization for returning value affected by std::move
- use `memcpy()`/`memset()` instead of for loop

## Class

Check the code for each class.

- Missing constructors and copy constructors
- Constructors which should be explicit
- Are all variables initialized by the constructors?
- Are all variables assigned by `operator=`?
- Warn if memset, memcpy etc are used on a class
- Warn if memory for classes is allocated with `malloc()`
- If it's a base class, check that the destructor is virtual
- Are there unused private functions?
- `operator=` should check for assignment to self
- Constness for member functions
- Order of initializations
- Suggest usage of initialization list
- Initialization of a member with itself
- Suspicious subtraction from 'this'
- Call of pure virtual function in constructor/destructor
- Duplicated inherited data members
- Check that arbitrary usage of public interface does not result in division by zero
- Delete "self pointer" and then access `this`
- Check that the `override` keyword is used when overriding virtual functions
- Check that the 'one definition rule' is not violated

## Condition

Match conditions with assignments and other conditions:

- Mismatching assignment and comparison `=>` comparison is always true/false
- Mismatching lhs and rhs in comparison `=>` comparison is always true/false
- Detect usage of `|` where `&` should be used
- Duplicate condition and assignment
- Detect matching `if` and `else if` conditions
- Mismatching bitand `(a &= 0xf0; a &= 1; => a = 0)`
- Opposite inner condition is always false
- Identical condition after early exit is always false
- Condition that is always true/false
- Mutual exclusion over `||` always evaluating to true
- Comparisons of modulo results that are always true/false.
- Known variable values `=>` condition is always true/false
- Invalid test for overflow. Some mainstream compilers remove such overflow tests when optimising code.
- Suspicious assignment of container/iterator in condition `=>` condition is always true.

## Exception Safety

Checking exception safety

- Throwing exceptions in destructors
- Throwing exception during invalid state
- Throwing a copy of a caught exception instead of rethrowing the original exception
- Exception caught by value instead of by reference
- Throwing exception in `noexcept`, `nothrow()`, `attribute((nothrow))` or `__declspec(nothrow)` function
- Unhandled exception specification when calling function `foo()`
- Rethrow without currently handled exception

## IO using format string

Check format string input/output operations.

- Bad usage of the function `sprintf` (overlapping data)
- Missing or wrong width specifiers in `scanf` format string
- Use a file that has been closed
- File input/output without positioning results in undefined behaviour
- Read to a file that has only been opened for writing (or vice versa)
- Repositioning operation on a file opened in append mode
- The same file can't be open for read and write at the same time on different streams
- Using fflush() on an input stream
- Invalid usage of output stream. For example: `std::cout << std::cout`
- Wrong number of arguments given to `printf` or `scanf`

## Leaks (auto variables)

Detect when a auto variable is allocated but not deallocated or deallocated twice.

## Memory leaks (address not taken)

Not taking the address to allocated memory

## Memory leaks (class variables)

If the constructor allocate memory then the destructor must deallocate it.

## Memory leaks (function variables)

Is there any allocated memory when a function goes out of scope

## Memory leaks (struct members)

Don't forget to deallocate struct members

## Null pointer

Null pointers

- null pointer dereferencing
- undefined null pointer arithmetic

## Other

Other checks

- division with zero
- scoped object destroyed immediately after construction
- assignment in an assert statement
- free() or delete of an invalid memory location
- bitwise operation with negative right operand
- cast the return values of getc(),fgetc() and getchar() to character and compare it to EOF
- race condition with non-interlocked access after InterlockedDecrement() call
- expression `x = x++;` depends on order of evaluation of side effects
- overlapping write of union
- either division by zero or useless condition
- access of moved or forwarded variable.
- redundant data copying for const variable
- subsequent assignment or copying to a variable or buffer
- passing parameter by value
- Passing NULL pointer to function with variable number of arguments leads to UB.
- C-style pointer cast in C++ code
- casting between incompatible pointer types
- Incomplete statement
- check how signed char variables are used
- variable scope can be limited
- unusual pointer arithmetic. For example: `"abc" + 'd'`
- redundant assignment, increment, or bitwise operation in a switch statement
- redundant strcpy in a switch statement
- Suspicious case labels in switch()
- assignment of a variable to itself
- Comparison of values leading always to true or false
- Clarify calculation with parentheses
- suspicious comparison of `\0` with a `char*` variable
- duplicate break statement
- unreachable code
- testing if unsigned variable is negative/positive
- Suspicious use of `;` at the end of 'if/for/while' statement.
- Array filled incompletely using memset/memcpy/memmove.
- NaN (not a number) value used in arithmetic expression.
- comma in return statement (the comma can easily be misread as a semicolon).
- prefer erfc, expm1 or log1p to avoid loss of precision.
- identical code in both branches of if/else or ternary operator.
- redundant pointer operation on pointer like `&*some_ptr`.
- find unused 'goto' labels.
- function declaration and definition argument names different.
- function declaration and definition argument order different.
- shadow variable.
- variable can be declared const.
- calculating modulo of one.
- known function argument, suspicious calculation.

## STL usage

Check for invalid usage of STL:

- out of bounds errors
- misuse of iterators when iterating through a container
- mismatching containers in calls
- same iterators in calls
- dereferencing an erased iterator
- for vectors: using iterator/pointer after push_back has been used
- optimisation: use empty() instead of size() to guarantee fast code
- suspicious condition when using find
- unnecessary searching in associative containers
- redundant condition
- common mistakes when using `string::c_str()`
- useless calls of string and STL functions
- dereferencing an invalid iterator
- reading from empty STL container
- iterating over an empty STL container
- consider using an STL algorithm instead of raw loop
- incorrect locking with mutex

## Sizeof

sizeof() usage checks

- sizeof for array given as function argument
- sizeof for numeric given as function argument
- using sizeof(pointer) instead of the size of pointed data
- look for `sizeof sizeof ..`
- look for calculations inside sizeof()
- look for function calls inside sizeof()
- look for suspicious calculations with sizeof()
- using `sizeof(void)` which is undefined

## String

Detect misusage of C-style strings:

- overlapping buffers passed to sprintf as source and destination
- incorrect length arguments for 'substr' and 'strncmp'
- suspicious condition (runtime comparison of string literals)
- suspicious condition (string/char literals as boolean)
- suspicious comparison of a string literal with a char* variable
- suspicious comparison of `\0` with a `char*` variable
- overlapping `strcmp()` expression

## Type

Type checks

- bitwise shift by too many bits (only enabled when `--platform` is used)
- signed integer overflow (only enabled when `--platform` is used)
- dangerous sign conversion, when signed value can be negative
- possible loss of information when assigning int result to long variable
- possible loss of information when returning int result as long return value
- float conversion overflow

## Uninitialized variables

Uninitialized variables

- using uninitialized local variables
- using allocated data before it has been initialized

## Unused functions

Check for functions that are never called

## UnusedVar

UnusedVar checks

- unused variable
- allocated but unused variable
- unread variable
- unassigned variable
- unused struct member

## Using postfix operators

Warn if using postfix operators ++ or -- rather than prefix operator

## Vaarg

Check for misusage of variable argument lists:

- Wrong parameter passed to `va_start()`
- Reference passed to `va_start()`
- Missing `va_end()`
- Using `va_list` before it is opened
- Subsequent calls to `va_start/va_copy()`
