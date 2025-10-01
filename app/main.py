#!/usr/bin/env python3
import sys

# Lightweight regex engine with support for:
# - literals
# - escapes: \d and \w
# - character classes [abc] and negated [^abc]
# - anchors ^ and $
# - one-or-more quantifier +
# - optional quantifier ?
# - dot . which matches any character except newline
# - grouping (...) and alternation with |

def parse_pattern(pattern):
    L = len(pattern)

    def parse_alternatives(i, end_char=None):
        # returns (alternatives_list, new_index)
        # alternatives_list: list of sequences, each sequence is a list of tokens
        alts = []
        seq = []
        while i < L:
            c = pattern[i]
            if end_char is not None and c == end_char:
                alts.append(seq)
                return alts, i + 1
            if c == '|':
                alts.append(seq)
                seq = []
                i += 1
                continue
            # parse an atom
            if c == '\\':
                if i + 1 < L:
                    esc = pattern[i+1]
                    if esc == 'd':
                        token = ('digit', None, None)
                    elif esc == 'w':
                        token = ('word', None, None)
                    else:
                        token = ('literal', esc, None)
                    i += 2
                else:
                    token = ('literal', c, None)
                    i += 1
            elif c == '[':
                close = pattern.find(']', i+1)
                if close == -1:
                    raise RuntimeError('Unterminated character class')
                content = pattern[i+1:close]
                if content.startswith('^'):
                    token = ('class', (set(content[1:]), True), None)
                else:
                    token = ('class', (set(content), False), None)
                i = close + 1
            elif c == '.':
                token = ('dot', None, None)
                i += 1
            elif c == '(':
                inner_alts, j = parse_alternatives(i+1, ')')
                # represent group as a single token with val = list of alternative sequences
                token = ('group', inner_alts, None)
                i = j
            else:
                token = ('literal', c, None)
                i += 1

            # handle quantifier following the atom (if any)
            if i < L and pattern[i] in ('+', '?'):
                quant = pattern[i]
                token = (token[0], token[1], quant)
                i += 1

            seq.append(token)

        # end while
        if end_char is None:
            alts.append(seq)
            return alts, i
        else:
            raise RuntimeError(f"Unterminated group, expected '{end_char}'")

    alts, idx = parse_alternatives(0, None)
    # If top-level has more than one alternative, wrap into a single top-level group token
    if len(alts) == 1:
        return alts[0]
    else:
        return [('group', alts, None)]


def token_matches_char(token, ch):
    ttype, val, quant = token
    if ttype == 'literal':
        return ch == val
    if ttype == 'digit':
        return ch.isdigit()
    if ttype == 'word':
        return ch.isalnum() or ch == '_'
    if ttype == 'class':
        chars, negative = val
        if negative:
            return ch not in chars
        else:
            return ch in chars
    if ttype == 'dot':
        return ch != '\n'
    return False


# returns a set of end positions after matching tokens[i:] starting at pos in line
def match_from(tokens, i, pos, line):
    if i == len(tokens):
        return {pos}
    ttype, val, quant = tokens[i]
    results = set()
    n = len(line)

    # helper to match an entire sequence of tokens (sequence is a list of tokens)
    def match_sequence(seq_tokens, start_pos):
        return match_from(seq_tokens, 0, start_pos, line)

    if ttype != 'group':
        # single-token cases: literal, digit, word, class, dot
        if quant is None:
            if pos < n and token_matches_char(tokens[i], line[pos]):
                return match_from(tokens, i+1, pos+1, line)
            else:
                return set()
        if quant == '+':
            p = pos
            if p >= n or not token_matches_char(tokens[i], line[p]):
                return set()
            while p < n and token_matches_char(tokens[i], line[p]):
                p += 1
            max_k = p - pos
            for k in range(max_k, 0, -1):
                next_pos = pos + k
                ends = match_from(tokens, i+1, next_pos, line)
                results.update(ends)
            return results
        if quant == '?':
            # zero occurrences
            results.update(match_from(tokens, i+1, pos, line))
            # one occurrence
            if pos < n and token_matches_char(tokens[i], line[pos]):
                results.update(match_from(tokens, i+1, pos+1, line))
            return results
    else:
        # group token: val is a list of alternative sequences (each sequence is a list of tokens)
        alternatives = val  # list of seqs

        if quant is None:
            # try each alternative once
            for alt in alternatives:
                ends_after_alt = match_sequence(alt, pos)
                for end in ends_after_alt:
                    results.update(match_from(tokens, i+1, end, line))
            return results

        if quant == '?':
            # zero occurrences
            results.update(match_from(tokens, i+1, pos, line))
            # one occurrence of any alternative
            for alt in alternatives:
                ends_after_alt = match_sequence(alt, pos)
                for end in ends_after_alt:
                    results.update(match_from(tokens, i+1, end, line))
            return results

        if quant == '+':
            # need to allow one or more consecutive occurrences of the group (each occurrence matches one alternative)
            # first round: endpoints after exactly one occurrence
            first_positions = set()
            for alt in alternatives:
                first_positions.update(match_sequence(alt, pos))
            if not first_positions:
                return set()
            # compute closure: all positions reachable after 1 or more occurrences
            reachable = set(first_positions)
            frontier = set(first_positions)
            visited = set(first_positions)
            while frontier:
                new_frontier = set()
                for p in frontier:
                    for alt in alternatives:
                        ends = match_sequence(alt, p)
                        for e in ends:
                            if e not in visited:
                                visited.add(e)
                                new_frontier.add(e)
                                reachable.add(e)
                frontier = new_frontier
            # try longer matches first by sorting reachable descending to be greedy
            for next_pos in sorted(reachable, reverse=True):
                results.update(match_from(tokens, i+1, next_pos, line))
            return results

    return set()


def match_pattern(input_line, pattern):
    anchor_start = pattern.startswith('^')
    if anchor_start:
        pattern = pattern[1:]
    anchor_end = pattern.endswith('$')
    if anchor_end:
        pattern = pattern[:-1]

    tokens = parse_pattern(pattern)

    # handle empty pattern
    if len(tokens) == 0:
        lines = input_line.splitlines()
        if anchor_start or anchor_end:
            return any(line == '' for line in lines) or (input_line == '' and (anchor_start or anchor_end))
        return True

    lines = input_line.splitlines()
    if len(lines) == 0 and input_line == '':
        lines = ['']

    def match_in_line(line):
        n = len(line)
        if anchor_start and anchor_end:
            ends = match_from(tokens, 0, 0, line)
            return n in ends
        if anchor_start:
            ends = match_from(tokens, 0, 0, line)
            return len(ends) > 0
        if anchor_end:
            for start in range(0, n+1):
                ends = match_from(tokens, 0, start, line)
                if n in ends:
                    return True
            return False
        for start in range(0, n+1):
            ends = match_from(tokens, 0, start, line)
            if ends:
                return True
        return False

    for line in lines:
        if match_in_line(line):
            return True

    if not anchor_start and not anchor_end:
        full = input_line
        n = len(full)
        for start in range(0, n+1):
            ends = match_from(tokens, 0, start, full)
            if ends:
                return True
    return False


def main():
    if len(sys.argv) < 3:
        print('Usage: ./your_program.sh -E <pattern>')
        exit(2)
    if sys.argv[1] != '-E':
        print("Expected first argument to be '-E'")
        exit(1)
    pattern = sys.argv[2]
    input_line = sys.stdin.read()
    if match_pattern(input_line, pattern):
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()
