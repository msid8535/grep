# Python Grep - Lightweight Regex Engine

A from-scratch implementation of a grep-like utility in Python, featuring a custom regex parser and matching engine.

## Overview

This project implements a lightweight regular expression engine that provides core pattern matching functionality similar to `grep -E`. Rather than relying on Python's built-in `re` module, it builds the entire regex parsing and matching logic from the ground up.

## Features

### Supported Regex Syntax

- **Literals** - Match exact characters
- **Character Classes** - `[abc]` matches any character in the set
- **Negated Classes** - `[^abc]` matches any character NOT in the set
- **Shorthand Classes**
  - `\d` - Matches any digit (0-9)
  - `\w` - Matches word characters (alphanumeric + underscore)
- **Wildcards** - `.` matches any character except newline
- **Quantifiers**
  - `+` - One or more occurrences (greedy)
  - `?` - Zero or one occurrence
- **Anchors**
  - `^` - Match start of line
  - `$` - Match end of line
- **Grouping & Alternation**
  - `(...)` - Group expressions
  - `|` - Alternation (logical OR)

## Usage

```bash
./your_program.sh -E '<pattern>'
```

The program reads input from stdin and exits with:
- `0` if the pattern matches
- `1` if the pattern doesn't match
- `2` if arguments are invalid

### Examples

# Match lines containing digits
```bash
echo "abc123def" | ./your_program.sh -E '\d+'
echo $?
```

# Match email-like patterns
```bash
echo "user@example.com" | ./your_program.sh -E '\w+@\w+\.\w+'
echo $?
```

# Match lines starting with specific text
```bash
echo "Hello World" | ./your_program.sh -E '^Hello'
echo $?
```

# Match alternation
```bash
echo "cat" | ./your_program.sh -E '(cat|dog|bird)'
echo $?
```

# Complex pattern with multiple features
```bash
echo "test-123" | ./your_program.sh -E '^[a-z]+-\d+$'
echo $?
```

## Implementation Details

### Architecture

The implementation consists of three main components:

1. **Pattern Parser** (`parse_pattern`)
   - Tokenizes the regex pattern into an abstract syntax tree
   - Handles nested groups and alternation
   - Attaches quantifiers to their corresponding tokens

2. **Token Matcher** (`token_matches_char`)
   - Determines if a single character matches a token type
   - Handles character classes, escapes, and wildcards

3. **Recursive Matcher** (`match_from`)
   - Recursively matches token sequences against input
   - Handles quantifiers with greedy matching
   - Explores multiple possible matches using backtracking

### Key Design Decisions

- **Greedy Quantifiers**: The `+` quantifier matches as much as possible, then backtracks if needed
- **Multi-line Support**: Input is processed line-by-line and also as a complete string for unanchored patterns
- **Set-based Matching**: Returns all possible match endpoints for comprehensive pattern exploration

## Limitations

This is a learning/demonstration project and doesn't implement the full POSIX or PCRE regex specifications. Notable omissions include:

- `*` (zero or more) quantifier
- `{n,m}` repetition counts
- Backreferences
- Lookahead/lookbehind assertions
- Many escape sequences beyond `\d` and `\w`

## Requirements

- Python 3.x
- No external dependencies

## License

Feel free to use and modify this code for educational purposes.

## Contributing

This is a personal learning project, but suggestions and improvements are welcome!