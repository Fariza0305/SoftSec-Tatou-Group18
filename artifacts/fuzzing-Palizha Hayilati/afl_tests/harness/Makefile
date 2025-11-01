# Makefile for AFL++ XML Parser Fuzzing Harness
# ==============================================

CC = afl-clang-fast
CXX = afl-clang-fast++
CFLAGS = -g -O2 -Wall -Wextra
LDFLAGS = -lxml2

# Sanitizer flags
ASAN_FLAGS = -fsanitize=address -fsanitize-address-use-after-scope
UBSAN_FLAGS = -fsanitize=undefined -fno-sanitize-recover=all
MSAN_FLAGS = -fsanitize=memory -fno-optimize-sibling-calls

# AFL++ instrumentation flags
AFL_FLAGS = -fsanitize=fuzzer-no-link

# Targets
HARNESS = xml_parser_harness
HARNESS_ASAN = $(HARNESS)_asan
HARNESS_UBSAN = $(HARNESS)_ubsan
HARNESS_PERSISTENT = $(HARNESS)_persistent

.PHONY: all clean asan ubsan persistent

all: $(HARNESS) asan ubsan persistent

# Standard build
$(HARNESS): xml_parser_harness.c
	$(CC) $(CFLAGS) $(AFL_FLAGS) -o $@ $< $(LDFLAGS)

# ASan build
asan: $(HARNESS_ASAN)
$(HARNESS_ASAN): xml_parser_harness.c
	$(CC) $(CFLAGS) $(AFL_FLAGS) $(ASAN_FLAGS) -o $@ $< $(LDFLAGS)

# UBSan build
ubsan: $(HARNESS_UBSAN)
$(HARNESS_UBSAN): xml_parser_harness.c
	$(CC) $(CFLAGS) $(AFL_FLAGS) $(UBSAN_FLAGS) -o $@ $< $(LDFLAGS)

# Persistent mode build
persistent: $(HARNESS_PERSISTENT)
$(HARNESS_PERSISTENT): xml_parser_harness.c
	$(CC) $(CFLAGS) $(AFL_FLAGS) -DAFL_PERSISTENT_MODE -o $@ $< $(LDFLAGS)

clean:
	rm -f $(HARNESS) $(HARNESS_ASAN) $(HARNESS_UBSAN) $(HARNESS_PERSISTENT)
	rm -rf *.dSYM

# Test targets
test: $(HARNESS)
	./$(HARNESS) ../seeds/valid_rmap.xml

test-asan: $(HARNESS_ASAN)
	./$(HARNESS_ASAN) ../seeds/valid_rmap.xml

test-ubsan: $(HARNESS_UBSAN)
	./$(HARNESS_UBSAN) ../seeds/valid_rmap.xml

